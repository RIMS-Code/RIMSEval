"""Test for fitting utilities."""

from hypothesis import given, strategies as st
import numpy as np

from rimseval.utilities import fitting

# Hypothesis variables
my_float = st.floats(allow_nan=False)
my_tuple = st.tuples(my_float, my_float)


@given(xdat=st.lists(my_float), coeffs=st.tuples(my_float, my_float, my_float))
def test_gaussian(xdat, coeffs):
    """Return a Gaussian for given coefficients."""
    xdat = np.array(xdat)
    coeffs = np.array(coeffs)
    exp_value = coeffs[2] * np.exp(-(((xdat - coeffs[0]) / coeffs[1]) ** 2))
    np.testing.assert_equal(fitting.gaussian(xdat, coeffs), exp_value)


@given(
    xydat=st.lists(my_tuple, min_size=1),
    coeffs=st.tuples(my_float, my_float, my_float),
)
def test_residual_gaussian(xydat, coeffs):
    """Return a Gaussian for given coefficients."""
    xydat = np.array(xydat)
    xdat = xydat[:, 0]
    ydat = xydat[:, 1]

    coeffs = np.array(coeffs)

    exp_value = ydat - fitting.gaussian(xdat, coeffs)
    np.testing.assert_equal(fitting.residuals_gaussian(coeffs, ydat, xdat), exp_value)
