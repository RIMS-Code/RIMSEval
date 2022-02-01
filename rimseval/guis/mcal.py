"""Interactive mass calibration using matplotlib's qtagg backend."""

from functools import partial
import sys
from typing import List, Tuple, Union

import numpy as np
from PyQt6 import QtWidgets


from .mpl_canvas import PlotSpectrum
from rimseval.processor import CRDFileProcessor
import rimseval.processor_utils
from rimseval.processor_utils import gaussian_fit_get_max
from rimseval.utilities import ini, string_transformer


class CreateMassCalibration(PlotSpectrum):
    """QMainWindow to create a mass calibration."""

    def __init__(
        self, crd: CRDFileProcessor, logy=True, mcal: np.array = None, theme=None
    ) -> None:
        """Get a PyQt6 window to define the mass calibration for the given data.

        :param crd: The CRD file processor to work with.
        :param logy: Display the y axis logarithmically? Bottom set to 0.7
        :param mcal: Existing mass calibration.
        :param theme: Theme to load, requirems ``pyqtdarktheme`` to be installed
        """
        super().__init__(crd, logy=logy, theme=theme)
        self.setWindowTitle("Create mass calibration")
        self.theme = theme

        # create a matpotlib canvas
        self.sc.mouse_right_press_position.connect(self.right_click_event)

        # buttons in bottom layout
        self.undo_button = QtWidgets.QPushButton("Undo")
        self.undo_button.setToolTip("Undo last peak calibration, see status bar.")
        self.undo_button.clicked.connect(lambda: self.undo_last_mcal())

        cancel_button = QtWidgets.QPushButton("Cancel")
        cancel_button.setToolTip("Cancel mass calibration.")
        cancel_button.clicked.connect(lambda: self.close())
        self.apply_button = QtWidgets.QPushButton("Apply")

        self.apply_button.setToolTip("Apply mass calibration.")
        self.apply_button.clicked.connect(lambda: self.apply())

        # set layout of bottom part
        self.bottom_layout.addStretch()
        self.bottom_layout.addWidget(self.undo_button)
        self.bottom_layout.addWidget(cancel_button)
        self.bottom_layout.addWidget(self.apply_button)

        # some variables for guessing
        self._last_element = None
        self._mass = None  # mass array for guessing
        self._mass_axis = None

        # init mass calibration
        if mcal is None:
            self._mcal = []
        else:
            self._mcal = mcal.tolist()
        self.check_mcal_length()

        # help in statusbar
        self.status_bar.showMessage(
            "Please right-click on a peak to begin mass calibration."
        )

        # plot data
        self.plot_tof()

    def append_to_mcal(self, tof: float, mass: float) -> None:
        """Append a given value to the mass calibration.

        :param tof: Time of flight.
        :param mass: Mass.
        """
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
            # button
            self.apply_button.setDisabled(False)
            # mass calibration
            self._mass, params = rimseval.processor_utils.mass_calibration(
                np.array(self._mcal), self.crd.tof, return_params=True
            )
            # plot secondary axis
            self.secondary_axis(params=params, visible=True)
        else:
            self.apply_button.setDisabled(True)
            self._mass = None
            self._last_element = None
            self.secondary_axis(visible=False)

        if len(self._mcal) > 0:
            self.undo_button.setDisabled(False)
        else:
            self.undo_button.setDisabled(True)

    def guess_mass(self, tof: float) -> str:
        """Guess the mass depending on what is currently set.

        If not drawn from iniabu, I assume the user wants even masses!

        :param tof: Time of Flight (us)

        :return: Guessed mass.
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

    def secondary_axis(self, params: List = None, visible: bool = False) -> None:
        """Toggle secondary axis.

        :param params: Parameters for the transfer functions t0 and const. Only
            required when visible=True.
        :param visible: Turn it on? If so, params are required.
        """
        if visible:
            if params is None:
                return
            else:
                if self._mass_axis is not None:
                    self._mass_axis.set_visible(False)
                self._mass_axis = self.axes.secondary_xaxis(
                    "top",
                    functions=(
                        partial(
                            rimseval.processor_utils.tof_to_mass,
                            tm0=params[0],
                            const=params[1],
                        ),
                        partial(
                            rimseval.processor_utils.mass_to_tof,
                            tm0=params[0],
                            const=params[1],
                        ),
                    ),
                )
                self._mass_axis.set_xlabel("Mass (amu)")
                if self.theme == "dark":
                    self._mass_axis.set_color("tab:orange")
                else:
                    self._mass_axis.set_color("tab:red")
                self.sc.draw()
        elif self._mass_axis is not None:
            self._mass_axis.set_visible(False)
            self._mass_axis = None
            self.sc.draw()

    def undo_last_mcal(self):
        """Undo the last mass calibration by popping the last entry of list."""
        tof, mass = self._mcal.pop()
        self.status_bar.showMessage(
            f"Deleted calibration with mass {mass:.2f} at {tof:.2f}us."
        )
        self.check_mcal_length()


def create_mass_cal_app(crd: CRDFileProcessor, logy: bool = True, theme=None) -> None:
    """Create a PyQt5 app for the mass cal window.

    :param crd: CRD file to calibrate for.
    :param logy: Should the y axis be logarithmic? Defaults to True.
    :param theme: Theme of GUI, requires ``pyqtdarktheme`` to be installed
    """
    app = QtWidgets.QApplication(sys.argv)
    mcal = crd.def_mcal
    window = CreateMassCalibration(crd, mcal=mcal, logy=logy, theme=theme)
    window.show()
    app.exec()


def find_closest_iso(mass: float, key: List = None) -> Tuple[str, float]:
    """Find closest iniabu isotope to given mass and return its name.

    If a key is given, will only consider that element, otherwise all.

    :param mass: Mass of the isotope to look for.
    :param key: An element or isotope key that is valid for iniabu.

    :return: Closest isotpoe, name and mass as tuple.
    """
    if key is None:
        key = list(ini.ele_dict.keys())
    isos = ini.iso[key]
    index = np.argmin(np.abs(isos.mass - mass))
    return isos.name[index], isos.mass[index]
