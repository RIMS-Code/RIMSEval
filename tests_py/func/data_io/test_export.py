"""Tests for export routines."""

from pathlib import Path

import numpy as np

from rimseval.data_io import export
from rimseval.processor import CRDFileProcessor


def test_bin_array_avg():
    """Bin an array by averaging."""
    arr_in = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])

    bins = 2
    arr_exp = np.array([1.5, 3.5, 5.5, 7.5, 9.5])
    arr_rec = export._bin_array_avg(arr_in, bins)
    np.testing.assert_equal(arr_exp, arr_rec)

    bins = 3
    arr_exp = np.array([2, 5, 8])
    arr_rec = export._bin_array_avg(arr_in, bins)
    np.testing.assert_equal(arr_exp, arr_rec)


def test_bin_array_sum():
    """Bin an array by summing."""
    arr_in = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])

    bin = 2
    arr_exp = np.array([3, 7, 11, 15, 19])
    arr_rec = export._bin_array_sum(arr_in, bin)
    np.testing.assert_equal(arr_exp, arr_rec)

    bin = 3
    arr_exp = np.array([6, 15, 24])
    arr_rec = export._bin_array_sum(arr_in, bin)
    np.testing.assert_equal(arr_exp, arr_rec)


def test_tof_spectrum(tmpdir, crd_file):
    """Export time of flight spectrum."""
    _, _, _, fname = crd_file
    crd = CRDFileProcessor(Path(fname))
    crd.spectrum_full()

    file_out = Path(tmpdir.strpath).joinpath("tof")
    export.tof_spectrum(crd, file_out, bins=2)
    assert file_out.with_suffix(".csv").is_file()


def test_mass_spectrum(tmpdir, crd_file):
    """Export time of flight and mass spectrum."""
    _, _, _, fname = crd_file
    crd = CRDFileProcessor(Path(fname))
    crd.def_mcal = np.array([[1, 2], [10, 20]])
    crd.spectrum_full()
    crd.mass_calibration()

    file_out = Path(tmpdir.strpath).joinpath("mass")
    export.mass_spectrum(crd, file_out, bins=2)
    assert file_out.with_suffix(".csv").is_file()
