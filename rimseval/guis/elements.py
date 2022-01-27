"""PyQt interface to query elements."""

from typing import Tuple
import sys

from PyQt6 import QtCore, QtGui
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
import numpy as np

from rimseval.utilities import ini


class PeriodicTable(QMainWindow):
    """Periodic table main window with clickable buttons for all elements."""

    def __init__(self) -> None:
        """Initialize the periodic table class."""
        super().__init__()

        self.setWindowTitle("Periodic Table of Elements")

        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        self.main_layout = QGridLayout()
        main_widget.setLayout(self.main_layout)

        self.create_buttons()

    def create_buttons(self) -> None:
        """Creates buttons for all elements and aligns them on the main widget."""
        eles = list(ini.ele_dict.keys())

        for ele in eles:
            button = QPushButton(ele)
            button.pressed.connect(lambda val=ele: self.open_element(val))
            button.setFixedWidth(40)
            button.setFixedHeight(40)

            row, col, color = element_position_color(ele)
            button.setStyleSheet(f"background-color: {color}")
            self.main_layout.addWidget(button, row, col)

        # labels for lanthanides and actinides
        lbl_star = QLabel("*")
        lbl_star.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        lbl_2star = QLabel("**")
        lbl_2star.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        lbl_lanthanides = QLabel("*")
        lbl_lanthanides.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        lbl_actinides = QLabel("**")
        lbl_actinides.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self.main_layout.addWidget(lbl_star, 5, 2)
        self.main_layout.addWidget(lbl_2star, 6, 2)
        self.main_layout.addWidget(lbl_lanthanides, 7, 2)
        self.main_layout.addWidget(lbl_actinides, 8, 2)

    def open_element(self, ele):
        """Opens an element in a QWidget window.

        :param ele: Name of element
        """
        dialog = ElementInfo(self, ele)
        dialog.show()


class ElementInfo(QDialog):
    """Open a QDialog specified to my needs for element information."""

    def __init__(self, parent: QMainWindow, ele: str):
        """Initialilze the dialog.

        :param parent: Parent of QDialog
        :param ele: Element name.
        """
        super().__init__(parent)

        self.setWindowTitle(ele)

        self.ele = ele

        self.font_ele = QtGui.QFont()
        self.font_ele.setBold(True)
        self.font_ele.setPixelSize(32)

        # layout
        main_layout = QHBoxLayout()

        self.left_layout = QVBoxLayout()
        self.right_layout = QVBoxLayout()

        main_layout.addLayout(self.left_layout)
        main_layout.addStretch()
        main_layout.addLayout(self.right_layout)
        self.setLayout(main_layout)

        # fill layouts
        self.element_and_ms()  # element must be drawn before mass spectrum
        self.element_data()

    @staticmethod
    def copy_to_clipboard(text: str) -> None:
        """Copies given text to clipboard."""
        app.clipboard().setText(text)

    def element_and_ms(self) -> None:
        """Create a table with all the element data of interest and add to layout."""
        # element
        zz = ini.ele[self.ele].z
        ele_layout = QHBoxLayout()
        lbl = QLabel(f"<sub>{zz}</sub>{self.ele}")
        lbl.setFont(self.font_ele)
        ele_layout.addStretch()
        ele_layout.addWidget(lbl)
        ele_layout.addStretch()
        self.left_layout.addStretch()
        self.left_layout.addLayout(ele_layout)
        self.left_layout.addStretch()

        # draw MS
        isos = ini.iso[self.ele]
        abus = isos.abu_rel
        masses = isos.a

        drawing = QLabelClickable("")
        drawing.setToolTip("Click to copy all abundances to clipboard")

        width = 150
        height = 100
        canvas = QtGui.QPixmap(width, height)
        canvas.fill(QtGui.QColor("#c3d0ff"))

        painter = QtGui.QPainter(canvas)
        pen = QtGui.QPen()

        # draw mass lines
        pen.setWidth(7)
        pen.setColor(QtGui.QColor("#001666"))
        painter.setPen(pen)

        spacing = 10

        max_mass_spacing = get_max_mass_spacing()
        iso_spacing = (width - 2 * spacing) / max_mass_spacing
        if not isinstance(masses, np.ndarray):
            mass_spacing = 0
            abu_max = 1.0
            abus = np.array([abus])
            masses = np.array([masses])
        else:
            mass_spacing = masses[-1] - masses[0]
            abu_max = abus.max()
        xpos_shift = int((max_mass_spacing - mass_spacing) * iso_spacing / 2)
        max_height = height - 2 * spacing

        for it, abu in enumerate(abus):  # note: painting starts top left as 0,0
            if abu != 0:
                xpos = int(
                    spacing + (masses[it] - masses.min()) * iso_spacing + xpos_shift
                )
                ystart = int(spacing + max_height * (1 - abu / abu_max))
                painter.drawLine(xpos, ystart, xpos, height - spacing)

        painter.end()

        # connect abus to clickable label
        abus_str = "\t".join([str(tmp) for tmp in abus]) + "\n"
        drawing.clicked.connect(lambda val=abus_str: self.copy_to_clipboard(val))

        drawing.setPixmap(canvas)
        self.left_layout.addWidget(drawing)

    def element_data(self) -> None:
        """Create table for element information: the data."""
        layout_names = QVBoxLayout()
        layout_masses = QVBoxLayout()
        layout_abus = QVBoxLayout()

        # titles
        font_italic = QtGui.QFont()
        font_italic.setItalic(True)
        hdr_names = QLabel("Isotope")
        hdr_names.setFont(font_italic)
        hdr_masses = QLabel("Mass")
        hdr_masses.setFont(font_italic)
        hdr_abus = QLabel("Rel. Abundance")
        hdr_abus.setFont(font_italic)
        layout_names.addWidget(hdr_names)
        layout_masses.addWidget(hdr_masses)
        layout_abus.addWidget(hdr_abus)

        isos = ini.iso[self.ele]
        names = isos.name
        abus = isos.abu_rel
        masses = isos.mass

        if not isinstance(names, list):
            names = [names]
            abus = np.array([abus])
            masses = np.array([masses])

        # fill layout
        for name, abu, mass in zip(names, abus, masses):
            a, ele = split_iso_name(name)
            name_label = QLabel(f"<sup>{a}</sup>{ele}")

            mass_label = QLabelClickable(f"{mass:.2f}")
            mass_label.setToolTip("Click to copy to clipboard")
            mass_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
            mass_label.clicked.connect(
                lambda val=f"{mass}\n": self.copy_to_clipboard(val)
            )
            abu_label = QLabelClickable(f"{abu:.5f}")
            abu_label.setToolTip("Click to copy to clipboard")
            abu_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
            abu_label.clicked.connect(
                lambda val=f"{abu}\n": self.copy_to_clipboard(val)
            )

            layout_names.addWidget(name_label)
            layout_masses.addWidget(mass_label)
            layout_abus.addWidget(abu_label)

        # add to main layout
        layout = QHBoxLayout()
        layout.addLayout(layout_names)
        layout.addStretch()
        layout.addLayout(layout_masses)
        layout.addStretch()
        layout.addLayout(layout_abus)
        self.right_layout.addLayout(layout)
        self.right_layout.addStretch()


