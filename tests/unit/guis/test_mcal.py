"""Test mass calibration GUI."""

from pathlib import Path

from PyQt5.QtCore import Qt, QPoint
import pytest
import pytestqt

from rimseval import CRDFileProcessor
from rimseval.guis import mcal


def test_mass_calibration_gui(qtbot, crd_file):
    """Test Mass calibration window and functionality by clicking."""
    _, _, _, fname = crd_file
    crd = CRDFileProcessor(Path(fname))
    crd.spectrum_full()

    window = mcal.CreateMassCalibration(crd)
    window.show()
    qtbot.addWidget(window)

    # qtbot.mouseClick(window.sc, Qt.RightButton)  # select position with qpoint
    # todo: maybe: full calibration, etc. this at least tests if it runs.
    # check first if this even runs on github actions...
