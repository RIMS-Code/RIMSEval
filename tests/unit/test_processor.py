"""Unit tests for processor, focusing on multiple functions at a time."""

from pathlib import Path

import numpy as np
import pytest

from rimseval.processor import CRDFileProcessor


def test_integrals(crd_file):
    """Define an integral manually and calculate the integration."""
    _, ions_per_shot, all_tofs, fname = crd_file

    crd = CRDFileProcessor(Path(fname))
    crd.spectrum_full()

    # set some random mass cal from 1 to 2
    crd.def_mcal = np.array([[crd.tof.min(), 1.0], [crd.tof.max(), 2.0]])
    crd.mass_calibration()

    # now set the integrals to include everything
    crd.def_integrals = (["all"], np.array([[0.9, 2.1]]))  # avoid floating errors
    crd.integrals_calc()

    assert len(all_tofs) == crd.integrals[0][0]
    assert pytest.approx(np.sqrt(len(all_tofs)) == crd.integrals[0][1])


def test_integrals_bg_corr_behavior(crd_file):
    """Ensure that bg corrected integrals behave correctly."""
    _, ions_per_shot, all_tofs, fname = crd_file

    shots_per_pkg = 2
    nof_pkgs = int(np.ceil(len(ions_per_shot) / shots_per_pkg))
    integrals_exp = np.zeros((nof_pkgs, 1, 2))  # 1 integral

    start_ind = 0
    for it in range(nof_pkgs - 1):
        stop_ind = start_ind + shots_per_pkg
        integrals_exp[it][0][0] = np.sum(ions_per_shot[start_ind:stop_ind])
        integrals_exp[it][0][1] = np.sqrt(integrals_exp[it][0][0])
        start_ind = stop_ind
    # add the last
    integrals_exp[-1][0][0] = np.sum(ions_per_shot[start_ind:])
    integrals_exp[-1][0][1] = np.sqrt(integrals_exp[-1][0][0])

    crd = CRDFileProcessor(Path(fname))
    crd.spectrum_full()
    crd.packages(shots_per_pkg)

    # set some random mass cal from 1 to 2
    crd.def_mcal = np.array([[crd.tof.min(), 1.0], [crd.tof.max(), 2.0]])
    crd.mass_calibration()

    # now set the integrals to include everything
    crd.def_integrals = (["all"], np.array([[0.9, 2.1]]))  # avoid floating errors
    crd.integrals_calc()

    integrals_only = np.array(crd.integrals)
    integrals_pkg_only = np.array(crd.integrals_pkg)

    # set the background correction
    crd.def_backgrounds = (["all"], np.array([[0.1, 0.9]]))
    crd.integrals_calc()

    # now make sure that integrals are always smaller when bg corrected than when not
    assert all(crd.integrals[:, 0] <= integrals_only[:, 0])
    assert all(crd.integrals[:, 1] >= integrals_only[:, 1])

    # sum of packaged integrals is still equal to sum of integrals
    np.testing.assert_allclose(crd.integrals_pkg.sum(axis=0)[:, 0], crd.integrals[:, 0])


def test_integrals_pkg(crd_file):
    """Define an integral manually and calculate the integration for packages."""
    _, ions_per_shot, all_tofs, fname = crd_file

    shots_per_pkg = 2
    nof_pkgs = int(np.ceil(len(ions_per_shot) / shots_per_pkg))
    integrals_exp = np.zeros((nof_pkgs, 1, 2))  # 1 integral

    start_ind = 0
    for it in range(nof_pkgs - 1):
        stop_ind = start_ind + shots_per_pkg
        integrals_exp[it][0][0] = np.sum(ions_per_shot[start_ind:stop_ind])
        integrals_exp[it][0][1] = np.sqrt(integrals_exp[it][0][0])
        start_ind = stop_ind
    # add the last
    integrals_exp[-1][0][0] = np.sum(ions_per_shot[start_ind:])
    integrals_exp[-1][0][1] = np.sqrt(integrals_exp[-1][0][0])

    crd = CRDFileProcessor(Path(fname))
    crd.spectrum_full()
    crd.packages(shots_per_pkg)

    # set some random mass cal from 1 to 2
    crd.def_mcal = np.array([[crd.tof.min(), 1.0], [crd.tof.max(), 2.0]])
    crd.mass_calibration()

    # now set the integrals to include everything
    crd.def_integrals = (["all"], np.array([[0.9, 2.1]]))  # avoid floating errors
    crd.integrals_calc()

    np.testing.assert_almost_equal(crd.integrals_pkg, integrals_exp)

    # check that sum agrees -> sqrt of sqsum for uncertainty
    crd_integrals_sum = np.array(crd.integrals_pkg)
    crd_integrals_sum[:, :, 1] = crd_integrals_sum[:, :, 1] ** 2
    crd_integrals_sum = crd_integrals_sum.sum(axis=0)
    crd_integrals_sum[:, 1] = np.sqrt(crd_integrals_sum[:, 1])

    np.testing.assert_almost_equal(crd.integrals, crd_integrals_sum)


def test_integrals_pkg_with_filtering(crd_file):
    """Filtering in packages and get the sum of the integrals."""
    _, _, _, fname = crd_file
    shots_per_pkg = 1
    max_ions_per_shot = 1

    crd = CRDFileProcessor(Path(fname))
    crd.spectrum_full()
    crd.packages(shots_per_pkg)
    crd.filter_max_ions_per_pkg(1)

    # set some random mass cal from 1 to 2
    crd.def_mcal = np.array([[crd.tof.min(), 1.0], [crd.tof.max(), 2.0]])
    crd.mass_calibration()

    # now set the integrals to include everything
    crd.def_integrals = (["all"], np.array([[0.9, 2.1]]))  # avoid floating errors
    crd.integrals_calc()

    # check that sum agrees -> sqrt of sqsum for uncertainty
    crd_integrals_sum = np.array(crd.integrals_pkg)
    crd_integrals_sum[:, :, 1] = crd_integrals_sum[:, :, 1] ** 2
    crd_integrals_sum = crd_integrals_sum.sum(axis=0)
    crd_integrals_sum[:, 1] = np.sqrt(crd_integrals_sum[:, 1])

    np.testing.assert_almost_equal(crd.integrals, crd_integrals_sum)
