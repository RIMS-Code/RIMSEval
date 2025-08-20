"""Tests for KORE lst to CRD transformation."""

import pytest

from rimseval.data_io import KORE2CRD

FNAME = "run001.lst"


def test_ini_file_parsing(kore_crd_path):
    """Parse the ini file and check all values are okay."""
    file_name = kore_crd_path.joinpath(FNAME)
    converter = KORE2CRD(file_name, write_crd=False)

    assert converter.acq_datetime == "2025:08:11 21:50:37"
    assert converter.bin_width_ps == 250
    assert converter.first_bin == 16000
    assert converter.last_bin == 400_000
    assert converter.num_shots == 614_400
    assert converter.num_scans == 1
    assert converter.shots_per_pixel == 150
    assert converter.shot_pattern == 32

    assert converter.num_pixels == 4096
    assert converter.xdim == 64
    assert converter.ydim == 64


def test_write_crd(kore_crd_path):
    """Write the CRD file from the `run001.lst` file."""
    file_name = kore_crd_path.joinpath(FNAME)
    _ = KORE2CRD(file_name)

    crd_file = file_name.with_suffix(".crd")
    assert crd_file.exists()


def test_empty_data_raises_error(kore_crd_path):
    """An empty data file should raise an error."""
    file_name = kore_crd_path.joinpath("empty.lst")
    with pytest.raises(IOError, match="The lst file is empty."):
        _ = KORE2CRD(file_name)
    assert not file_name.with_suffix(".crd").exists()
