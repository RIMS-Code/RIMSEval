"""Interactive integral and background selection using matplotlib's qtagg backend."""

import sys
from typing import List, Union

import matplotlib.colors as mcolors
import numpy as np
from PyQt6 import QtCore, QtWidgets


from rimseval.processor import CRDFileProcessor
import rimseval.processor_utils as pu
from .mpl_canvas import PlotSpectrum


class DefineAnyTemplate(PlotSpectrum):
    """Template to define integrals and backgrounds."""

    def __init__(self, crd: CRDFileProcessor, logy=True, theme: str = None) -> None:
        """Get a PyQt5 window to define the mass calibration for the given data.

        :param crd: The CRD file processor to work with.
        :param logy: Display the y axis logarithmically? Bottom set to 0.7
        :param theme: Theme to load, requires ``pyqtdarktheme`` to be installed
        """
        super().__init__(crd, logy=logy, theme=theme)

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

        self.button_header = None
        self.button_tooltip = None

        # plot data
        self.plot_ms()

    def apply(self):
        """Apply the mass calibration and return it."""
        raise NotImplementedError

    def button_pressed(self, name: str):
        """Define action for left click of a peak button.

        :param name: Name of the peak.
        """  # noqa: DAR401
        raise NotImplementedError

    def check_peak_overlapping(self, peak_pos: np.array) -> Union[List, None]:
        """Check if a given peak position overlaps with any other peaks.

        :param peak_pos: Position of peak, 2 entry array with from, to.

        :return: List of all peak names that it overlaps or ``None``.
        """
        left = peak_pos[0]
        right = peak_pos[1]

        outlist = []
        for it, [dleft, dright] in enumerate(self.int_values):
            name = self.int_names[it]
            if (
                (dleft <= left < dright)
                or (dleft < right <= dright)
                or (left < dleft and right > dright)
            ):
                outlist.append(name)

        if outlist:
            return outlist
        else:
            return

    def clear_layout(self, layout) -> None:
        """Clear a given layout of all widgets, etc."""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget() is not None:
                child.widget().deleteLater()
            elif child.layout() is not None:
                self.clear_layout(child.layout())

    def create_buttons(self):
        """Create the buttons in the right menubar."""
        self.clear_layout(self.right_layout)

        # add text to layout
        if self.button_header is not None:
            self.right_layout.addWidget(QtWidgets.QLabel(self.button_header))

        # create buttons with functions to delete values
        for name in self.int_names:
            button = QtWidgets.QPushButton(name)
            if self.button_tooltip is not None:
                button.setToolTip(self.button_tooltip)
            button.pressed.connect(lambda val=name: self.button_pressed(val))
            self.right_layout.addWidget(button)
        self.right_layout.addStretch()

    def mouse_right_press(self, xpos: float) -> None:
        """Act on right mouse button pressed.

        :param xpos: Position on x axis.
        """
        self._last_xpos = xpos

    def mouse_right_released(self, xpos: float) -> None:
        """Right mouse button was released.

        :param xpos: Position on x axis.
        """
        peak = np.sort(np.array([self._last_xpos, xpos], dtype=float))
        self.user_input(peak)

    def peaks_changed(self):
        """Go through the list of peaks, make buttons and shade areas."""
        raise NotImplementedError

    def shade_peaks(self):
        """Shade the peaks with given integrals."""
        # clear plot but keep axes limits (in case zoomed)
        xax_lims = self.axes.get_xlim()
        yax_lims = self.axes.get_ylim()
        self.axes.clear()
        self.plot_ms()
        self.axes.set_xlim(xax_lims)
        self.axes.set_ylim(yax_lims)

        # shade peaks
        for it, peak_pos in enumerate(self.int_values):
            indexes = np.where(
                np.logical_and(self.crd.mass > peak_pos[0], self.crd.mass < peak_pos[1])
            )

            self.axes.fill_between(
                self.crd.mass[indexes],
                self.crd.data[indexes],
                color=tableau_color(it),
                linewidth=0.3,
            )

    def sort_integrals(self):
        """Sort the names and integrals using routine from processor_utilities."""
        if len(self.int_names) > 1:
            def_integrals, _ = pu.sort_integrals(
                (self.int_names, np.array(self.int_values))
            )
            self.int_names, int_values = def_integrals
            self.int_values = list(int_values)

    def user_input(self, peak_pos: np.array, name: str = "") -> None:
        """Query user for position.

        :param peak_pos: Sorted array, left and right position of peak.
        :param name: Name to preset the line-edit with.
        """  # noqa: DAR401
        raise NotImplementedError


