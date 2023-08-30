"""Unit tests for the CRD reader, making use of the `crd_file` fixture."""

from pathlib import Path

import numpy as np
import pytest

from rimseval.data_io.crd_reader import CRDReader
from ...utils import assert_crd_equal


# TEST PROPERTIES #


def test_crd_reader_wrong_filetype():
    """Raise TypeError if file is not given as Path instance."""
    fname = "some_file.crd"
    with pytest.raises(TypeError) as err:
        CRDReader(fname)
    err_msg = err.value.args[0]
    assert err_msg == "Filename must be given as a valid Path using pathlib."


def test_crd_reader_header(crd_file):
    """Assert that the header of a crd file is read correctly."""
    hdr, _, _, fname = crd_file
    crd = CRDReader(Path(fname))
    assert crd.header == hdr


def test_crd_reader_all_data(crd_file):
    """Return all the data from the CRD file."""
    _, ions_per_shot, all_tofs, fname = crd_file
    crd = CRDReader(Path(fname))
    ret_ions_per_shot, ret_arrival_bins = crd.all_data
    np.testing.assert_equal(ions_per_shot, ret_ions_per_shot)
    np.testing.assert_equal(all_tofs, ret_arrival_bins)


def test_crd_all_tofs(crd_file):
    """Return all tof arrival bins."""
    _, _, all_tofs, fname = crd_file
    crd = CRDReader(Path(fname))
    np.testing.assert_equal(crd.all_tofs, all_tofs)


def test_crd_ions_per_shot(crd_file):
    """Return ions per shot array."""
    _, ions_per_shot, _, fname = crd_file
    crd = CRDReader(Path(fname))
    np.testing.assert_equal(crd.ions_per_shot, ions_per_shot)


def test_crd_nof_ions(crd_file):
    """Return number of ions."""
    _, ions_per_shot, _, fname = crd_file
    crd = CRDReader(Path(fname))
    assert crd.nof_ions == ions_per_shot.sum()


def test_crd_nof_shots(crd_file):
    """Return number of shots."""
    hdr, _, _, fname = crd_file
    crd = CRDReader(Path(fname))
    assert crd.nof_shots == hdr["nofShots"]


# ERROR CHECKING #


def test_invalid_data_length(crd_data):
    """Raise an OSError if an incorrect data length was encountered."""
    crd_file = crd_data.joinpath("err_invalid_data_length.crd")
    with pytest.raises(OSError) as err:
        _ = CRDReader(crd_file)

    msg = err.value.args[0]
    assert "Data length does not agree" in msg


def test_invalid_header(crd_data):
    """Raise a KeyError if an incorrect header was encountered."""
    hdr_version = "v0p1"
    crd_file = crd_data.joinpath("err_invalid_header.crd")
    with pytest.raises(KeyError) as err:
        _ = CRDReader(crd_file)

    msg = err.value.args[0]
    assert hdr_version in msg


def test_inavlid_num_of_ions_less(crd_data):
    """Parse the file properly, even if less ions in file than expected."""
    crd_file = crd_data.joinpath("err_less_ions_than_hdr.crd")

    with pytest.warns(UserWarning, match="I will try a slow reading routine now"):
        _ = CRDReader(crd_file)


def test_inavlid_num_of_ions_more(crd_data):
    """Parse the file properly, even if more ions in file than expected."""
    crd_file = crd_data.joinpath("err_less_ions_than_hdr.crd")

    with pytest.warns(UserWarning, match="I will try a slow reading routine now"):
        _ = CRDReader(crd_file)


def test_no_eof(crd_data, crd_file):
    """Parse file even without an EoF."""
    _, _, _, fname = crd_file
    crd_correct = CRDReader(Path(fname))
    crd_faulty = CRDReader(Path(crd_data.joinpath("err_no_eof.crd")))

    assert_crd_equal(crd_correct, crd_faulty)
