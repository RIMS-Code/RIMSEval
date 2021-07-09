"""Utilities for CRD processors. Mostly methods that can be jitted."""

from numba import njit
import numpy as np


@njit
def dead_time_correction(data: np.ndarray, nof_shots: int, dbins: int) -> np.ndarray:
    """Calculate dead time for a given spectrum.

    :param data: Data array, histogram in bins.
    :param nof_shots: Number of shots
    :param dbins: Number of dead bins after original bin (total - 1).
    """
    dbins += 1  # to get total bins
    ndash = np.zeros(len(data))  # initialize array to correct with later
    for it in range(len(ndash)):
        # create how far the sum should go
        if it < dbins:
            k = it
        else:
            k = dbins - 1
        # now calculate the sum
        sum_tmp = 0
        for jt in range(k):
            sum_tmp += data[it - (jt + 1)]
        # calculate and add ndash
        ndash[it] = nof_shots - sum_tmp
    # correct the data
    for it in range(len(data)):
        data[it] = -nof_shots * np.log(1 - data[it] / ndash[it])
    return data


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
