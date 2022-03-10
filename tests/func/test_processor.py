"""Function test for processor class methods, focusing on each function."""

from pathlib import Path

import pytest
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


def test_filter_max_ions_per_pkg(crd_file):
    """Filter the packages by maximum ion."""
    _, ions_per_shot, _, fname = crd_file
    max_ions = ions_per_shot.max() - 1  # filter one or so packages out
    sum_ions = 0
    for ion in ions_per_shot:
        if ion <= max_ions:
            sum_ions += ion

    crd = CRDFileProcessor(Path(fname))
    crd.spectrum_full()
    crd.packages(1)
    crd.filter_max_ions_per_pkg(max_ions)
    assert crd.data_pkg.sum() == sum_ions


def test_filter_max_ions_per_shot(crd_file):
    """Filter the shots by maximum ions per shot."""
    _, ions_per_shot, _, fname = crd_file
    max_ions = ions_per_shot.min() + 1  # filter most out
    filtered_data = ions_per_shot[np.where(ions_per_shot <= max_ions)]
    sum_ions_exp = np.sum(filtered_data)
    nof_shots_exp = len(filtered_data)

    crd = CRDFileProcessor(Path(fname))
    crd.spectrum_full()
    crd.filter_max_ions_per_shot(max_ions)

    assert crd.nof_shots == nof_shots_exp
    assert crd.data.sum() == sum_ions_exp
    np.testing.assert_equal(crd.ions_per_shot, filtered_data)


def test_filter_max_ions_per_shot_double(crd_file):
    """Test filterting max ions per shot twice (no pkgs)."""
    header, ions_per_shot, all_tofs, fname = crd_file
    max_ions1 = max(ions_per_shot) - 1  # filter the highest one out
    max_ions2 = min(ions_per_shot) + 1

    crd = CRDFileProcessor(Path(fname))
    crd.spectrum_full()
    crd.filter_max_ions_per_shot(max_ions1)
    crd.filter_max_ions_per_shot(max_ions2)

    ions_per_shot_filtered = ions_per_shot[np.where(ions_per_shot <= max_ions2)]
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
    crd.spectrum_full()
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
    crd.spectrum_full()
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
    crd.spectrum_full()
    crd.filter_max_ions_per_time(max_ions, time_window_us)

    assert crd.nof_shots == len(ions_per_shot) - 1
    assert np.sum(crd.data) == np.sum(ions_per_shot) - 4


def test_filter_max_ions_per_tof_window(crd_file):
    """Test maximum ions per shot in given time window."""
    header, ions_per_shot, all_tofs, fname = crd_file
    max_ions = 1  # filter the highest one out
    tof_window_us = (
        np.array([221, 281]) * 100 / 1e6
    )  # filter out the last one, but none of the others

    crd = CRDFileProcessor(Path(fname))
    crd.spectrum_full()
    crd.filter_max_ions_per_tof_window(max_ions, tof_window_us)

    assert crd.nof_shots == len(ions_per_shot) - 1
    assert np.sum(crd.data) == np.sum(ions_per_shot) - 2


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


@pytest.mark.parametrize("new_integral", [None, (["Int2"], np.array([[3.0, 4.0]]))])
def test_integrals_definition_delete_undefined_background_to_none(
    crd_file, new_integral
):
    """Delete backgrounds and set to none if peak goes to undefined."""
    _, _, _, fname = crd_file
    crd = CRDFileProcessor(Path(fname))

    crd.def_integrals = ["Integral"], np.array([[1.0, 2.0]])
    crd.def_backgrounds = ["Integral"], np.array([[2.0, 3.0]])
    crd.def_integrals = new_integral
    assert crd.def_backgrounds is None


