"""Tests for KORE lst to CRD transformation."""

import pytest

from rimseval.data_io import KORE2CRD

FNAME = "run001.lst"


def test_ini_file_parsing(kore_crd_path):
    """Parse the ini file and check all values are okay."""
    file_name = kore_crd_path.joinpath(FNAME)
    converter = KORE2CRD(file_name)

    assert converter.acq_datetime == "2025:05:15 15:03:16"
    assert converter.bin_width_ps == 250
    assert converter.first_bin == 16000
    assert converter.last_bin == 360_000
    assert converter.num_shots == 1_310_720
    assert converter.num_scans == 1
    assert converter.shots_per_pixel == 5
    assert converter.shot_pattern == 32

    assert converter.num_pixels == 262_144
    assert converter.xdim == 512
    assert converter.ydim == 512


def test_write_crd(kore_crd_path):
    """Write the CRD file from the `run001.lst` file."""
    file_name = kore_crd_path.joinpath(FNAME)
    kore = KORE2CRD(file_name)
    kore.write_crd()

    crd_file = file_name.with_suffix(".crd")

    # compare crd files byte by byte with expexted
    crd_content = crd_file.read_bytes()
    crd_fname_exp = kore_crd_path.joinpath("run001_exp.crd")
    crd_exp = crd_fname_exp.read_bytes()
    assert crd_content == crd_exp


def test_empty_data_raises_error(kore_crd_path):
    """An empty data file should raise an error."""
    file_name = kore_crd_path.joinpath("faulty_files/empty.lst")
    with pytest.raises(IOError, match="The lst file is empty."):
        kore = KORE2CRD(file_name)
        kore.write_crd()
    assert not file_name.with_suffix(".crd").exists()


def test_file_not_found_only_lst(kore_crd_path):
    """A file not found error should be raised if only the .lst file is present."""
    file_name = kore_crd_path.joinpath("faulty_files/only_lst.lst")
    file_name_ini = file_name.with_suffix(".ini")
    with pytest.raises(FileNotFoundError, match=f"{file_name_ini} does not exist."):
        KORE2CRD(file_name)


def test_file_not_found_only_ini(kore_crd_path):
    """A file not found error should be raised if only the .ini file is present."""
    file_name = kore_crd_path.joinpath("faulty_files/only_ini.ini")
    file_name_lst = file_name.with_suffix(".lst")
    with pytest.raises(FileNotFoundError, match=f"{file_name_lst} does not exist."):
        KORE2CRD(file_name)


def test_unsupported_experiment_type(kore_crd_path):
    """An unsupported experiment type should raise a ValueError."""
    file_name = kore_crd_path.joinpath("faulty_files/unsupported_exp_type.ini")
    with pytest.raises(ValueError, match="Unsupported experiment type:"):
        KORE2CRD(file_name)


@pytest.mark.parametrize(
    "file_name",
    [
        "exp_type_not_found.ini",
        "acq_time_not_found.ini",
        "bin_width_not_found.ini",
        "first_bin_not_found.ini",
        "last_bin_not_found.ini",
        "num_scans_not_found.ini",
        "num_shots_not_found.ini",
        "shots_per_px_not_found.ini",
    ],
)
def test_missing_parameters_ini_file(kore_crd_path, file_name):
    """Test that missing parameters in the ini file raise a ValueError."""
    file_name = kore_crd_path.joinpath(f"faulty_files/{file_name}")
    with pytest.raises(ValueError, match="not found in the INI file."):
        KORE2CRD(file_name)


def test_first_three_lst_bytes_bad(kore_crd_path):
    """Test that a .lst file with bad first three bytes raises a ValueError."""
    file_name = kore_crd_path.joinpath("faulty_files/first_three_lst_bytes_bad.lst")
    kore = KORE2CRD(file_name)
    with pytest.raises(ValueError, match="The first three bytes are not a start."):
        kore.write_crd()


def test_warning_bad_number_shots(kore_crd_path):
    """Test that a warning is raised for a bad number of shots."""
    file_name = kore_crd_path.joinpath("faulty_files/bad_number_shots.ini")
    kore = KORE2CRD(file_name)
    with pytest.warns(
        UserWarning,
        match=r"Number of shots in the LST file \(3\) does not match the number in the INI file \(1310720\).",
    ):
        _ = kore.write_crd()
    crd_file = file_name.with_suffix(".crd")
    assert crd_file.exists()
