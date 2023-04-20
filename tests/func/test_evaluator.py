"""Function tests for evaluator class methods, focusing on each function."""

from pathlib import Path

import pytest
import numpy as np

from rimseval import data_io
from rimseval.evaluator import IntegralEvaluator


def test_init(integral_data):
    """Test the initialization of the integral evaluator with a sample file."""
    ev = IntegralEvaluator(integral_data)
    name = integral_data[0]

    assert ev.name == name
    assert ev.names == [name]
    assert ev.peaks == integral_data[2]
    assert ev.timestamp_dict == {name: integral_data[1]}
    np.testing.assert_array_equal(ev.integral_dict[name], integral_data[3])

    # ensure default mode is sum


def test_init_from_file(crd_int_delta, integral_data, tmpdir):
    """Assure importing from file works the same as providing data."""
    int_file = Path(tmpdir).joinpath("test.csv")
    data_io.integrals.export(crd_int_delta, int_file)

    ev_file = IntegralEvaluator(int_file)
    ev_data = IntegralEvaluator(integral_data)

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


# PROPERTIES #


def test_integrals(integral_data):
    """Return the summed integrals property for a simple case."""
    ev = IntegralEvaluator(integral_data)
    peaks, integrals = ev.integrals

    assert peaks == integral_data[2]
    np.testing.assert_array_equal(integrals, integral_data[3])


def test_integrals_multiple(integral_data):
    "Return the summed integrals for multiple samples."
    ev = IntegralEvaluator(integral_data)
    integral_data[0] = "second_file.crd"
    ev.add_integral(integral_data)
    peaks, integrals = ev.integrals

    integrals_expected = np.zeros_like(integral_data[3])
    for it in range(len(integrals_expected)):
        integrals_expected[it][0] = integral_data[3][it][0] * 2
        integrals_expected[it][1] = np.sqrt(integral_data[3][it][1] ** 2 * 2)

    assert peaks == integral_data[2]
    np.testing.assert_array_almost_equal(integrals, integrals_expected)


# METHODS #


def test_add_integral_overwrite(integral_data):
    """Add an integral to the evaluator and overwrite the existing one."""
    ev = IntegralEvaluator(integral_data)
    data = list(integral_data)
    data[3] = np.array([1, 2, 3])

    ev.add_integral(data, overwrite=True)

    assert ev.name == data[0]
    assert ev.names == [data[0]]
    assert ev.peaks == data[2]
    assert ev.timestamp_dict == {data[0]: data[1]}
    np.testing.assert_array_equal(ev.integral_dict[data[0]], data[3])


def test_add_integral_exists_no_overwrite(integral_data):
    """Raise error if integral already exists and overwrite is False."""
    ev = IntegralEvaluator(integral_data)

    with pytest.raises(KeyError):
        ev.add_integral(integral_data)


def test_add_integral_peaks_not_the_same(integral_data):
    """Raise error if peaks are not the same."""
    ev = IntegralEvaluator(integral_data)
    data = list(integral_data)
    data[2] = ["test"]

    with pytest.raises(ValueError):
        ev.add_integral(data, overwrite=True)


def test_add_integral_peaks_different_sorting(integral_data):
    """Raise error if peaks are not sorted the same."""
    ev = IntegralEvaluator(integral_data)
    integral_data[2] = integral_data[2][::-1]

    with pytest.raises(ValueError):
        ev.add_integral(integral_data, overwrite=True)
