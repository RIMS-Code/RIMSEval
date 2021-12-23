"""Function test for processor."""

from pathlib import Path

import numpy as np

from rimseval.processor import CRDFileProcessor
import rimseval.processor_utils as pu


def test_data_dimension_after_dead_time_correction(crd_file):
    """Ensure ToF and data have the same dimensions - BF 2021-07-23."""
    _, _, _, fname = crd_file
    crd = CRDFileProcessor(Path(fname))
    crd.spectrum_full()
    crd.dead_time_correction(3)

    assert crd.tof.ndim == crd.data.ndim


def test_mass_calibration_2pts(crd_file):
    """Perform mass calibration with two points."""
    _, _, _, fname = crd_file
    params = (13, 42)
    tms = (42.0, 95.0)

    mass_cal = np.zeros((len(tms), 2))
    for it, tm in enumerate(tms):
        mass_cal[it][0] = tm
        mass_cal[it][1] = pu.tof_to_mass(tm, params[0], params[1])

    # set variables
    crd = CRDFileProcessor(Path(fname))
    crd.spectrum_full()

    crd.def_mcal = mass_cal
    mass_exp = pu.tof_to_mass(crd.tof, params[0], params[1])

    crd.mass_calibration()
    mass_rec = crd.mass
    print(tms)
    np.testing.assert_almost_equal(mass_rec, mass_exp)
    assert crd.mass.ndim == crd.tof.ndim


def test_filter_max_ions_per_shot(crd_file):
    """Test maximum ions per shot filtering without packages."""
    header, ions_per_shot, all_tofs, fname = crd_file
    max_ions = max(ions_per_shot) - 1  # filter the highest one out

    crd = CRDFileProcessor(Path(fname))
    crd.filter_max_ions_per_shot(max_ions)

    ions_per_shot_filtered = ions_per_shot[np.where(ions_per_shot <= max_ions)]
    nof_shots = len(ions_per_shot_filtered)
    nof_ions = np.sum(ions_per_shot_filtered)

    assert crd.nof_shots == nof_shots
    assert np.sum(crd.data) == nof_ions


def test_filter_max_ions_per_shot_pkg(crd_file):
    """Test maximum ions per shot filtering with packages."""
    header, ions_per_shot, all_tofs, fname = crd_file
    max_ions = max(ions_per_shot) - 1  # filter the highest one out
    shots_per_pkg = 2

    crd = CRDFileProcessor(Path(fname))
    crd.packages(shots_per_pkg)
    crd.filter_max_ions_per_shot(max_ions)

    # assert that package data are the same as the rest
    assert crd.nof_shots == crd.nof_shots_pkg.sum()
    assert crd.data.sum() == crd.data_pkg.sum()


def test_filter_max_ions_per_shot_pkg_filtered(crd_file):
    """Test maximum ions per shot filtering with packages and pkg filter applied."""
    header, ions_per_shot, all_tofs, fname = crd_file
    shots_per_pkg = 2
    max_ions = 1
    max_ions_per_pkg = 4

    crd = CRDFileProcessor(Path(fname))
    crd.packages(shots_per_pkg)
    crd.filter_max_ions_per_pkg(max_ions_per_pkg)
    crd.filter_max_ions_per_shot(max_ions)

    # assert that package data are the same as the rest
    assert crd.nof_shots == crd.nof_shots_pkg.sum()
    assert crd.data.sum() == crd.data_pkg.sum()


def test_filter_max_ions_per_time(crd_file):
    """Test maximum ions per shot in given time window."""
    header, ions_per_shot, all_tofs, fname = crd_file
    max_ions = 1  # filter the highest one out
    time_window_us = 39 * 100 / 1e6  # 40 channels, filters third but not fifth

    crd = CRDFileProcessor(Path(fname))
    crd.filter_max_ions_per_time(max_ions, time_window_us)

    assert crd.nof_shots == len(ions_per_shot) - 1
    assert np.sum(crd.data) == np.sum(ions_per_shot) - 4
