"""Some Interactive stuff using matplotlib with the PyQt5 backend."""

from typing import List, Tuple, Union
import sys

import rimseval.processor_utils
from PyQt5 import QtCore, QtWidgets, QtGui
import matplotlib as mpl
from iniabu import ini
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg,
    NavigationToolbar2QT as NavigationToolbar,
)
from matplotlib.figure import Figure
import numpy as np

from rimseval.processor import CRDFileProcessor
from rimseval.processor_utils import gaussian_fit_get_max
from rimseval.utilities import string_transformer

mpl.use("Qt5Agg")


class MplCanvasRightClick(FigureCanvasQTAgg):
    """MPL Canvas reimplementation to catch right click.

    On right click, emits the coordinates of the position in axes coordinates as
    a signal of two floats (x_position, y_position).
    """

    right_click_position = QtCore.pyqtSignal(float, float)

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)

        super(MplCanvasRightClick, self).__init__(fig)

        self.mpl_connect("button_press_event", self.emit_mouse_position)

    def emit_mouse_position(self, event):
        """Emits a signal on a right mouse click event.

        Here, bring up a box to ask for the mass, then send it, along with the time
        the mass is at, to the parent class receiver.
        """
        if event.button == 3:  # right click as an mpl MouseEvent
            if event.xdata is not None and event.ydata is not None:  # click in canvas
                self.right_click_position.emit(event.xdata, event.ydata)


