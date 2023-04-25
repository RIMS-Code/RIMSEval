"""This file contains utilities that do not fit anywhere else."""

import iniabu
from numba import njit
import numpy as np

ini = iniabu.IniAbu(database="nist")  # select correct iniabu database for this program


def delta_label(iso1: str, iso2: str) -> str:
    """Return the delta-ratio label for a pair of isotopes.

    :param iso1: First isotope.
    :param iso2: Second isotope.

    :return: The delta label.
    """
    iso1 = ini.iso[iso1]
    iso2 = ini.iso[iso2]

    ele1 = iso1.name.split("-")[0]
    ele2 = iso2.name.split("-")[0]

    return f"δ({iso1.a}{ele1}/{iso2.a}{ele2})"


@njit
def not_index(ind: np.array, length: int) -> np.array:  # pragma: nocover
    """Reverse an index.

    After filtering ions, e.g., using `np.where`, and keeping the indices of an array,
    this routine creates the opposite, i.e., an array of the indices that have not been
    filtered.

    :param ind: Array of all the indexes.
    :param length: Length of the original index to take out of.

    :return: The reversed index.

    :raises ValueError: Max index is larger than the total length, which should not be.

    Example:
        >>> a = np.arange(7)
        >>> b = np.where(a < 4)[0]
        >>> b
        array([0, 1, 2, 3])
        >>> not_index(b)
        array([4, 5, 6])
    """
    if ind.shape == (0,):  # no indices filtered out
        return np.arange(length)
    else:
        if np.max(ind) >= length:
            raise ValueError("The maximum index must be smaller than the length.")

        not_arr = np.array([it for it in range(length) if it not in ind])
        return not_arr
