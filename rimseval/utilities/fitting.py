"""Functions for fitting using scipy optimize."""

from typing import Union

import numpy as np


def gaussian(
    xdat: Union[float, np.ndarray], coeffs: np.ndarray
) -> Union[float, np.ndarray]:
    """Return the value of a Gaussian for given parameters.

    :param xdat: X value
    :param coeffs: Coefficients, [mu, sigma, height]
    """
    return coeffs[2] * np.exp(-(((xdat - coeffs[0]) / coeffs[1]) ** 2))


def residuals_gaussian(
    coeffs: np.ndarray, ydat: np.ndarray, xdat: np.ndarray
) -> np.ndarray:
    """Calculate residuals and return them.

    :param coeffs: Coefficients for model
    :param ydat: Y data to compare with
    :param xdat: X data for model fit
    """
    return ydat - gaussian(xdat, coeffs)
