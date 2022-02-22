"""Tests for the plots utility functions that are in GUIs."""

import numpy as np

from rimseval.guis import plots


def test_create_histogram():
    """Create a histogram from a data array."""
    data = np.array([1, 2, 1, 1, 1, 2, 5, 4, 3, 4, 3, 1, 1, 0, 0, 0])
    xdata_exp = np.array([0, 1, 2, 3, 4, 5])
    hist_exp = np.array([3, 6, 2, 2, 2, 1])

    xdata_rec, hist_rec = plots._create_histogram(data)
    np.testing.assert_equal(xdata_exp, xdata_rec)
    np.testing.assert_equal(hist_exp, hist_rec)


def test_calculate_bin_differences():
    """Create a spacing vector with spaces in beetween ions."""
    all_tofs = np.arange(20)
    ion_ranges = np.array([[2, 5], [7, 10]])  # ranges with > 1 ion per shot
    spacing_exp = np.array([1, 2])
    frequency_exp = np.array([4, 2])

    spacing_rec, frequency_rec = plots._calculate_bin_differences(all_tofs, ion_ranges)
    np.testing.assert_equal(spacing_exp, spacing_rec)
    np.testing.assert_equal(frequency_exp, frequency_rec)