class DefineBackgrounds(DefineAnyTemplate):
    """QMainWindow to define backgrounds."""

    signal_backgrounds_defined = QtCore.pyqtSignal()

    def __init__(self, crd: CRDFileProcessor, logy=True, theme: str = None) -> None:
        """Get a PyQt5 window to define backgrounds for the given integrals.

        :param crd: The CRD file processor to work with.
        :param logy: Display the y axis logarithmically? Bottom set to 0.7
        :param theme: Theme to load, requires ``pyqtdarktheme`` to be installed
        """
        super().__init__(crd, logy=logy, theme=theme)

        self.setWindowTitle("Define integrals")

        # if backgrounds already exist
        if (crd_int := crd.def_backgrounds) is None:
            self.bg_names = []
            self.bg_values = []
        else:
            self.bg_names, bg_values = crd_int
            self.bg_values = list(bg_values)

        # temp variables
        self._selected_peak_name = None

        self.status_bar.showMessage(
            "Right click, drag, and release to define background."
        )

        self.button_header = "Click to delete:"
        self.button_tooltip = (
            "Click to delete all background definitions for this peak."
        )

        QtWidgets.QInputDialog()

        self.sort_integrals()
        self.create_buttons()
        self.shade_peaks()
        self.shade_backgrounds()

    def apply(self):
        """Apply the mass calibration and return it."""
        if self.bg_names:
            self.crd.def_backgrounds = pu.sort_backgrounds(
                (self.bg_names, np.array(self.bg_values))
            )
        else:
            self.crd.def_backgrounds = None
        self.signal_backgrounds_defined.emit()
        self.close()

    def button_pressed(self, name: str):
        """Delete a peak from consideration names and values list.

        :param name: Name of the peak.
        """
        comp = True
        while comp:
            try:
                index_to_pop = self.bg_names.index(name)
                self.bg_names.pop(index_to_pop)
                self.bg_values.pop(index_to_pop)
            except ValueError:
                comp = False

        self.peaks_changed()

    def peaks_changed(self):
        """Go through the list of peaks, make buttons and shade areas."""
        self.shade_peaks()  # also restarts the canvas
        self.shade_backgrounds()

    def shade_backgrounds(self):
        """Go through background list and shade them.

        .. note:: Canvas is not cleared prior to this!
        """
        for it, peak_pos in enumerate(self.bg_values):
            int_name_index = self.int_names.index(self.bg_names[it])
            col = tableau_color(int_name_index)

            self.axes.axvspan(
                peak_pos[0], peak_pos[1], linewidth=0, color=col, alpha=0.25
            )

        self.sc.draw()

    def user_input(self, bg_pos: np.array, name: str = "") -> None:
        """Query user for position of background.

        :param bg_pos: Sorted array, left and right position of background.
        :param name: Name of the peak, for reloading the UI.
        :param other_peaks: Remove overlap of bg with other peaks than itself?
        """
        # dialog
        def set_selected_peak_name(val):
            """Set the selected peak_name to the value provided by signal."""
            self._selected_peak_name = val

        dlg = PeakDialog(
            self, peak_names=self.int_names, desc="Select a peak for this background:"
        )
        dlg.peak_selected_signal.connect(set_selected_peak_name)

        if not dlg.exec():
            return
        else:
            name = self._selected_peak_name

        self_corr, all_corr = pu.peak_background_overlap(
            (self.int_names, np.array(self.int_values)), ([name], np.array([bg_pos]))
        )
        if (
            not self_corr[1].shape == all_corr[1].shape
            or not (self_corr[1] == all_corr[1]).all()
        ):  # more overlap
            question = QtWidgets.QMessageBox.question(
                self,
                "Overlap detected",
                f"The selected background overlaps with a peak other than {name}. "
                f"If this was your intention, press `Yes`. If you press `No`, "
                f"the overlap will automatically be resolved.",
            )
            if question == QtWidgets.QMessageBox.StandardButton.No:
                self.bg_names += all_corr[0]
                self.bg_values += list(all_corr[1])
            else:
                self.bg_names += self_corr[0]
                self.bg_values += list(self_corr[1])
        else:
            self.bg_names += self_corr[0]
            self.bg_values += list(self_corr[1])

        self.peaks_changed()