class QLabelClickable(QLabel):
    """Create a clickable QLabel to connect."""

    clicked = QtCore.pyqtSignal()

    def __init__(self, parent):
        """Initialize the regular QLabel."""
        super().__init__(parent)

    def mousePressEvent(self, ev):
        """Emit a ``clicked`` signal on mousePressEvent."""
        self.clicked.emit()


def element_position_color(ele: str) -> Tuple[int, int, str]:
    """Return the position of an element in grid view.

    :param ele: Element abbreviation.

    :return: Row, Column position and color as HEX.
    """
    positions_colors = {
        "H": (0, 0, "#ffffc7"),
        "He": (0, 17, "#ffe4bb"),
        "Li": (1, 0, "#ffc9c9"),
        "Be": (1, 1, "#d7d7ff"),
        "B": (1, 12, "#e1eebd"),
        "C": (1, 13, "#ffffc7"),
        "N": (1, 14, "#ffffc7"),
        "O": (1, 15, "#ffffc7"),
        "F": (1, 16, "#ffffc7"),
        "Ne": (1, 17, "#ffe4bb"),
        "Na": (2, 0, "#ffc9c9"),
        "Mg": (2, 1, "#d7d7ff"),
        "Al": (2, 12, "#c8ffc8"),
        "Si": (2, 13, "#e1eebd"),
        "P": (2, 14, "#ffffc7"),
        "S": (2, 15, "#ffffc7"),
        "Cl": (2, 16, "#ffffc7"),
        "Ar": (2, 17, "#ffe4bb"),
        "K": (3, 0, "#ffc9c9"),
        "Ca": (3, 1, "#d7d7ff"),
        "Sc": (3, 2, "#bbddff"),
        "Ti": (3, 3, "#bbddff"),
        "V": (3, 4, "#bbddff"),
        "Cr": (3, 5, "#bbddff"),
        "Mn": (3, 6, "#bbddff"),
        "Fe": (3, 7, "#bbddff"),
        "Co": (3, 8, "#bbddff"),
        "Ni": (3, 9, "#bbddff"),
        "Cu": (3, 10, "#bbddff"),
        "Zn": (3, 11, "#bbddff"),
        "Ga": (3, 12, "#c8ffc8"),
        "Ge": (3, 13, "#e1eebd"),
        "As": (3, 14, "#e1eebd"),
        "Se": (3, 15, "#ffffc7"),
        "Br": (3, 16, "#ffffc7"),
        "Kr": (3, 17, "#ffe4bb"),
        "Rb": (4, 0, "#ffc9c9"),
        "Sr": (4, 1, "#d7d7ff"),
        "Y": (4, 2, "#bbddff"),
        "Zr": (4, 3, "#bbddff"),
        "Nb": (4, 4, "#bbddff"),
        "Mo": (4, 5, "#bbddff"),
        "Tc": (4, 6, "#bbddff"),
        "Ru": (4, 7, "#bbddff"),
        "Rh": (4, 8, "#bbddff"),
        "Pd": (4, 9, "#bbddff"),
        "Ag": (4, 10, "#bbddff"),
        "Cd": (4, 11, "#bbddff"),
        "In": (4, 12, "#c8ffc8"),
        "Sn": (4, 13, "#c8ffc8"),
        "Sb": (4, 14, "#e1eebd"),
        "Te": (4, 15, "#e1eebd"),
        "I": (4, 16, "#ffffc7"),
        "Xe": (4, 17, "#ffe4bb"),
        "Cs": (5, 0, "#ffc9c9"),
        "Ba": (5, 1, "#d7d7ff"),
        "Hf": (5, 3, "#bbddff"),
        "Ta": (5, 4, "#bbddff"),
        "W": (5, 5, "#bbddff"),
        "Re": (5, 6, "#bbddff"),
        "Os": (5, 7, "#bbddff"),
        "Ir": (5, 8, "#bbddff"),
        "Pt": (5, 9, "#bbddff"),
        "Au": (5, 10, "#bbddff"),
        "Hg": (5, 11, "#bbddff"),
        "Tl": (5, 12, "#c8ffc8"),
        "Pb": (5, 13, "#c8ffc8"),
        "Bi": (5, 14, "#c8ffc8"),
        "Po": (5, 15, "#e1eebd"),
        "At": (5, 16, "#ffffc7"),
        "Rn": (5, 17, "#ffe4bb"),
        "Fr": (6, 0, "#ffc9c9"),
        "Ra": (6, 1, "#d7d7ff"),
        "Rf": (6, 3, "#bbddff"),
        "Db": (6, 4, "#bbddff"),
        "Sg": (6, 5, "#bbddff"),
        "Bh": (6, 6, "#bbddff"),
        "Hs": (6, 7, "#bbddff"),
        "Mt": (6, 8, "#bbddff"),
        "Ds": (6, 9, "#bbddff"),
        "Rg": (6, 10, "#bbddff"),
        "Cn": (6, 11, "#bbddff"),
        "Nh": (6, 12, "#c8ffc8"),
        "Fl": (6, 13, "#c8ffc8"),
        "Mc": (6, 14, "#c8ffc8"),
        "Lv": (6, 15, "#c8ffc8"),
        "Ts": (6, 16, "#ffffc7"),
        "Og": (6, 17, "#ffe4bb"),
        "La": (7, 3, "#b9ffff"),
        "Ce": (7, 4, "#b9ffff"),
        "Pr": (7, 5, "#b9ffff"),
        "Nd": (7, 6, "#b9ffff"),
        "Pm": (7, 7, "#b9ffff"),
        "Sm": (7, 8, "#b9ffff"),
        "Eu": (7, 9, "#b9ffff"),
        "Gd": (7, 10, "#b9ffff"),
        "Tb": (7, 11, "#b9ffff"),
        "Dy": (7, 12, "#b9ffff"),
        "Ho": (7, 13, "#b9ffff"),
        "Er": (7, 14, "#b9ffff"),
        "Tm": (7, 15, "#b9ffff"),
        "Yb": (7, 16, "#b9ffff"),
        "Lu": (7, 17, "#b9ffff"),
        "Ac": (8, 3, "#cdffee"),
        "Th": (8, 4, "#cdffee"),
        "Pa": (8, 5, "#cdffee"),
        "U": (8, 6, "#cdffee"),
        "Np": (8, 7, "#cdffee"),
        "Pu": (8, 8, "#cdffee"),
        "Am": (8, 9, "#cdffee"),
        "Cm": (8, 10, "#cdffee"),
        "Bk": (8, 11, "#cdffee"),
        "Cf": (8, 12, "#cdffee"),
        "Es": (8, 13, "#cdffee"),
        "Fm": (8, 14, "#cdffee"),
        "Md": (8, 15, "#cdffee"),
        "No": (8, 16, "#cdffee"),
        "Lr": (8, 17, "#cdffee"),
    }

    return positions_colors[ele]


def get_max_mass_spacing() -> int:
    """Get the maximum number of isotopes available in this database."""
    retval = 0
    for ele in list(ini.ele_dict.keys()):
        isos_a = ini.iso[ele].a
        if (dm := isos_a.max() - isos_a.min()) > retval:
            retval = dm
    return retval


def split_iso_name(iso: str) -> Tuple[int, str]:
    """Split an isotope name into its components.

    :param iso: Name of isotope formatted, e.g., as "He-3"

    :return: A, Name, e.g., (3, "He").
    """
    iso_split = iso.split("-")
    return int(iso_split[1]), iso_split[0]


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PeriodicTable()
    window.show()
    app.exec()
