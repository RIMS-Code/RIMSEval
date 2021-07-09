"""Utilities for CRD processors. Mostly methods that can be jitted."""

from numba import njit
import numpy as np


@njit
def sort_data_into_spectrum(ions: np.ndarray) -> np.ndarray:
    """Sort ion data in 1D array into an overall array and sum them up.

    :param ions: Arrival time of the ions - number of time bin

    :return: arrival bins summed up
    """
    bin_start = ions.min()
    bin_end = ions.max()
    data = np.zeros(bin_end - bin_start + 1)
    for ion in ions:
        data[ion - bin_end] += 1
    return data
