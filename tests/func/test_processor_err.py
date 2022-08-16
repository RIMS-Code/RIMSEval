"""Test error messages of the processor."""

from pathlib import Path

import numpy as np
import pytest

from rimseval import CRDFileProcessor


def test_dead_time_correction_no_shots(crd_file):
    """Raise warning if no shots were present in the crd file."""
    _, _, _, fname = crd_file

    crd = CRDFileProcessor(Path(fname))
    crd.nof_shots = 0

    msg_exp = "No data available"

    with pytest.warns(UserWarning, match=msg_exp):
        crd.dead_time_correction(10)


def test_filter_max_ions_per_pkg_smaller_one(crd_file):
    """Raise ValueError if max ions per pkg filter is smaller than 1."""
    _, _, _, fname = crd_file

    crd = CRDFileProcessor(Path(fname))

    err_exp = "The maximum number of ions must be larger than 1."

    with pytest.raises(ValueError) as err:
        crd.filter_max_ions_per_pkg(0)

    msg = err.value.args[0]
    assert err_exp == msg


def test_filter_max_ions_per_pkg_no_pkg_data(crd_file):
    """Raise OSError if no packaged data is available."""
    _, _, _, fname = crd_file

    crd = CRDFileProcessor(Path(fname))

    err_exp = "There is no packaged data."

    with pytest.raises(OSError) as err:
        crd.filter_max_ions_per_pkg(1)

    msg = err.value.args[0]
    assert err_exp in msg


def test_filter_max_ions_per_shot_smaller_one(crd_file):
    """Raise ValueError if number of shots is smaller than 1."""
    _, _, _, fname = crd_file

    crd = CRDFileProcessor(Path(fname))

    err_exp = "The maximum number of ions"

    with pytest.raises(ValueError) as err:
        crd.filter_max_ions_per_shot(0)

    msg = err.value.args[0]
    assert err_exp in msg


def test_filter_max_ions_per_tof_window(crd_file):
    """Raise ValueError if ToF window of wrong shape."""
    _, _, _, fname = crd_file

    crd = CRDFileProcessor(Path(fname))

    err_exp = "ToF window must be specified with two entries"

    with pytest.raises(ValueError) as err:
        crd.filter_max_ions_per_tof_window(10, np.array([13, 54, 199]))

    msg = err.value.args[0]
    assert err_exp in msg


def test_integral_windows_no_integrals_set(crd_file):
    """Raise ValueError if no integrals were set."""
    _, _, _, fname = crd_file

    crd = CRDFileProcessor(Path(fname))

    err_exp = "No integrals were set"

    with pytest.raises(ValueError) as err:
        crd.integrals_calc()

    msg = err.value.args[0]
    assert err_exp in msg


def test_integral_windows_no_mass(crd_file):
    """Raise ValueError if no mass calibration was applied."""
    _, _, _, fname = crd_file

    crd = CRDFileProcessor(Path(fname))
    peak_names = ["54Fe", "64Ni"]
    peak_limits = np.array([[53.8, 54.2], [63.5, 64.5]])
    crd.def_integrals = (peak_names, peak_limits)

    err_exp = "A mass calibration needs to be applied first"

    with pytest.raises(ValueError) as err:
        crd.integrals_calc()

    msg = err.value.args[0]
    assert err_exp in msg


def test_integral_calc_delta_no_integrals_set(crd_file):
    """Raise ValueError if no integrals were set."""
    _, _, _, fname = crd_file

    crd = CRDFileProcessor(Path(fname))

    err_exp = "No integrals were defined"

    with pytest.raises(ValueError) as err:
        crd.integrals_calc_delta()

    msg = err.value.args[0]
    assert err_exp in msg


def test_mass_calibration_no_params_set(crd_file):
    """Raise ValueError if mcal parameters were set."""
    _, _, _, fname = crd_file

    crd = CRDFileProcessor(Path(fname))

    err_exp = "No mass calibration was set"

    with pytest.raises(ValueError) as err:
        crd.mass_calibration()

    msg = err.value.args[0]
    assert err_exp in msg


def test_packages_wrong_shots(crd_file):
    """Raise ValueError if number of shots is too small or too large."""
    _, _, _, fname = crd_file

    crd = CRDFileProcessor(Path(fname))

    err_exp = "Number of shots per package must be between"

    with pytest.raises(ValueError) as err:
        crd.packages(0)

    msg = err.value.args[0]
    assert err_exp in msg


def test_spectrum_part_range_wrong_order(crd_file):
    """Raise ValueError range is in incorrect order."""
    _, _, _, fname = crd_file

    crd = CRDFileProcessor(Path(fname))

    err_exp = "such that `from` < `to`"

    with pytest.raises(ValueError) as err:
        crd.spectrum_part([[10, 4]])

    msg = err.value.args[0]
    assert err_exp in msg


def test_spectrum_part_range_not_mutually_exclusive(crd_file):
    """Raise ValueError ranges are not mutually exclusive."""
    _, _, _, fname = crd_file

    crd = CRDFileProcessor(Path(fname))

    err_exp = "Your ranges are not mutually exclusive"

    with pytest.raises(ValueError) as err:
        crd.spectrum_part([[4, 10], [8, 12]])

    msg = err.value.args[0]
    assert err_exp in msg
