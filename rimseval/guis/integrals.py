"""Interactive integral and background selection using matplotlib's qtagg backend."""

import sys
from typing import Tuple
import time

import matplotlib.colors as mcolors
import numpy as np
from PyQt5 import QtWidgets

from .mpl_canvas import PlotSpectrum
from rimseval.processor import CRDFileProcessor


class DefineIntegrals(PlotSpectrum):
    """QMainWindow to create a mass calibration."""

    def __init__(self, crd: CRDFileProcessor, logy=True) -> None:
        """Get a PyQt5 window to define the mass calibration for the given data.

        :param crd: The CRD file processor to work with.
        :param logy: Display the y axis logarithmically? Bottom set to 0.7
        """
        super(DefineIntegrals, self).__init__(crd, logy)
        self.setWindowTitle("Define integrals")

        # create a matpotlib canvas
        self.sc.mouse_right_press_position.connect(self.mouse_right_press)
        self.sc.mouse_right_release_position.connect(self.mouse_right_released)

        # buttons in bottom layout
        cancel_button = QtWidgets.QPushButton("Cancel")
        cancel_button.setToolTip("Cancel defining integrals.")
        cancel_button.clicked.connect(lambda: self.close())
        self.apply_button = QtWidgets.QPushButton("Apply")

        self.apply_button.setToolTip("Apply integrals.")
        self.apply_button.clicked.connect(lambda: self.apply())

        # set layout of bottom part
        self.bottom_layout.addStretch()
        self.bottom_layout.addWidget(cancel_button)
        self.bottom_layout.addWidget(self.apply_button)

        # some variables
        self._last_xpos = None

        # if integrals already exist
        if (crd_int := crd.def_integrals) is None:
            self.int_names = []
            self.int_values = []
        else:
            self.int_names, int_values = crd_int
            self.int_values = list(int_values)

        # help in statusbar
        self.status_bar.showMessage(
            "Right click-and-drag horizontally over peak you want to define integral "
            "for."
        )

        # plot data
        self.plot_ms()

        # setup layout and mark integrals
        self.peaks_changed()

    def apply(self):
        """Apply the mass calibration and return it."""
        self.crd.def_integrals = self.int_names, np.array(self.int_values)
        self.close()

    def delete_peak(self, name: str):
        """Delete a peak from consideration names and values list.

        :param name: Name of the peak.
        """
        index_to_pop = self.int_names.index(name)
        self.int_names.pop(index_to_pop)
        self.int_values.pop(index_to_pop)
        self.peaks_changed()

    def mouse_right_press(self, xpos: float, *args, **kwargs) -> None:
        """The right mouse button was pressed.

        :param xpos: Position on x axis.
        """
        self._last_xpos = xpos

    def mouse_right_released(self, xpos: float, *args, **kwargs) -> None:
        """Right mouse button was released.

        :param xpos: Position on x axis.
        """
        peak = np.sort(np.array([self._last_xpos, xpos], dtype=float))
        self.user_peak_name_input(peak)

    def peaks_changed(self):
        """Go through the list of peaks, make buttons and shade areas."""
        # clear layout
        for it in reversed(range(self.top_layout.count())):
            widgetToRemove = self.top_layout.itemAt(it).widget()
            self.top_layout.removeWidget(widgetToRemove)

        # sort the integrals
        self.sort_integrals()

        # add text to layout
        self.top_layout.addWidget(QtWidgets.QLabel("Click to delete:"))

        # create buttons with functions to delete values
        for name in self.int_names:
            button = QtWidgets.QPushButton(name)
            button.pressed.connect(lambda val=name: self.delete_peak(val))
            self.top_layout.addWidget(button)
        self.top_layout.addStretch()

        self.shade_peaks()

    def shade_peaks(self):
        """Shade the peaks with given integrals."""
        # clear plot but keep axes limits (in case zoomed)
        xax_lims = self.sc.axes.get_xlim()
        yax_lims = self.sc.axes.get_ylim()
        self.sc.axes.clear()
        self.plot_ms()
        self.sc.axes.set_xlim(xax_lims)
        self.sc.axes.set_ylim(yax_lims)

        # shade peaks
        for it, peak_pos in enumerate(self.int_values):
            indexes = np.where(
                np.logical_and(self.crd.mass > peak_pos[0], self.crd.mass < peak_pos[1])
            )
            self.sc.axes.fill_between(
                self.crd.mass[indexes],
                self.crd.data[indexes],
                color=tableau_color(it),
                linewidth=0.25,
            )

    def sort_integrals(self):
        """Sort the names and integrals."""
        if len(self.int_names) > 1:
            sorted_zip = sorted(zip(self.int_names, self.int_values))
            self.int_names = [i for i, j in sorted_zip]
            self.int_values = [j for i, j in sorted_zip]

    def user_peak_name_input(self, peak_pos: np.array, name: str = "") -> None:
        """Query user for position.

        :param peak_pos: Sorted array, left and right position of peak.
        """
        user_input = QtWidgets.QInputDialog.getText(
            self,
            "Name",
            f"Please name the integral from {round(peak_pos[0], 2)} to "
            f"{round(peak_pos[1], 2)} amu.",
            text=name,
        )

        if user_input[1]:
            name = user_input[0]
            if name == "":
                QtWidgets.QMessageBox.warning(
                    self,
                    "Invalid name",
                    "Please enter a name for the integral or press Cancel.",
                )
            elif name in self.int_names:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Name exists",
                    "Name already exists, please enter another name.",
                )
            else:
                self.int_names.append(name)
                self.int_values.append(peak_pos)
                self.peaks_changed()
                return
        else:
            return

        self.user_peak_name_input(peak_pos, name)


def define_integrals_app(crd: CRDFileProcessor, logy: bool = True) -> None:
    """Create a PyQt5 app for defining integrals.

    :param crd: CRD file to calibrate for.
    :param logy: Should the y axis be logarithmic? Defaults to True.
    """
    app = QtWidgets.QApplication(sys.argv)
    window = DefineIntegrals(crd, logy=logy)
    window.show()
    app.exec_()


def tableau_color(it: int = 0) -> str:
    """Return nth color from matplotlib TABLEAU_COLORS.

    If out of range, start at beginning.

    :param it: Which tableau color to get.

    :return: Matplotlib color string.
    """
    cols = list(mcolors.TABLEAU_COLORS.values())
    return cols[it % len(cols)]
