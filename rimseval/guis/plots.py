"""Plotting capability for specialty functions."""

import itertools
import sys
from typing import Tuple

import darkdetect
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from numba import njit
import numpy as np
from PyQt6 import QtWidgets
from scipy.stats import poisson

try:
    import qdarktheme
except ImportError:
    qdarktheme = None

from rimseval.guis.mpl_canvas import MyMplNavigationToolbar
from rimseval.processor import CRDFileProcessor


# markers to cycle through
MARKERS = ("o", "^", "s", "v", "<", ">", "+", "x", "*", "1", "2", "3", "4")


class PlotFigure(QtWidgets.QMainWindow):
    """QMainWindow to plot a Figure."""

    def __init__(self, logy: bool = False, theme: str = None) -> None:
        """Get a PyQt5 window to define the mass calibration for the given data.

        :param logy: Display the y axis logarithmically? Bottom set to 0.7
        :param theme: Theme, if applicable ("dark" or "light", default None)
        """
        super().__init__()
        self.setWindowTitle("Figure")

        self.theme = theme
        if theme is not None and qdarktheme is not None:
            self.setStyleSheet(qdarktheme.load_stylesheet(theme))

        # detect theme
        if theme is None or theme == "auto":  # detect system theme
            if darkdetect.isDark():
                theme = "dark"

        # set theme
        if theme == "dark":
            plt.style.use("dark_background")
            self.main_color = "w"
        else:
            self.main_color = "tab:blue"

        self.logy = logy

        # create a matpotlib canvas using my own canvas
        self.fig = Figure(figsize=(9, 6), dpi=100)
        self.axes = self.fig.add_subplot(111)
        sc = FigureCanvas(self.fig)
        self.sc = sc

        toolbar = MyMplNavigationToolbar(sc, self)
        self.status_bar = QtWidgets.QStatusBar()
        self.setStatusBar(self.status_bar)

        # layouts to populate
        self.bottom_layout = QtWidgets.QHBoxLayout()

        # toolbar and canvas
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(toolbar)
        layout.addWidget(sc)

        # add a logy toggle button
        self.button_logy_toggle = QtWidgets.QPushButton("LogY")
        self.button_logy_toggle.setCheckable(True)
        self.button_logy_toggle.setChecked(logy)
        self.button_logy_toggle.clicked.connect(self.logy_toggle)
        self.bottom_layout.addWidget(self.button_logy_toggle)

        close_button = QtWidgets.QPushButton("Close")
        close_button.clicked.connect(self.close)
        self.bottom_layout.addStretch()
        self.bottom_layout.addWidget(close_button)

        # final layout
        layout.addLayout(self.bottom_layout)

        widget = QtWidgets.QWidget()
        widget.setLayout(layout)

        self.setCentralWidget(widget)

    def logy_toggle(self):
        """Toggle logy."""
        self.logy = not self.logy
        self.button_logy_toggle.setChecked(self.logy)

        if self.logy:
            self.axes.set_yscale("log")
            self.axes.set_ylim(bottom=0.7)
        else:
            self.axes.set_yscale("linear")
            self.axes.set_ylim(bottom=0)

        self.sc.draw()


class DtIons(PlotFigure):
    """Plot time differences between ions."""

    def __init__(
        self,
        crd: CRDFileProcessor,
        logy: bool = False,
        theme: str = None,
        max_ns: float = None,
    ) -> None:
        """Initialize the class.

        :param crd: CRD file to process.
        :param logy: Plot with logarithmic y axis? Defaults to ``True``
        :param theme: Theme to plot in, defaults to ``None``.
        :param max_ns: Maximum time to plot in ns. If None, plots all.
        """
        super().__init__(logy=logy, theme=theme)

        self.setWindowTitle("Histogram time difference between ions")

        self.crd = crd
        self.max_ns = max_ns

        self.calc_and_draw()

    def calc_and_draw(self) -> None:
        """Calculate the required data and draw it."""
        ion_ranges = self.crd.ions_to_tof_map[np.where(self.crd.ions_per_shot > 1)]
        spacings, frequency = _calculate_bin_differences(self.crd.all_tofs, ion_ranges)

        # turn spacings to ns
        spacings = spacings.astype(float)
        spacings *= self.crd.crd.header["binLength"] / 1000  # bins are in ps

        # plot
        self.axes.plot(spacings, frequency, "-", color=self.main_color)
        self.axes.text(
            0.95,
            0.95,
            f"TDC bin length: {self.crd.crd.header['binLength']}ps",
            horizontalalignment="right",
            verticalalignment="top",
            transform=self.axes.transAxes,
        )

        # labels
        self.axes.set_xlabel("Time between all ions for individual shots (ns)")
        self.axes.set_ylabel("Frequency")
        self.axes.set_title(f"{self.crd.fname.with_suffix('').name}")

        # ax limit
        if self.max_ns is not None:
            self.axes.set_xlim(right=self.max_ns)
        self.axes.set_xlim(left=0)
        self.axes.set_ylim(bottom=0)

        self.sc.draw()


