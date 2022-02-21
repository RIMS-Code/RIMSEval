"""Plotting capability for specialty functions."""

import sys
from typing import Tuple

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

from rimseval.processor import CRDFileProcessor
from rimseval.guis.mpl_canvas import MyMplNavigationToolbar


class PlotFigure(QtWidgets.QMainWindow):
    """QMainWindow to plot a Figure."""

    def __init__(self, logy: bool = True, theme: str = None) -> None:
        """Get a PyQt5 window to define the mass calibration for the given data.

        :param logy: Display the y axis logarithmically? Bottom set to 0.7
        :param theme: Theme, if applicable ("dark" or "light", default None)
        """
        super().__init__()
        self.setWindowTitle("Mass Spectrum")

        self.theme = theme
        if theme is not None and qdarktheme is not None:
            self.setStyleSheet(qdarktheme.load_stylesheet(theme))

        if theme == "dark":
            plt.style.use("dark_background")

        self.logy = logy

        # create a matpotlib canvas using my own canvas
        self.fig = Figure(figsize=(9, 6), dpi=100)
        sc = FigureCanvas(self.fig)
        self.axes = self.fig.add_subplot(111)
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


def hist_nof_shots(
    crd: CRDFileProcessor, logy: bool = False, theme: str = None
) -> None:
    """Plot a histogram of the number of shots in a given crd file.

    The histogram is compared with the theoretical curve based on poisson statistics.

    :param crd: CRD file to process.
    :param logy: Plot with logarithmic y axis? Defaults to ``True``
    :param theme: Theme to plot in, defaults to ``None``.
    """
    app = QtWidgets.QApplication(sys.argv)
    fig = PlotFigure(logy=logy, theme=theme)

    xdata, hist = _create_histogram(crd.ions_per_shot)

    # theoretical prediction
    lambda_poisson = np.sum(crd.ions_per_shot) / crd.nof_shots
    theoretical_values = poisson.pmf(xdata, lambda_poisson) * np.sum(hist)

    if theme == "dark":
        main_color = "w"
    else:
        main_color = "tab:blue"

    fig.axes.bar(xdata, hist, width=1, color=main_color, label="Data")
    fig.axes.step(
        xdata - 0.5,
        theoretical_values,
        "-",
        color="tab:red",
        label="Poisson Distribution",
    )

    # labels
    fig.axes.set_xlabel("Number of ions in individual shot")
    fig.axes.set_ylabel("Frequency")
    fig.axes.set_title(
        f"Histogram number of ions per shot - {crd.fname.with_suffix('').name}"
    )

    fig.axes.legend()
    fig.show()

    # create the app
    fig.show()
    app.exec()


@njit
def _create_histogram(data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Sort the data into a histogram. Bins are equal to one integer."""
    xdata = np.arange(np.max(data) + 1)
    hist = np.zeros_like(xdata)
    for it in data:
        hist[int(it)] += 1
    return xdata, hist
