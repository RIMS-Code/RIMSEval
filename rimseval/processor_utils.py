"""Utilities for CRD processors. Mostly methods that can be jitted."""

from typing import List, Tuple, Union

from numba import njit
import numpy as np


def calculate_mass_square(
    tm: Union[np.ndarray, float], tm0: float, const: float
) -> Union[np.ndarray, float]:
    """Functional prescription for mass calibration.

    Returns the mass with the defined functional description for a mass calibration.
    Two parameters are required. The equation, with parameters defined as below,
     is as following:

    ..math::
        m = \left( \frac{tm - tm0}{const} \right)^{2}

    :param tm: time or channel
    :param tm0: parameter 1
    :param const: parameter 2

    :return: mass m
    """
    return ((tm - tm0) / const) ** 2


@njit
def create_packages(
    shots: int,
    tofs_mapper: np.ndarray,
    all_tofs: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray]:
    """Create packages from data.

    :params shots: Number of shots per package
    :params tofs_mapper: mapper for ions_per_shot to tofs
    :params all_tofs: all arrival times / bins of ions

    :return: Data array where each row is a full spectrum, each line a package and a
        shot array on how many shots are there per pkg
    """
    bin_start = all_tofs.min()
    bin_end = all_tofs.max()

    nof_pkgs = len(tofs_mapper) // shots
    nof_shots_last_pkg = len(tofs_mapper) % shots
    if nof_shots_last_pkg > 0:
        nof_pkgs += 1

    # number of shots per package
    nof_shots_pkg = np.zeros(nof_pkgs) + shots
    if nof_shots_last_pkg != 0:
        nof_shots_pkg[-1] = nof_shots_last_pkg

    pkg_data = np.zeros((nof_pkgs, bin_end - bin_start + 1))
    for it, tof_map in enumerate(tofs_mapper):
        pkg_it = it // shots
        ions = all_tofs[tof_map[0] : tof_map[1]]
        for ion in ions:
            pkg_data[pkg_it][ion - bin_start] += 1

    return pkg_data, nof_shots_pkg


@njit
def dead_time_correction(
    data: np.ndarray, nof_shots: np.ndarray, dbins: int
) -> np.ndarray:
    """Calculate dead time for a given spectrum.

    :param data: Data array, histogram in bins. 2D array (even for 1D data!)
    :param nof_shots: Number of shots, 1D array of data
    :param dbins: Number of dead bins after original bin (total - 1).
    """
    dbins += 1  # to get total bins

    for lit in range(len(data)):
        ndash = np.zeros(len(data[lit]))  # initialize array to correct with later
        for it in range(len(ndash)):
            # create how far the sum should go
            if it < dbins:
                k = it
            else:
                k = dbins - 1
            # now calculate the sum
            sum_tmp = 0
            for jt in range(k):
                sum_tmp += data[lit][it - (jt + 1)]
            # calculate and add ndash
            ndash[it] = nof_shots[lit] - sum_tmp
        # correct the data
        for it in range(len(data[lit])):
            data[lit][it] = -nof_shots[lit] * np.log(1 - data[lit][it] / ndash[it])

    return data


@njit
def integrals_summing(
    data: np.ndarray, windows: Tuple[np.ndarray], data_pkg: np.ndarray = None
) -> Tuple[np.ndarray, np.ndarray]:
    """Sum up the integrals within the defined windows and return them.

    :param data: Data to be summed over.
    :param windows: The windows to be investigated (using numpy views)
    :param data_pkg: Package data (optional), if present.

    :return: integrals for data, integrals for data_pkg
    """
    integrals = np.zeros((len(windows), 2))

    # packages
    integrals_pkg = None
    if data_pkg is not None:
        integrals_pkg = np.zeros((data_pkg.shape[0], len(windows), 2))
        for ht, data_one in enumerate(data_pkg):
            for it, window in enumerate(windows):
                integrals_pkg[ht][it][0] = data_pkg[ht][window].sum()
                integrals_pkg[ht][it][1] = np.sqrt(integrals_pkg[ht][it][0])
        # define all integrals as the sum of the packages -> allow for filtering
        integrals[:, 0] = integrals_pkg.sum(axis=0)[:, 0]
        integrals[:, 1] = np.sqrt(np.sum(integrals_pkg[:, :, 1] ** 2, axis=0))
    else:
        for it, window in enumerate(windows):
            integrals[it][0] = data[window].sum()
            integrals[it][1] = np.sqrt(integrals[it][0])

    return integrals, integrals_pkg


def multi_range_indexes(rng: np.array) -> np.array:
    """Create multi range indexes.

    If a range is given as (from, to), the from will be included, while the to will
    be excluded.

    :param rng: Range, given as a numpy array of two entries each.

    :return: A 1D array with all the indexes spelled out. This allows for viewing
        numpy arrays for multiple windows.
    """
    num_shots = 0
    ind_tmp = []
    for rit in rng:
        if rit[0] != rit[1]:
            arranged_tmp = np.arange(rit[0], rit[1])
            ind_tmp.append(arranged_tmp)
            num_shots += len(arranged_tmp)

    indexes = np.zeros(num_shots, dtype=int)
    ind_b = 0
    for rit in ind_tmp:
        ind_e = ind_b + len(rit)
        indexes[ind_b:ind_e] = rit
        ind_b = ind_e
    return indexes


@njit
def sort_data_into_spectrum(
    ions: np.ndarray, bin_start: int, bin_end: int
) -> np.ndarray:
    """Sort ion data in 1D array into an overall array and sum them up.

    :param ions: Arrival time of the ions - number of time bin
    :param bin_start: First bin of spectrum
    :param bin_end: Last bin of spectrum

    :return: arrival bins summed up
    """
    data = np.zeros(bin_end - bin_start + 1)
    for ion in ions:
        data[ion - bin_start] += 1
    return data