class CreateMassCalibration(QtWidgets.QMainWindow):
    def __init__(self, crd: CRDFileProcessor, mcal: np.array = None) -> None:
        """Get a PyQt5 window to define the mass calibration for the given data.

        :param crd: The CRD file processor to work with.
        :param mcal: Existing mass calibration.
        """
        super(CreateMassCalibration, self).__init__()
        self.setWindowTitle("Create mass calibration")

        self.crd = crd

        # create a matpotlib canvas
        sc = MplCanvasRightClick(self, width=9, height=6, dpi=100)
        sc.right_click_position.connect(self.right_click_event)
        self.sc = sc

        toolbar = NavigationToolbar(sc, self)
        self.status_bar = QtWidgets.QStatusBar()
        self.setStatusBar(self.status_bar)

        # layout
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(toolbar)
        layout.addWidget(sc)

        widget = QtWidgets.QWidget()
        widget.setLayout(layout)

        # buttons and stuff
        bottom_layout = QtWidgets.QHBoxLayout()
        bottom_layout.addStretch()

        self.undo_button = QtWidgets.QPushButton("Undo")
        self.undo_button.setToolTip("Undo last peak calibration, see status bar.")
        self.undo_button.clicked.connect(lambda: self.undo_last_mcal())

        cancel_button = QtWidgets.QPushButton("Cancel")
        cancel_button.setToolTip("Cancel mass calibration.")
        cancel_button.clicked.connect(lambda: self.close())
        self.apply_button = QtWidgets.QPushButton("Apply")

        self.apply_button.setToolTip("Apply mass calibration.")
        self.apply_button.clicked.connect(lambda: self.apply())

        bottom_layout.addWidget(self.undo_button)
        bottom_layout.addWidget(cancel_button)
        bottom_layout.addWidget(self.apply_button)

        layout.addLayout(bottom_layout)

        self.setCentralWidget(widget)

        # init mass calibration
        if mcal is None:
            self._mcal = []
        else:
            self._mcal = mcal.tolist()
        self.check_mcal_length()

        # some variables for guessing
        self._last_element = None
        self._mass = None  # mass array for guessing

        # plot some data
        self.plot_data()

        # help in statusbar
        self.status_bar.showMessage(
            "Please right-click on a peak to begin mass calibration."
        )

    def append_to_mcal(self, tof: float, mass: float) -> None:
        self._mcal.append([tof, mass])
        self.check_mcal_length()

    def apply(self):
        """Apply the mass calibration and return it."""
        self.crd.def_mcal = np.array(self._mcal)
        self.crd.mass_calibration()
        self.close()

    def check_mcal_length(self):
        """Check length of mcal to set button statuses, start guessing."""
        # apply button
        if len(self._mcal) >= 2:
            self.apply_button.setDisabled(False)
            self._mass = rimseval.processor_utils.mass_calibration(
                np.array(self._mcal), self.crd.tof
            )
        else:
            self.apply_button.setDisabled(True)
            self._mass = None
            self._last_element = None

        if len(self._mcal) > 0:
            self.undo_button.setDisabled(False)
        else:
            self.undo_button.setDisabled(True)

    def guess_mass(self, tof: float) -> str:
        """Guess the mass depending on what is currently set.

        If not drawn from iniabu, I assume the user wants even masses!

        :param tof: Time of Flight (us)
        """
        ind_tof = np.argmin(np.abs(self.crd.tof - tof))
        mass = self._mass[ind_tof]

        if self._last_element is not None:  # guess with iniabu
            name_iso, mass_iso = find_closest_iso(mass, self._last_element)
            if np.abs(mass_iso - mass) < 0.5:  # within half a mass
                return name_iso
            else:
                return find_closest_iso(mass)[0]
        else:  # guess mass from values
            return str(int(np.round(mass, 0)))

    def plot_data(self):
        """Plot the data on the canvas."""
        self.sc.axes.plot(self.crd.tof, self.crd.data)

    def query_mass(self, tof: float) -> Union[float, None]:
        """Query mass from user.

        Query a mass from the user using a QInputDialog.

        :param tof: Time of flight of the clicked area.

        :return: Mass of the peak as given by user.
        """
        if self._mass is not None:
            guess = self.guess_mass(tof)
        else:
            guess = ""

        user_input = QtWidgets.QInputDialog.getText(
            self,
            "Calibrate Mass",
            f"Enter isotope name or mass for {tof:.2f}us.",
            text=guess,
        )

        def err_invalid_entry():
            """Show Error Message for invalid entry."""
            QtWidgets.QMessageBox.warning(
                self,
                "Invalid Input",
                "No valid input. Please enter a mass (number) or an isotope "
                "in the format, e.g., 46Ti, Ti46, or Ti-46.",
            )

        def err_invalid_isotope(iso):
            """Show Error Message for invalid isotope."""
            QtWidgets.QMessageBox.warning(
                self,
                "Invalid Isotope",
                f"Could not find an isotope with the name {iso}. "
                f"Please make sure you entered a valid isotope name, "
                f"e.g., 46Ti or Ti46.\n"
                f"It could also be that the isotope you requested is "
                f"currently not available in the database. In that case, "
                f"please enter the mass manually.",
            )

        if user_input[1]:
            if (iso := user_input[0]) == "":
                err_invalid_entry()
                return self.query_mass(tof)
            try:  # user input is a mass
                mass = float(iso)
            except ValueError:
                if "-" not in iso:
                    iso = string_transformer.iso_to_iniabu(iso)
                try:
                    mass = ini.iso[iso].mass
                    self._last_element = ini.iso[iso].name.split("-")[0]
                except IndexError:
                    err_invalid_isotope(iso)
                    return self.query_mass(tof)
            return mass
        else:
            return

    def right_click_event(self, xpos: float, *args, **kwargs) -> None:
        """Act on an emitted right click event."""
        mass = self.query_mass(xpos)
        if mass is None:
            return None  # user hit cancel

        min_value = xpos - 2 * self.crd.peak_fwhm
        max_value = xpos + 2 * self.crd.peak_fwhm
        window = np.where(
            np.logical_and(self.crd.tof > min_value, self.crd.tof < max_value)
        )

        xdata = self.crd.tof[window]
        ydata = self.crd.data[window]

        tof_max = gaussian_fit_get_max(xdata, ydata)

        # make sure max is in between min and max
        if tof_max <= xdata.min() or tof_max >= xdata.max():
            QtWidgets.QMessageBox.warning(
                self,
                "No peak found",
                "Couldn't find a peak. Please try again or choose a bigger peak.",
            )
            return None

        self.append_to_mcal(tof_max, mass)

        self.status_bar.showMessage(
            f"Peak with mass {mass:.2f} found at {tof_max:.2f}us."
        )

    def undo_last_mcal(self):
        """Undo the last mass calibration by popping the last entry of list."""
        tof, mass = self._mcal.pop()
        self.status_bar.showMessage(
            f"Deleted calibration with mass {mass:.2f} at {tof:.2f}us."
        )
        self.check_mcal_length()


def create_mass_cal_app(crd: CRDFileProcessor):
    """Create a PyQt5 app for the mass cal window."""
    app = QtWidgets.QApplication(sys.argv)
    window = CreateMassCalibration(crd)
    window.show()
    app.exec_()


def find_closest_iso(mass: float, key: List = None) -> Tuple[str, float]:
    """Find closest iniabu isotope to given mass and return its name.

    If a key is given, will only consider that element, otherwise all.

    :param mass: Mass of the isotope to look for.
    :param key: An element or isotope key that is valid for iniabu.
    """
    if key is None:
        key = list(ini.ele_dict.keys())
    isos = ini.iso[key]
    index = np.argmin(np.abs(isos.mass - mass))
    return isos.name[index], isos.mass[index]
