"""Unit tests for legacy file reader."""

from pathlib import Path

import numpy as np
import pytest

from rimseval.compatibility.lion_eval import LIONEvalCal


def test_lion_eval_cal_file_type_error():
    """Raise TypeError if not initialized with a path."""
    with pytest.raises(TypeError):
        _ = LIONEvalCal(13)


def test_lion_eval_cal_file_all(legacy_files_path):
    """Read an existing calibration file with all information."""
    fname = Path(legacy_files_path).joinpath("all_cals.cal")
    cal = LIONEvalCal(fname)
    assert isinstance(cal.mass_cal, np.ndarray)
    assert isinstance(cal.integrals, list)
    assert isinstance(cal.bg_corr, list)


def test_lion_eval_cal_file_mcal_only(legacy_files_path):
    """Read an existing calibration file with only mass calibration."""
    fname = Path(legacy_files_path).joinpath("mcal_only.cal")
    cal = LIONEvalCal(fname)
    assert isinstance(cal.mass_cal, np.ndarray)
    assert cal.integrals is None
    assert cal.bg_corr is None


def test_lion_eval_cal_file_no_cal(legacy_files_path):
    """Read an existing calibration file with no calibration information."""
    fname = Path(legacy_files_path).joinpath("no_cal.cal")
    cal = LIONEvalCal(fname)
    assert cal.mass_cal is None
    assert cal.integrals is None
    assert cal.bg_corr is None


def test_lion_eval_applied_filters(legacy_files_path):
    """Set applied filters data from `lioneval_full_calfile`."""
    fname = Path(legacy_files_path).joinpath("lioneval_full_calfile.cal")
    cal = LIONEvalCal(fname)

    dict_exp = {
        "dead_time_corr": [True, 7],
        "packages": [True, 1000],
        "max_ions_per_shot": [True, 10],
        "max_ions_per_pkg": [True, 1000],
        "max_ions_per_time": [True, 50, float(200)],
        "max_ions_per_tof_window": [True, 100, [float(5), float(8)]],
        "spectrum_part": [True, [1, 70000]],
    }

    assert cal.applied_filters == dict_exp


def test_lion_eval_applied_filters_no_block(legacy_files_path):
    """No applied filters if no block given."""
    fname = Path(legacy_files_path).joinpath("lioneval_full_calfile.cal")
    cal = LIONEvalCal(fname)
    assert cal._read_and_set_settings_calculation(None) is None


def test_lion_eval_applied_filters_bad_settings(legacy_files_path):
    """Applied filters stays ``None`` if bad calibration file."""
    fname = Path(legacy_files_path).joinpath("bad_settings.cal")
    cal = LIONEvalCal(fname)
    assert cal.applied_filters is None
