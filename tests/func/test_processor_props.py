"""Function test for processor class properties."""

from pathlib import Path

import hypothesis
from hypothesis import given, HealthCheck, settings, strategies as st
import pytest
import numpy as np

from rimseval.processor import CRDFileProcessor


def test_def_backgrounds(crd_file):
    """Get / set background definitions."""
    _, _, _, fname = crd_file
    crd = CRDFileProcessor(Path(fname))

    # backgrounds not defined at start
    assert crd.def_backgrounds is None

    peak_names = ["54Fe", "54Fe"]
    peak_limits = np.array([[53.4, 53.6], [54.4, 54.6]])

    # set some backgrounds
    crd.def_backgrounds = (peak_names, peak_limits)
    ret_names, ret_limts = crd.def_backgrounds
    assert ret_names == peak_names
    np.testing.assert_equal(ret_limts, peak_limits)

    # unset backgrounds
    crd.def_backgrounds = None
    assert crd.def_backgrounds is None


def test_def_backgrounds_value_error(crd_file):
    """Raise value errors if backgrounds defined with wrong shape."""
    _, _, _, fname = crd_file
    crd = CRDFileProcessor(Path(fname))

    with pytest.raises(ValueError):
        crd.def_backgrounds = ["54Fe", 53, 54]
    with pytest.raises(ValueError):
        crd.def_backgrounds = (["54Fe"], np.array([]))
    with pytest.raises(ValueError):
        crd.def_backgrounds = (["54Fe"], np.array([[1, 2, 3]]))


def test_def_mcal(crd_file):
    """Get / set mass calibration definitions."""
    _, _, _, fname = crd_file
    crd = CRDFileProcessor(Path(fname))

    assert crd.def_mcal is None

    mass_cal = np.array([[64, 223.0], [66, 337.0]])
    crd.def_mcal = mass_cal
    np.testing.assert_equal(mass_cal, crd.def_mcal)


def test_def_mcal_type_error(crd_file):
    """Raise TypeError if mass calibration is set with none numpy array."""
    _, _, _, fname = crd_file
    crd = CRDFileProcessor(Path(fname))

    mass_cal = [[64, 223.0], [66, 337.0]]

    with pytest.raises(TypeError):
        crd.def_mcal = mass_cal


def test_def_mcal_value_error(crd_file):
    """Raise ValueError if mass_cal is of wrong shape."""
    _, _, _, fname = crd_file
    crd = CRDFileProcessor(Path(fname))

    with pytest.raises(ValueError):
        crd.def_mcal = np.array([[1.0, 2.0]])
    with pytest.raises(ValueError):
        crd.def_mcal = np.array([[1.0], [2.0], [3.0]])


def test_def_integrals(crd_file):
    """Get / set integral definitions."""
    _, _, _, fname = crd_file
    crd = CRDFileProcessor(Path(fname))

    # integrals not defined at start
    assert crd.def_integrals is None

    peak_names = ["54Fe", "64Ni"]
    peak_limits = np.array([[53.8, 54.2], [63.5, 64.5]])

    # set some integrals
    crd.def_integrals = (peak_names, peak_limits)
    ret_names, ret_limts = crd.def_integrals
    assert ret_names == peak_names
    np.testing.assert_equal(ret_limts, peak_limits)

    # unset integrals
    crd.def_integrals = None
    assert crd.def_integrals is None


def test_def_integrals_value_error(crd_file):
    """Raise value errors if integrals defined with wrong shape or non-unique peaks."""
    _, _, _, fname = crd_file
    crd = CRDFileProcessor(Path(fname))

    with pytest.raises(ValueError):
        crd.def_integrals = ["54Fe", 53, 54]
    with pytest.raises(ValueError):
        crd.def_integrals = (["54Fe"], np.array([]))
    with pytest.raises(ValueError):
        crd.def_integrals = (["54Fe"], np.array([[1, 2, 3]]))

    with pytest.raises(ValueError):
        crd.def_integrals = (["54Fe", "54Fe"], np.array([[53.8, 54.2], [63.5, 64.5]]))


@given(value=st.floats(allow_nan=False))
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=500)
def test_peak_fwhm(crd_file, value):
    """Get / set peak full width at half max."""
    _, _, _, fname = crd_file
    crd = CRDFileProcessor(Path(fname))

    crd.peak_fwhm = value
    assert crd.peak_fwhm == value


@given(value=st.floats(allow_nan=False))
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=500)
def test_us_to_chan(crd_file, value):
    """Get / set conversion factor for microseconds to channel."""
    _, _, _, fname = crd_file
    crd = CRDFileProcessor(Path(fname))

    crd.us_to_chan = value
    assert crd.us_to_chan == value
