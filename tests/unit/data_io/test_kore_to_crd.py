"""Tests for KORE lst to CRD transformation."""

from rimseval.data_io import KORE2CRD

FNAME = "run001.lst"


def test_ini_file_parsing(kore_crd_path):
    """Parse the ini file and check all values are okay."""
    file_name = kore_crd_path.joinpath(FNAME)
    converter = KORE2CRD(file_name)

    assert converter.acq_datetime == "2025:08:11 21:50:37"
    assert converter.bin_width_ns == 0.25
    assert converter.first_bin == 16000
    assert converter.last_bin == 400_000
    assert converter.num_shots == 614_400
