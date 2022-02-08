"""Test for Peirce criterion data rejection."""


import pytest
import numpy as np

from rimseval.utilities import peirce


def test_peirce_ross_2003_example():
    """Run example in Ross (2003) through Peirce criterion."""
    data = np.array([102.2, 90, 99, 102, 103, 100.2, 89, 98.1, 101.5, 102])
    outliers_exp = np.array([89, 90])
    outliers_ind = np.array([1, 6])  # index of outliers in original array
    avg_exp = 100.9
    std_exp = 1.66

    avg_rec, std_rec, outliers_rec, outliers_ind_rec = peirce.reject_outliers(data)

    assert avg_rec == pytest.approx(avg_exp, abs=0.1)
    assert std_rec == pytest.approx(std_exp, abs=0.1)
    np.testing.assert_equal(outliers_rec, outliers_exp)
    np.testing.assert_equal(outliers_ind_rec, outliers_ind)
