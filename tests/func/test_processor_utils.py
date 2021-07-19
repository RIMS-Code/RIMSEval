"""Tests for processors utilities."""

import numpy as np

import rimseval.processor_utils as pu


def test_multi_range_indexes():
    """Create multi-range indexes for view on data."""
    ranges = np.array([[0, 2], [3, 6], [0, 0], [15, 22]])
    indexes_exp = np.array(
        [0, 1, 2, 3, 4, 5, 6, 15, 16, 17, 18, 19, 20, 21, 22], dtype=int
    )

    indexes_rec = pu.multi_range_indexes(ranges)
    np.testing.assert_equal(indexes_rec, indexes_exp)
    assert indexes_rec.dtype == int


def test_multi_range_indexes_empty():
    """Return empty index array if all ranges of zero length."""
    ranges = np.array([[0, 0], [0, 0]])
    indexes_exp = np.array([])
    np.testing.assert_equal(pu.multi_range_indexes(ranges), indexes_exp)
