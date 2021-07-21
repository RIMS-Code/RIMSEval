"""Unit tests for legacy file reader."""

from pathlib import Path

import numpy as np

from rimseval.compatibility.lion_eval import LIONEvalCal


def test_lion_eval_cal_file_all(legacy_files_path):
    """Read an existing calibration file with all information."""
    fname = Path(legacy_files_path).joinpath("all_cals.cal")
    cal = LIONEvalCal(fname)
    assert isinstance(cal.mass_cal, np.ndarray)
    assert isinstance(cal.integrals, list)
    assert isinstance(cal.bg_corr, list)


def test_lion_eval_cal_file_mcal_only(legacy_files_path):
    """Read an existing calibration file with all information."""
    fname = Path(legacy_files_path).joinpath("mcal_only.cal")
    cal = LIONEvalCal(fname)
    assert isinstance(cal.mass_cal, np.ndarray)
    assert cal.integrals is None
    assert cal.bg_corr is None
