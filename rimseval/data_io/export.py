"""Export data to files."""

from pathlib import Path

from numba import njit
import numpy as np

from rimseval.processor import CRDFileProcessor


@njit
def bin_array_avg(arr: np.ndarray, bins: int) -> np.ndarray:  # pragma: nocover
    """Takes a numpy array and bins it by averaging the range.

    End of the array, if it doesn't fit, will be thrown away.

    :param arr: Array of data.
    :param bins: Number of entries to bin.

    :return: Binned array.
    """
    ret_array = np.zeros(len(arr) // bins)
    for it in range(len(ret_array)):
        ret_array[it] = np.average(arr[it * bins : it * bins + bins])
    return ret_array


@njit
def bin_array_sum(arr: np.ndarray, bin: int) -> np.ndarray:  # pragma: nocover
    """Takes a numpy array and bins it by summing the range.

    End of the array, if it doesn't fit, will be thrown away.

    :param arr: Array of data.
    :param bin: Number of entries to bin.

    :return: Binned array.
    """
    ret_array = np.zeros(len(arr) // bin)
    for it in range(len(ret_array)):
        ret_array[it] = np.sum(arr[it * bin : it * bin + bin])
    return ret_array


def tof_spectrum(crd: CRDFileProcessor, fname: Path, bins: int = 1) -> None:
    """Export time of flight spectra to csv file.

    :param crd: CRD file.
    :param fname: File name to export to.
    :param bins: How many data to bin.
    """
    tof_binned = bin_array_avg(crd.tof, bins)
    data_binned = bin_array_sum(crd.data, bins)

    header = "Time of Flight (us),Counts"
    data_to_write = np.stack([tof_binned, data_binned], axis=1)

    fname = fname.with_suffix(".csv").absolute()

    np.savetxt(fname, data_to_write, delimiter=",", header=header)


def mass_spectrum(crd: CRDFileProcessor, fname: Path, bins: int = 1) -> None:
    """Export time of flight and mass spectra to csv file.

    :param crd: CRD file.
    :param fname: File name to export to.
    :param bins: How many data to bin.
    """
    tof_binned = bin_array_avg(crd.tof, bins)
    mass_binned = bin_array_avg(crd.mass, bins)
    data_binned = bin_array_sum(crd.data, bins)

    header = "Mass (amu),Time of Flight (us),Counts"
    data_to_write = np.stack([mass_binned, tof_binned, data_binned], axis=1)

    fname = fname.with_suffix(".csv").absolute()

    np.savetxt(fname, data_to_write, delimiter=",", header=header)
