"""Unit tests for processor, focusing on multiple functions at a time."""

from pathlib import Path

import numpy as np
import pytest

import rimseval
from rimseval import interfacer
from rimseval.processor import CRDFileProcessor


def test_filter_pkg_peirce_countrate(crd_file):
    """Apply Peirce countrate outlier rejection (run through, no assertions)."""
    _, _, _, fname = crd_file

    crd = CRDFileProcessor(Path(fname))
    crd.spectrum_full()
    crd.packages(2)

    # set some random mass cal from 1 to 2
    crd.def_mcal = np.array([[crd.tof.min(), 1.0], [crd.tof.max(), 2.0]])
    crd.mass_calibration()

    # now set the integrals to include everything
    crd.def_integrals = (["all"], np.array([[0.9, 2.1]]))  # avoid floating errors
    crd.integrals_calc()

    crd.filter_pkg_peirce_countrate()


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
    assert np.sqrt(len(all_tofs)) == pytest.approx(crd.integrals[0][1])


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


def test_integrals_multiple_backgrounds(crd_file):
    """Run bg correction with multiple backgrounds - run through only."""
    _, ions_per_shot, all_tofs, fname = crd_file

    crd = CRDFileProcessor(Path(fname))
    crd.spectrum_full()

    # set some random mass cal from 1 to 2
    crd.def_mcal = np.array([[crd.tof.min(), 1.0], [crd.tof.max(), 2.0]])
    crd.mass_calibration()

    # now set the integrals to include everything
    crd.def_integrals = (["all"], np.array([[0.9, 2.1]]))  # avoid floating errors
    crd.integrals_calc()

    # set the background correction
    crd.def_backgrounds = (["all", "all"], np.array([[0.1, 0.9], [2.1, 3.0]]))
    crd.integrals_calc(bg_corr=True)


def test_integrals_multiple_backgrounds_sorting(crd_file):
    """Ensure that everything is the same if backgrounds are sorted or not."""
    _, ions_per_shot, all_tofs, fname = crd_file

    # the unsorted way
    crd = CRDFileProcessor(Path(fname))
    crd.spectrum_full()

    # set some random mass cal from 1 to 2
    crd.def_mcal = np.array([[crd.tof.min(), 1.0], [crd.tof.max(), 2.0]])
    crd.mass_calibration()

    # now set the integrals to include everything
    crd.def_integrals = (
        ["pk1", "pk2"],
        np.array([[0.9, 1.4], [1.5, 2.1]]),
    )  # avoid floating errors
    crd.integrals_calc()

    # set the background correction
    crd.def_backgrounds = (["pk2", "pk1"], np.array([[2.1, 3.0], [0.1, 2.1]]))
    crd.integrals_calc(bg_corr=True)

    # the sorted way
    crd2 = CRDFileProcessor(Path(fname))
    crd2.spectrum_full()

    # set some random mass cal from 1 to 2
    crd2.def_mcal = np.array([[crd2.tof.min(), 1.0], [crd2.tof.max(), 2.0]])
    crd2.mass_calibration()

    # now set the integrals to include everything
    crd2.def_integrals = (
        ["pk1", "pk2"],
        np.array([[0.9, 1.4], [1.5, 2.1]]),
    )  # avoid floating errors
    crd2.integrals_calc()

    # set the background correction
    crd2.def_backgrounds = (["pk2", "pk1"], np.array([[2.1, 3.0], [0.1, 2.1]]))
    crd2.sort_backgrounds()
    crd2.integrals_calc(bg_corr=True)

    # make sure it's all the same
    assert crd2.def_backgrounds[0] == ["pk1", "pk2"]
    np.testing.assert_almost_equal(crd.integrals, crd2.integrals)

    # also make sure that the bg correction did something...
    crd.integrals_calc(bg_corr=False)
    assert (crd2.integrals < crd.integrals).any()


def test_background_one_bg_with_multiple_peaks(crd_data):
    """Ti Standard 01 spectrum with json file to do background correction."""
    crd = CRDFileProcessor(crd_data.joinpath("ti_standard_01.crd"))
    interfacer.load_cal_file(crd)
    crd.spectrum_full()
    crd.mass_calibration()
    crd.calculate_applied_filters()
    crd.integrals_calc(bg_corr=True)

    # assert background correction does not throw nans or zeros
    assert not np.isnan(crd.integrals).any()
    assert not (crd.integrals == 0).any()


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


def test_calculation_with_filters(crd_data, macro_path):
    """Test that reapplying all filters results in the correct data.

    Ensured that all filters do something on this file!

    :param crd_data: Fixture to return the data path to the CRD files.
    """
    fname = crd_data.joinpath("ti_standard_01.crd")
    crd = CRDFileProcessor(fname)
    crd.spectrum_full()
    crd.def_mcal = np.array([[1.41150472, 45.95262772], [1.84462075, 46.95175879]])
    crd.mass_calibration()

    crd.def_integrals = (
        ["46Ti", "47Ti", "48Ti", "49Ti", "50Ti"],
        np.array(
            [
                [45.81992524, 46.11577284],
                [46.83425987, 47.11601949],
                [47.82041853, 48.10217815],
                [48.83475316, 49.08833681],
                [49.8349998, 50.0604075],
            ]
        ),
    )
    crd.spectrum_part([1, 116000])
    crd.filter_max_ions_per_shot(280)
    crd.filter_max_ions_per_time(170, 10)
    crd.filter_max_ions_per_tof_window(20, np.array([2, 2.4]))
    crd.packages(1000)
    crd.filter_max_ions_per_pkg(500)

    macro_file = macro_path.joinpath("ex_max_ions_per_shot_for_filter_test.py")
    crd.run_macro(macro_file)

    crd.dead_time_correction(7)
    crd.integrals_calc()  # default conditions

    crd2 = CRDFileProcessor(fname)
    crd2.applied_filters = crd.applied_filters
    crd2.calculate_applied_filters()

    np.testing.assert_equal(crd.data, crd2.data)
    np.testing.assert_equal(crd.data_pkg, crd2.data_pkg)
    np.testing.assert_equal(crd.tof, crd2.tof)


def test_calculation_tof_spectrum_never_cut(crd_data):
    """Ensure tof spectrum length stays the same throughout filters"""
    fname = crd_data.joinpath("ti_standard_01.crd")
    crd = CRDFileProcessor(fname)
    interfacer.load_cal_file(crd)
    crd.spectrum_full()
    crd.mass_calibration()

    # cut the range, the set max ions per shot
    crd.spectrum_part([[1, 10000]])
    crd.filter_max_ions_per_shot(10)

    assert crd.data.shape == crd.tof.shape
    assert crd.data.shape == crd.mass.shape


def test_optimize_mcal(crd_data):
    """Optimize the mass calibration of a given spectrum.

    Ensure that it runs through. Assert that values are as before to within 1%.

    :param crd_data: Fixture to return the data path to the CRD files.
    """
    fname = crd_data.joinpath("ti_standard_01.crd")
    mcal_input = np.array([[1.41150472, 45.95262772], [1.84462075, 46.95175879]])
    crd = CRDFileProcessor(fname)
    crd.spectrum_full()
    crd.def_mcal = mcal_input
    crd.mass_calibration()
    crd.optimize_mcal()

    np.testing.assert_allclose(mcal_input, crd.def_mcal, rtol=0.01)
