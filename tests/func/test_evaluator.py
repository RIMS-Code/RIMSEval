"""Function tests for evaluator class methods, focusing on each function."""

from pathlib import Path

import pytest
import numpy as np

from rimseval import data_io
from rimseval.evaluator import IntegralEvaluator


def test_init(crd_int_delta, integral_file, tmpdir):
    """Assure importing from file works the same as providing data."""
    int_file = Path(tmpdir).joinpath("test.csv")
    data_io.integrals.export(crd_int_delta, int_file)

    ev_file = IntegralEvaluator(int_file)
    ev_data = IntegralEvaluator(integral_file)

    assert ev_file.name == ev_data.name
    assert ev_file.names == ev_data.names
    assert ev_file.peaks == ev_data.peaks
    assert ev_file.timestamp_dict == ev_data.timestamp_dict
    np.testing.assert_array_equal(
        ev_file.integral_dict[ev_file.name], ev_data.integral_dict[ev_data.name]
    )


def test_init_empty():
    """Test the initialization of the integral evaluator without data."""
    ev = IntegralEvaluator()

    assert ev.name is None
    assert ev.names == []
    assert ev.peaks is None
    assert ev.timestamp_dict == {}
    assert ev.integral_dict == {}
    assert ev.correlation_set == set()


# PROPERTIES #


def test_correlation_set(integral_file):
    """Get the correlation property."""
    ev = IntegralEvaluator(integral_file)
    set_exp = {(2, 3), (1, 2)}
    ev._correlation_set = set_exp

    assert ev.correlation_set == set_exp


def test_deltas_no_standard(integral_file):
    """Raise error if no standard is loaded."""
    ev = IntegralEvaluator(integral_file)

    with pytest.raises(TypeError):
        _ = ev.deltas


def test_delta_labels(integral_file):
    """Get nicely formatted labels for delta-values."""
    ev = IntegralEvaluator(integral_file)
    ev.load_standard(ev)

    labels = ev.delta_labels
    assert len(labels) == len(ev.peaks)


def test_integrals(integral_file, crd_int_delta):
    """Return the summed integrals property for a simple case."""
    ev = IntegralEvaluator(integral_file)
    integrals = ev.integrals

    np.testing.assert_array_equal(integrals, crd_int_delta.integrals)


def test_integrals_multiple(tmpdir, integral_file, crd_int_delta):
    "Return the summed integrals for multiple samples."
    ev = IntegralEvaluator(integral_file)

    # second file with same data
    integral_file2 = Path(tmpdir).joinpath("second_file.csv")
    crd_int_delta.fname = integral_file2
    data_io.integrals.export(crd_int_delta, integral_file2)

    ev.add_integral(integral_file2)
    integrals = ev.integrals

    integrals_expected = np.zeros_like(crd_int_delta.integrals)
    for it in range(len(integrals_expected)):
        integrals_expected[it][0] = crd_int_delta.integrals[it][0] * 2
        integrals_expected[it][1] = np.sqrt(crd_int_delta.integrals[it][1] ** 2 * 2)

    np.testing.assert_array_almost_equal(integrals, integrals_expected)


# METHODS #


def test_add_integral_overwrite(tmpdir, integral_file, crd_int_delta):
    """Add an integral to the evaluator and overwrite the existing one."""
    ev = IntegralEvaluator(integral_file)
    crd_int_delta.integrals[3] = np.array([1, 2])
    integral_file2 = Path(tmpdir).joinpath("second_file.csv")
    data_io.integrals.export(crd_int_delta, integral_file2)

    ev.add_integral(integral_file2, overwrite=True)

    assert ev.name == crd_int_delta.name
    assert ev.names == [crd_int_delta.name]
    assert ev.peaks == crd_int_delta.def_integrals[0]
    assert ev.timestamp_dict == {crd_int_delta.name: crd_int_delta.timestamp}
    np.testing.assert_array_equal(ev.integrals, crd_int_delta.integrals)


def test_add_integral_exists_no_overwrite(integral_file):
    """Raise error if integral already exists and overwrite is False."""
    ev = IntegralEvaluator(integral_file)

    with pytest.raises(KeyError):
        ev.add_integral(integral_file)


def test_add_integral_peaks_not_the_same(tmpdir, integral_file, crd_int_delta):
    """Raise error if peaks are not the same."""
    ev = IntegralEvaluator(integral_file)

    peaks, peak_defs = crd_int_delta.def_integrals
    peaks[0] = "asdf"
    crd_int_delta.def_integrals = (peaks, peak_defs)
    integral_file2 = Path(tmpdir).joinpath("second_file.csv")
    data_io.integrals.export(crd_int_delta, integral_file2)

    with pytest.raises(ValueError):
        ev.add_integral(integral_file2, overwrite=True)


def test_add_integral_peaks_different_sorting(tmpdir, integral_file, crd_int_delta):
    """Raise error if peaks are not sorted the same."""
    ev = IntegralEvaluator(integral_file)
    peaks, peak_defs = crd_int_delta.def_integrals
    peaks = peaks[::-1]
    crd_int_delta.def_integrals = (peaks, peak_defs)
    integral_file2 = Path(tmpdir).joinpath("second_file.csv")
    data_io.integrals.export(crd_int_delta, integral_file2)

    with pytest.raises(ValueError):
        ev.add_integral(integral_file2, overwrite=True)


