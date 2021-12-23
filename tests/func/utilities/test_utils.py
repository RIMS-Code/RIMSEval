"""Test for Peirce criterion data rejection."""


import pytest
import numpy as np

from rimseval.utilities import utils


def test_not_index():
    """Return all indices not of length that are not in a given array."""
    # docstring example
    a = np.arange(7)
    b = np.where(a < 4)[0]
    expected = np.array([4, 5, 6])
    np.testing.assert_equal(expected, utils.not_index(b, len(a)))

    # filter a bit further
    b = np.where(np.logical_or(a < 4, a > 5))[0]
    expected = np.array([4, 5])
    np.testing.assert_equal(expected, utils.not_index(b, len(a)))

    # only one entry left
    b = np.where(a < 1)[0]
    expected = np.array([1, 2, 3, 4, 5, 6])
    np.testing.assert_equal(expected, utils.not_index(b, len(a)))


def test_not_index_empty_ind():
    """Return all indices if `ind` is empty."""
    a = np.arange(7)
    b = np.where(a < 0)[0]
    expected = np.arange(len(a))
    np.testing.assert_equal(expected, utils.not_index(b, len(a)))


def test_not_index_value_error():
    """Raise a value error if max index is larger than length."""
    ind = np.arange(10)
    with pytest.raises(ValueError):
        utils.not_index(ind, 5)
