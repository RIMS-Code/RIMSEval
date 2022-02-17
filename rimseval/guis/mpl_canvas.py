"""Matplotlib Canvas implementation to handle various mouse events."""

from matplotlib.backends.backend_qtagg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar,
)
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from PyQt6 import QtCore, QtWidgets

try:
    import qdarktheme
except ImportError:
    qdarktheme = None

from rimseval.processor import CRDFileProcessor


class PlotSpectrum(QtWidgets.QMainWindow):
    """QMainWindow to plot a ToF or mass spectrum."""

    def __init__(
        self, crd: CRDFileProcessor, logy: bool = True, theme: str = None
    ) -> None:
        """Get a PyQt5 window to define the mass calibration for the given data.

        :param crd: The CRD file processor to work with.
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

        self.crd = crd
        self.logy = logy

        # create a matpotlib canvas using my own canvas
        self.fig = Figure(figsize=(9, 6), dpi=100)
        sc = MplCanvasRightClick(self.fig)
        self.axes = self.fig.add_subplot(111)
        self.sc = sc

        toolbar = MyMplNavigationToolbar(sc, self)
        self.status_bar = QtWidgets.QStatusBar()
        self.setStatusBar(self.status_bar)

        # layouts to populate
        self.bottom_layout = QtWidgets.QHBoxLayout()
        self.right_layout = QtWidgets.QVBoxLayout()

        self.right_layout.addStretch()  # layout must contain something to work...

        # toolbar and canvas
        layout_plot = QtWidgets.QVBoxLayout()
        layout_plot.addWidget(toolbar)
        layout_plot.addWidget(sc)

        # layout top
        layout_top = QtWidgets.QHBoxLayout()
        layout_top.addLayout(layout_plot)
        layout_top.addLayout(self.right_layout)

        # main layout
        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(layout_top)

        # add a logy toggle button
        self.button_logy_toggle = QtWidgets.QPushButton("LogY")
        self.button_logy_toggle.setCheckable(True)
        self.button_logy_toggle.setChecked(logy)
        self.button_logy_toggle.clicked.connect(self.logy_toggle)
        self.bottom_layout.addWidget(self.button_logy_toggle)

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

    def plot_tof(self):
        """Plot ToF spectrum."""
        self._plot_data("tof")

    def plot_ms(self):
        """Plot mass spectrum."""
        if self.crd.mass is not None:
            self._plot_data("mass")

    # PRIVATE METHODS #

    def _plot_data(self, case: str) -> None:
        """Plot the data on the canvas.

        :param case: What should we plot on x axis? "tof" for time of flight or
            "mass" for mass spectrum
        """
        if case == "tof":
            xax = self.crd.tof
            xlabel = "Time of Flight (us)"
        else:
            xax = self.crd.mass
            xlabel = "Mass (amu)"

        color = "w" if self.theme == "dark" else "k"

        self.axes.fill_between(xax, self.crd.data, color=color, linewidth=0.3)
        self.axes.set_xlabel(xlabel)
        self.axes.set_ylabel("Counts")
        if self.logy:
            self.axes.set_yscale("log")
            self.axes.set_ylim(bottom=0.7)

        self.sc.draw()


class MplCanvasRightClick(FigureCanvas):
    """MPL Canvas reimplementation to catch right click.

    On right click, emits the coordinates of the position in axes coordinates as
    a signal of two floats (x_position, y_position).
    """

    mouse_right_press_position = QtCore.pyqtSignal(float, float)
    mouse_right_release_position = QtCore.pyqtSignal(float, float)

    def __init__(self, figure: Figure) -> None:
        """Initialize MPL canvas with right click capability.

        :param figure: Matplotlib Figure
        """
        super().__init__(figure)

        self.mpl_connect(
            "button_press_event",
            lambda event: self.emit_mouse_position(event, "pressed"),
        )
        self.mpl_connect(
            "button_release_event",
            lambda event: self.emit_mouse_position(event, "released"),
        )

    def emit_mouse_position(self, event, case):
        """Emit a signal on a right mouse click event.

        Here, bring up a box to ask for the mass, then send it, along with the time
        the mass is at, to the parent class receiver.

        :param event: PyQt event.
        :param case: Which case are we handling? Currently implemented are "pressed",
            "released".
        """
        if event.button == 3:  # right click as an mpl MouseEvent
            if event.xdata is not None and event.ydata is not None:
                if case == "pressed":
                    self.mouse_right_press_position.emit(event.xdata, event.ydata)
                elif case == "released":
                    self.mouse_right_release_position.emit(event.xdata, event.ydata)


class MyMplNavigationToolbar(NavigationToolbar):
    """My own reimplementation of the navigation toolbar.

    Features:
    - untoggle zoom button after zoom is finished.
    """

    def __init__(self, *args, **kwargs):
        """Initialize toolbar."""
        super().__init__(*args, **kwargs)

    def release_zoom(self, event):
        """Run a normal zoom release event and then untoggle button."""
        super().release_zoom(event)
        self.zoom()  # untoggle zoom button