class IntegralsPerPackage(PlotFigure):
    """Plot integrals of all packages versus package number."""

    def __init__(
        self, crd: CRDFileProcessor, logy: bool = False, theme: str = None
    ) -> None:
        """Initialize the class.

        :param crd: CRD file to process.
        :param logy: Plot with logarithmic y-axis? Defaults to ``True``
        :param theme: Theme to plot in, defaults to ``None``.

        :raises OSError: Packages are not defined
        """
        super().__init__(logy=logy, theme=theme)

        self.setWindowTitle("Integrals per package")

        self.crd = crd

        if crd.integrals_pkg is None:
            raise OSError("Integrals for packages are not available.")

        self.calc_and_draw()

    def calc_and_draw(self) -> None:
        """Create the plot for all the defined integrals."""
        int_names = self.crd.def_integrals[0]
        integrals_pkg = self.crd.integrals_pkg

        xdata = np.arange(len(integrals_pkg)) + 1  # start with 1
        counts = integrals_pkg[:, :, 0]
        errors = integrals_pkg[:, :, 1]

        # plot
        marker = itertools.cycle(MARKERS)
        for it in range(counts.shape[1]):  # loop through all defined integrals
            dat = counts[:, it]
            err = errors[:, it]
            self.axes.errorbar(
                xdata, dat, yerr=err, ls="--", label=int_names[it], marker=next(marker)
            )

        # labels
        self.axes.set_xlabel("Package number")
        self.axes.set_ylabel("Counts in integral")
        self.axes.set_title(
            f"Integrals per package - {self.crd.fname.with_suffix('').name}"
        )
        self.axes.legend()

        self.sc.draw()


class IonsPerShot(PlotFigure):
    """Plot histogram for number of ions per shot."""

    def __init__(
        self, crd: CRDFileProcessor, logy: bool = False, theme: str = None
    ) -> None:
        """Initialize the class.

        :param crd: CRD file to process.
        :param logy: Plot with logarithmic y-axis? Defaults to ``True``
        :param theme: Theme to plot in, defaults to ``None``.
        """
        super().__init__(logy=logy, theme=theme)

        self.setWindowTitle("Histogram ions per shot")

        self.crd = crd

        self.calc_and_draw()

    def calc_and_draw(self) -> None:
        """Calculate the histogram and plot it."""
        xdata, hist = _create_histogram(self.crd.ions_per_shot)

        # theoretical prediction
        lambda_poisson = np.sum(self.crd.ions_per_shot) / self.crd.nof_shots
        theoretical_values = poisson.pmf(xdata, lambda_poisson) * np.sum(hist)

        # plot
        self.axes.bar(xdata, hist, width=1, color=self.main_color, label="Data")
        self.axes.step(
            xdata - 0.5,
            theoretical_values,
            "-",
            color="tab:red",
            label="Poisson Distribution",
        )

        # labels
        self.axes.set_xlabel("Number of ions in individual shot")
        self.axes.set_ylabel("Frequency")
        self.axes.set_title(
            f"Histogram number of ions per shot - {self.crd.fname.with_suffix('').name}"
        )
        self.axes.legend()

        self.sc.draw()


def dt_ions(
    crd: CRDFileProcessor, logy: bool = False, theme: str = None, max_ns: float = None
) -> None:
    """Plot ToF difference between ions for shots with 2+ ions.

    :param crd: CRD file to process.
    :param logy: Plot with logarithmic y axis? Defaults to ``True``
    :param theme: Theme to plot in, defaults to ``None``.
    :param max_ns: Maximum time to plot in ns. If None, plots all.
    """
    app = QtWidgets.QApplication(sys.argv)
    window = DtIons(crd, logy=logy, theme=theme, max_ns=max_ns)
    window.show()
    app.exec()


def integrals_packages(
    crd: CRDFileProcessor, logy: bool = False, theme: str = None
) -> None:
    """Plot all the integrals versus package number for data split into packages.

    :param crd: CRD file to process.
    :param logy: Plot with logarithmic y axis? Defaults to ``True``
    :param theme: Theme to plot in, defaults to ``None``.
    """
    app = QtWidgets.QApplication(sys.argv)
    window = IntegralsPerPackage(crd, logy=logy, theme=theme)
    window.show()
    app.exec()


def nof_ions_per_shot(
    crd: CRDFileProcessor, logy: bool = False, theme: str = None
) -> None:
    """Plot a histogram of the number of shots in a given crd file.

    The histogram is compared with the theoretical curve based on poisson statistics.

    :param crd: CRD file to process.
    :param logy: Plot with logarithmic y axis? Defaults to ``True``
    :param theme: Theme to plot in, defaults to ``None``.
    """
    app = QtWidgets.QApplication(sys.argv)
    window = IonsPerShot(crd, logy=logy, theme=theme)
    window.show()
    app.exec()


@njit
def _create_histogram(data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Sort the data into a histogram. Bins are equal to one integer."""
    xdata = np.arange(np.max(data) + 1)
    hist = np.zeros_like(xdata)
    for it in data:
        hist[int(it)] += 1
    return xdata, hist


@njit
def _calculate_bin_differences(
    all_tofs: np.ndarray, ion_ranges: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:
    """Sort through bins and write the bin spacings back.

    :param all_tofs: All tofs array with info on arrival bins
    :param ion_ranges: Range of ions to consider.

    :return: Spacings between ions in bins, frequency of spacing occurance
    """
    # calculate number of spacings -> must be a gaussian sum of numbers
    nof_spacings = 0
    for rng in ion_ranges:
        nof_ions = rng[1] - rng[0]
        nof_spacings += nof_ions * (nof_ions - 1) / 2

    ind = 0
    spacings = np.zeros(int(nof_spacings), dtype=np.int32)
    for rng in ion_ranges:
        ions = all_tofs[rng[0] : rng[1]]
        for it in range(len(ions) - 1):
            diffs = np.abs(ions[it + 1 :] - ions[it])
            spacings[ind : ind + len(diffs)] = diffs
            ind += len(diffs)

    # now create the histogram
    min_diff = np.min(spacings)
    max_diff = np.max(spacings)

    frequency = np.zeros(max_diff - min_diff + 1, dtype=np.int32)
    for sp in spacings:
        frequency[sp - min_diff] += 1

    return np.arange(min_diff, max_diff + 1), frequency