def test_correlation_coefficient_delta(integral_file):
    """Calculate correlation coefficient for d(54Fe/56Fe) and d(57Fe/56Fe)."""
    ev = IntegralEvaluator(integral_file)
    std = IntegralEvaluator(integral_file)
    ev.load_standard(std)

    indexes = (0, 2)

    corr_rec = ev.correlation_coefficient_delta(*indexes)

    corr_exp = (
        2
        * (ev.integrals[1][1] / ev.integrals[1][0]) ** 2
        / (
            ev.deltas[0][1]
            / (ev.deltas[0][0] + 1000)
            * ev.deltas[2][1]
            / (ev.deltas[2][0] + 1000)
        )
    )

    assert pytest.approx(corr_rec) == corr_exp
    assert ev.correlation_set == {(0, 2)}


def test_correlation_coefficient_delta_methods(integral_file):
    """Ensure all methods of calling the routine result in the same results."""
    ev = IntegralEvaluator(integral_file)
    std = IntegralEvaluator(integral_file)
    ev.load_standard(std)

    delta_labels = ev.delta_labels
    # pick d(54Fe/56Fe) and d(57Fe/56Fe)
    ind1, ind2 = 0, 2
    corr_delta = ev.correlation_coefficient_delta(
        delta_labels[ind1], delta_labels[ind2]
    )
    corr_ind = ev.correlation_coefficient_delta(ind1, ind2)
    corr_tuples = ev.correlation_coefficient_delta(
        tuple(ev._ratio_indexes[ind1]), tuple(ev._ratio_indexes[ind2])
    )
    corr_list = ev.correlation_coefficient_delta(
        list(ev._ratio_indexes[ind1]), list(ev._ratio_indexes[ind2])
    )
    corr_ndarray = ev.correlation_coefficient_delta(
        ev._ratio_indexes[ind1], ev._ratio_indexes[ind2]
    )
    assert corr_delta == corr_ind == corr_tuples == corr_list == corr_ndarray
    assert ev.correlation_set == {(ind1, ind2)}


def test_correlation_coefficient_delta_invalid_type(integral_file):
    """Raise TypeError if input is invalid."""
    ev = IntegralEvaluator(integral_file)
    std = IntegralEvaluator(integral_file)
    ev.load_standard(std)

    with pytest.raises(TypeError):
        _ = ev.correlation_coefficient_delta(0.1, 2.3)
    with pytest.raises(TypeError):
        _ = ev.correlation_coefficient_delta(0, 2.3)


def test_correlation_coefficient_delta_invalid_nominator(integral_file):
    """Raise ValueError if nominators are the same."""
    ev = IntegralEvaluator(integral_file)
    std = IntegralEvaluator(integral_file)
    ev.load_standard(std)

    with pytest.raises(ValueError):
        _ = ev.correlation_coefficient_delta(0, 0)


def test_correlation_coefficient_delta_invalid_denominator(integral_file):
    """Raise ValueError if denominators are not the same."""
    ev = IntegralEvaluator(integral_file)
    std = IntegralEvaluator(integral_file)
    ev.load_standard(std)

    with pytest.raises(ValueError):
        _ = ev.correlation_coefficient_delta(0, 4)


def test_correlation_coefficient_delta_invalid_string(integral_file):
    """Raise ValueError if input delta string cannot be found."""
    ev = IntegralEvaluator(integral_file)
    std = IntegralEvaluator(integral_file)
    ev.load_standard(std)

    delta_valid = ev.delta_labels[0]
    with pytest.raises(ValueError):
        _ = ev.correlation_coefficient_delta("test", delta_valid)
    with pytest.raises(ValueError):
        _ = ev.correlation_coefficient_delta(delta_valid, "test")


def test_correlation_coefficient_delta_invalid_tuple(integral_file):
    """Raise IndexError if input delta tuple cannot be found."""
    ev = IntegralEvaluator(integral_file)
    std = IntegralEvaluator(integral_file)
    ev.load_standard(std)

    with pytest.raises(IndexError):
        _ = ev.correlation_coefficient_delta((0, 20), (0, 2))
    with pytest.raises(IndexError):
        _ = ev.correlation_coefficient_delta((0, 1), (20, 2))


def test_correlation_coefficient_delta_invalid_int(integral_file):
    """Raise IndexError if input integer is out of range."""
    ev = IntegralEvaluator(integral_file)
    std = IntegralEvaluator(integral_file)
    ev.load_standard(std)

    with pytest.raises(IndexError):
        _ = ev.correlation_coefficient_delta(20, 2)
    with pytest.raises(IndexError):
        _ = ev.correlation_coefficient_delta(0, 20)


def test_load_standard(integral_file, crd_int_delta):
    """Load a standard into the evaluator."""
    ev = IntegralEvaluator(integral_file)
    std = IntegralEvaluator(integral_file)

    ev.load_standard(std)

    np.testing.assert_array_equal(ev.standard, crd_int_delta.integrals)


def test_load_standard_peaks_not_same(tmpdir, integral_file, crd_int_delta):
    """Raise error if peaks are not the same."""
    ev = IntegralEvaluator(integral_file)

    # create a new file with different peaks
    peaks, integrals = crd_int_delta.def_integrals
    peaks = peaks[::-1]
    crd_int_delta.def_integrals = peaks, integrals
    std_file = Path(tmpdir).joinpath("standard.csv")
    data_io.integrals.export(crd_int_delta, std_file)
    std = IntegralEvaluator(std_file)

    with pytest.raises(ValueError):
        ev.load_standard(std)


def test_reset_correlation_set(integral_file):
    """Reset the correlation set."""
    ev = IntegralEvaluator(integral_file)
    ev._correlation_set = {(0, 1), (2, 3)}
    ev.reset_correlation_set()

    assert ev.correlation_set == set()
