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
    assert ev.timestamps == {name: integral_data[1]}
    np.testing.assert_array_equal(ev.integrals[name], integral_data[3])

    # ensure default mode is sum
    assert ev.mode == IntegralEvaluator.Mode.SUM


def test_init_from_file(crd_int_delta, integral_data, tmpdir):
    """Assure importing from file works the same as providing data."""
    int_file = Path(tmpdir).joinpath("test.csv")
    data_io.integrals.export(crd_int_delta, int_file)

    ev_file = IntegralEvaluator(int_file)
    ev_data = IntegralEvaluator(integral_data)

    assert ev_file.name == ev_data.name
    assert ev_file.names == ev_data.names
    assert ev_file.peaks == ev_data.peaks
    assert ev_file.timestamps == ev_data.timestamps
    np.testing.assert_array_equal(
        ev_file.integrals[ev_file.name], ev_data.integrals[ev_data.name]
    )
    assert ev_file.mode == ev_data.mode


def test_init_empty():
    """Test the initialization of the integral evaluator without data."""
    ev = IntegralEvaluator()

    assert ev.name is None
    assert ev.names == []
    assert ev.peaks is None
    assert ev.timestamps == {}
    assert ev.integrals == {}
    assert ev.mode == IntegralEvaluator.Mode.SUM


# PROPERTIES not tested in inits #


@pytest.mark.parametrize("mode", IntegralEvaluator.Mode)
def test_mode(mode):
    """Get / set mode."""
    ev = IntegralEvaluator()
    ev.mode = mode

    assert ev.mode == mode


def test_mode_type_error():
    """Set mode with wrong type."""
    ev = IntegralEvaluator()

    with pytest.raises(TypeError):
        ev.mode = "test"
