"""PyQt interface to query elements."""

from typing import Tuple
import sys

import iniabu
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import (
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


INIABU = iniabu.IniAbu(database="nist")


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
        eles = list(INIABU.ele_dict.keys())

        for ele in eles:
            button = QPushButton(ele)
            button.pressed.connect(lambda val=ele: self.open_element(val))
            button.setFixedWidth(40)
            button.setFixedHeight(40)

            row, col = element_position(ele)
            self.main_layout.addWidget(button, row, col)

        # labels for lanthanides and actinides
        lbl_star = QLabel("*")
        lbl_star.setAlignment(QtCore.Qt.AlignCenter)
        lbl_2star = QLabel("**")
        lbl_2star.setAlignment(QtCore.Qt.AlignCenter)
        lbl_lanthanides = QLabel("* Lanthanides")
        lbl_lanthanides.setAlignment(QtCore.Qt.AlignCenter)
        lbl_actinides = QLabel("** Actinides")
        lbl_actinides.setAlignment(QtCore.Qt.AlignCenter)
        self.main_layout.addWidget(lbl_star, 5, 2)
        self.main_layout.addWidget(lbl_2star, 6, 2)

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

    def element_and_ms(self) -> None:
        """Create a table with all the element data of interest and add to layout."""
        # element
        zz = INIABU.ele[self.ele].z
        ele_layout = QHBoxLayout()
        lbl = QLabel(f"<sub>{zz}</sub>{self.ele}")
        lbl.setFont(self.font_ele)
        ele_layout.addStretch()
        ele_layout.addWidget(lbl)
        ele_layout.addStretch()
        self.left_layout.addLayout(ele_layout)
        self.left_layout.addStretch()

        # draw MS
        isos = INIABU.iso[self.ele]
        abus = isos.abu_rel
        masses = isos.mass

        drawing = QLabel()
        width = 150
        height = 100
        canvas = QtGui.QPixmap(width, height)
        canvas.fill(QtGui.QColor("#c3d0ff"))
        drawing.setPixmap(canvas)

        painter = QtGui.QPainter(drawing.pixmap())
        pen = QtGui.QPen()

        # draw mass lines
        pen.setWidth(7)
        pen.setColor(QtGui.QColor("#001666"))
        painter.setPen(pen)

        spacing = 10
        # fixme: monoisotopic, no abundnaces for isotopes
        delta = (width - 2 * spacing) / (masses.max() - masses.min())
        max_height = height - 2 * spacing

        for it, abu in enumerate(abus):  # note: painting starts top left as 0,0
            xpos = int(spacing + (masses[it] - masses.min()) * delta)
            ystart = int(spacing + max_height * (1 - abu))
            painter.drawLine(xpos, ystart, xpos, height - spacing)

        painter.end()

        self.left_layout.addWidget(drawing)

    def element_data(self) -> None:
        """Create table for element information: the data."""
        pass


def element_position(ele: str) -> Tuple[int, int]:
    """Return the position of an element in grid view.

    :param ele: Element abbreviation.

    :return: Row, Column position as a tuple, zero based.
    """
    positions = {
        "H": (0, 0),
        "He": (0, 17),
        "Li": (1, 0),
        "Be": (1, 1),
        "B": (1, 12),
        "C": (1, 13),
        "N": (1, 14),
        "O": (1, 15),
        "F": (1, 16),
        "Ne": (1, 17),
        "Na": (2, 0),
        "Mg": (2, 1),
        "Al": (2, 12),
        "Si": (2, 13),
        "P": (2, 14),
        "S": (2, 15),
        "Cl": (2, 16),
        "Ar": (2, 17),
        "K": (3, 0),
        "Ca": (3, 1),
        "Sc": (3, 2),
        "Ti": (3, 3),
        "V": (3, 4),
        "Cr": (3, 5),
        "Mn": (3, 6),
        "Fe": (3, 7),
        "Co": (3, 8),
        "Ni": (3, 9),
        "Cu": (3, 10),
        "Zn": (3, 11),
        "Ga": (3, 12),
        "Ge": (3, 13),
        "As": (3, 14),
        "Se": (3, 15),
        "Br": (3, 16),
        "Kr": (3, 17),
        "Rb": (4, 0),
        "Sr": (4, 1),
        "Y": (4, 2),
        "Zr": (4, 3),
        "Nb": (4, 4),
        "Mo": (4, 5),
        "Tc": (4, 6),
        "Ru": (4, 7),
        "Rh": (4, 8),
        "Pd": (4, 9),
        "Ag": (4, 10),
        "Cd": (4, 11),
        "In": (4, 12),
        "Sn": (4, 13),
        "Sb": (4, 14),
        "Te": (4, 15),
        "I": (4, 16),
        "Xe": (4, 17),
        "Cs": (5, 0),
        "Ba": (5, 1),
        "Hf": (5, 3),
        "Ta": (5, 4),
        "W": (5, 5),
        "Re": (5, 6),
        "Os": (5, 7),
        "Ir": (5, 8),
        "Pt": (5, 9),
        "Au": (5, 10),
        "Hg": (5, 11),
        "Tl": (5, 12),
        "Pb": (5, 13),
        "Bi": (5, 14),
        "Po": (5, 15),
        "At": (5, 16),
        "Rn": (5, 17),
        "Fr": (6, 0),
        "Ra": (6, 1),
        "Rf": (6, 3),
        "Db": (6, 4),
        "Sg": (6, 5),
        "Bh": (6, 6),
        "Hs": (6, 7),
        "Mt": (6, 8),
        "Ds": (6, 9),
        "Rg": (6, 10),
        "Cn": (6, 11),
        "Nh": (6, 12),
        "Fl": (6, 13),
        "Mc": (6, 14),
        "Lv": (6, 15),
        "Ts": (6, 16),
        "Og": (6, 17),
        "La": (8, 3),
        "Ce": (8, 4),
        "Pr": (8, 5),
        "Nd": (8, 6),
        "Pm": (8, 7),
        "Sm": (8, 8),
        "Eu": (8, 9),
        "Gd": (8, 10),
        "Tb": (8, 11),
        "Dy": (8, 12),
        "Ho": (8, 13),
        "Er": (8, 14),
        "Tm": (8, 15),
        "Yb": (8, 16),
        "Lu": (8, 17),
        "Ac": (9, 3),
        "Th": (9, 4),
        "Pa": (9, 5),
        "U": (9, 6),
        "Np": (9, 7),
        "Pu": (9, 8),
        "Am": (9, 9),
        "Cm": (9, 10),
        "Bk": (9, 11),
        "Cf": (9, 12),
        "Es": (9, 13),
        "Fm": (9, 14),
        "Md": (9, 15),
        "No": (9, 16),
        "Lr": (9, 17),
    }

    return positions[ele]


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PeriodicTable()
    window.show()
    app.exec()