def test_integrals_definition_delete_undefined_background(crd_file):
    """Delete backgrounds and set to none if peak goes to undefined."""
    _, _, _, fname = crd_file
    crd = CRDFileProcessor(Path(fname))

    crd.def_integrals = ["Int1", "Int2"], np.array([[1.0, 2.0], [2.0, 3.0]])
    crd.def_backgrounds = ["Int1", "Int2"], np.array([[2.0, 3.0], [4.0, 5.0]])
    crd.def_integrals = ["Int1"], np.array([[1.0, 2.0]])

    assert "Int2" not in crd.def_backgrounds[0]


def test_integrals_delta_calc(crd_int_delta):
    """Assure that the delta calculation on the integral returns correct values."""
    crd_int_delta.integrals_calc_delta()
    deltas_exp = np.array([0, 0, 0, 0, np.nan, np.nan, np.nan])
    deltas_rec = crd_int_delta.integrals_delta.transpose()[0]  # test only deltas
    np.testing.assert_almost_equal(deltas_exp, deltas_rec)
    for line in crd_int_delta.integrals_pkg:
        np.testing.assert_almost_equal(crd_int_delta.integrals, line)


def test_packages(crd_file):
    """Simple test to ensure packages are made in two ways correctly."""
    _, ions_per_shot, _, fname = crd_file
    nof_shots = len(ions_per_shot)
    crd = CRDFileProcessor(Path(fname))
    crd.spectrum_full()
    crd.packages(nof_shots // 2)

    assert crd.data_pkg.sum() == crd.data.sum()
    np.testing.assert_equal(crd.data_pkg.sum(axis=0), crd.data)
    assert crd.nof_shots_pkg.sum() == crd.nof_shots
    # now redo w/ a lower number of shots per pkg
    crd.packages(nof_shots // 4)
    assert crd.data_pkg.sum() == crd.data.sum()
    np.testing.assert_equal(crd.data_pkg.sum(axis=0), crd.data)
    assert crd.nof_shots_pkg.sum() == crd.nof_shots


def test_sort_integrals(crd_file):
    """Sort integrals by first mass."""
    _, _, _, fname = crd_file
    crd = CRDFileProcessor(Path(fname))
    crd.sort_integrals()  # does nothing, since None
    crd.def_integrals = ["Fe-56", "Ti-46"], np.array([[55.8, 56.2], [45.8, 46.2]])

    crd.integrals = np.array([[2, 2], [1, 1]])
    crd.integrals_pkg = np.array([crd.integrals, crd.integrals - 1])

    names_exp = ["Ti-46", "Fe-56"]
    values_exp = np.array([[45.8, 46.2], [55.8, 56.2]])
    integrals_exp = np.array([[1, 1], [2, 2]])
    integrals_pkg_exp = np.array([[[1, 1], [2, 2]], [[0, 0], [1, 1]]])

    crd.sort_integrals()
    names_rec, values_rec = crd.def_integrals
    assert names_rec == names_exp
    np.testing.assert_equal(values_rec, values_exp)
    np.testing.assert_equal(crd.integrals, integrals_exp)
    np.testing.assert_equal(crd.integrals_pkg, integrals_pkg_exp)


def test_spectrum_part(crd_file):
    """Cut spectrum by two shots."""
    _, ions_per_shot, _, fname = crd_file

    crd = CRDFileProcessor(Path(fname))
    crd.spectrum_full()
    crd.spectrum_part([1, len(ions_per_shot) - 2])

    assert crd.nof_shots == len(ions_per_shot) - 2


def test_spectrum_part_data_length(crd_file):
    """Ensure that the data length is not cut."""
    _, _, _, fname = crd_file

    crd = CRDFileProcessor(Path(fname))
    crd.spectrum_full()
    crd.spectrum_part([1, 2])

    assert len(crd.data) == len(crd.tof)


def test_spectrum_part_undo(crd_file):
    """Cut spectrum by two shots."""
    _, ions_per_shot, _, fname = crd_file

    crd = CRDFileProcessor(Path(fname))
    crd.spectrum_full()
    crd.spectrum_part([1, len(ions_per_shot) - 2])
    # undo the spectrum_part
    crd.spectrum_full()

    assert crd.nof_shots == len(ions_per_shot)