class DefineIntegrals(DefineAnyTemplate):
    """QMainWindow to define integrals."""

    signal_integrals_defined = QtCore.pyqtSignal()

    def __init__(self, crd: CRDFileProcessor, logy=True, theme: str = None) -> None:
        """Get a PyQt5 window to define integrals in the given mass spectrum.

        :param crd: The CRD file processor to work with.
        :param logy: Display the y axis logarithmically? Bottom set to 0.7
        :param theme: Theme to load, requires ``pyqtdarktheme`` to be installed
        """
        super().__init__(crd, logy=logy, theme=theme)

        self.setWindowTitle("Define integrals")

        self.status_bar.showMessage(
            "Right click, drag, and release to define integral."
        )

        self.button_header = "Click to delete:"
        self.button_tooltip = "Click to delete this integral definition."

        self.sort_integrals()
        self.create_buttons()
        self.shade_peaks()

    def apply(self):
        """Apply the mass calibration and return it."""
        if self.int_names:
            self.crd.def_integrals = self.int_names, np.array(self.int_values)
        else:
            self.crd.def_integrals = None
        self.signal_integrals_defined.emit()
        self.close()

    def button_pressed(self, name: str):
        """Delete a peak from consideration names and values list.

        :param name: Name of the peak.
        """
        index_to_pop = self.int_names.index(name)
        self.int_names.pop(index_to_pop)
        self.int_values.pop(index_to_pop)
        self.peaks_changed()

    def peaks_changed(self):
        """Go through the list of peaks, make buttons and shade areas."""
        # sort the integrals
        self.sort_integrals()

        # buttons
        self.create_buttons()

        # shade
        self.shade_peaks()

    def user_input(self, peak_pos: np.array, name: str = "") -> None:
        """Query user for position.

        :param peak_pos: Sorted array, left and right position of peak.
        :param name: Name to pre-populate line-edit with.
        """
        # check for overlap:
        if self.check_peak_overlapping(peak_pos):
            QtWidgets.QMessageBox.warning(
                self,
                "Overlap detected",
                "Your peak overlaps with one or more other peaks. Try again.",
            )
            return

        user_in = QtWidgets.QInputDialog.getText(
            self,
            "Name",
            f"Please name the integral from {round(peak_pos[0], 2)} to "
            f"{round(peak_pos[1], 2)} amu.",
            text=name,
        )

        if user_in[1]:
            name = user_in[0]
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

        self.user_input(peak_pos, name)


class PeakDialog(QtWidgets.QDialog):
    """Custom QDialog to select from a list of buttons.

    If a button is pressed, a signal with its name as a string is emitted and the
    dialog is closed with an ``accept``. If the window is closed otherwise,
    a ``reject`` is sent.
    """

    peak_selected_signal = QtCore.pyqtSignal(str)

    def __init__(self, parent, peak_names=None, desc=None):
        """Initialize a peak dialog.

        .. note:: The parameters must be given as keyword argument.

        :param parent: Parent class for dialog.
        :param peak_names: Name of the peaks to be displayed. If None, will reject.
        :param desc: Description for user.
        """
        super().__init__(parent)

        if not peak_names:  # quit if no names were given
            self.reject()

        self.setWindowTitle("Pick from given list")

        # buttons
        button_layout = QtWidgets.QHBoxLayout()
        for it, name in enumerate(peak_names):
            button = QtWidgets.QPushButton(name)
            button.pressed.connect(lambda val=name: self.peak_selected(val))
            button_layout.addWidget(button)
            if it < len(peak_names) - 1:
                button_layout.addStretch()

        # main layout
        layout = QtWidgets.QVBoxLayout()

        # description
        if desc is not None:
            layout.addWidget(QtWidgets.QLabel(desc))
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def peak_selected(self, val):
        """Emit signal with the peak name and exit out of dialog with accept.

        :param val: Name of the selected peak.
        """
        self.peak_selected_signal.emit(val)
        self.accept()


def define_backgrounds_app(crd: CRDFileProcessor, logy: bool = True) -> None:
    """Create a PyQt5 app for defining backgruonds.

    :param crd: CRD file to calibrate for.
    :param logy: Should the y axis be logarithmic? Defaults to True.
    """
    app = QtWidgets.QApplication(sys.argv)
    window = DefineBackgrounds(crd, logy=logy)
    window.show()
    app.exec()


def define_integrals_app(crd: CRDFileProcessor, logy: bool = True) -> None:
    """Create a PyQt5 app for defining integrals.

    :param crd: CRD file to calibrate for.
    :param logy: Should the y axis be logarithmic? Defaults to True.
    """
    app = QtWidgets.QApplication(sys.argv)
    window = DefineIntegrals(crd, logy=logy)
    window.show()
    app.exec()


def tableau_color(it: int = 0) -> str:
    """Return nth color from matplotlib TABLEAU_COLORS.

    If out of range, start at beginning.

    :param it: Which tableau color to get.

    :return: Matplotlib color string.
    """
    cols = list(mcolors.TABLEAU_COLORS.values())
    return cols[it % len(cols)]
