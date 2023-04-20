"""Test for utilities delta module."""

import numpy as np
import pytest

import rimseval


def test_delta_calc():
    """Take an integrals like array and calculate delta values.

    Details of delta calculation is not tested.
    """
    names = ["Fe54", "Fe56", "244Pu", "bg"]
    integrals = np.array([[10000, 100], [100000, 240], [100, 10], [2001, 21]])
    deltas = rimseval.utilities.delta.delta_calc(names, integrals)
    assert np.isnan(deltas[2:3]).all()  # last two must be nans


def test_delta_calc_verbosity_warning():
    """Raise warning if VERBOSITY is >= 2 and division by zero occurs."""
    rimseval.VERBOSITY = 2
    names = ["Fe54", "Fe56"]
    integrals = np.array([[10000, 100], [0, 240]])
    with pytest.warns(RuntimeWarning):
        _ = rimseval.utilities.delta.delta_calc(names, integrals)
