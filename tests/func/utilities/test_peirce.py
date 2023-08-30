"""Test for Peirce criterion data rejection."""


from hypothesis import given, strategies as st
import numpy as np
import pytest

from rimseval.utilities import peirce


def test_peirce_criterion_ldiv_zero():
    """Choose a minimum ldiv if it is zero (erfc turns 0 at large values)."""
    # define values such that it turns out to be zero
    n_tot = 100
    n = 1e3  # this brings `ldiv` numerically to zero
    m = 1

    _ = peirce.peirce_criterion(n_tot, n, m)


@given(n_hyp=st.integers(), m_hyp=st.integers())
def test_peirce_criterion_n_tot_zero(n_hyp, m_hyp):
    """Check that setting number of observations to zero returns zero always."""
    n_tot = 0
    expected = 0
    received = peirce.peirce_criterion(n_tot, n_hyp, m_hyp)
    assert expected == received


def test_peirce_criterion_x2_less_zero():
    """Ensure that in while-loop, x2 is set to zero if it is smaller than zero."""
    # define values that get x2 < 0
    n_tot = 2
    n = 1
    m = 5

    expected = 0
    received = peirce.peirce_criterion(n_tot, n, m)

    assert expected == received


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
