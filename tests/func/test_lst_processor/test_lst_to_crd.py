"""Tests for `lst_to_crd.py`"""

from hypothesis import given, strategies as st
import numpy as np
from pathlib import Path
import pytest

import rimseval


# PROPERTIES #


def test_channel_data(init_lst_proc):
    """Get / set the number of the channel the data is in."""
    channel_number = 42
    init_lst_proc.channel_data = channel_number
    assert init_lst_proc.channel_data == channel_number


def test_channel_data_wrong_type(init_lst_proc):
    """Raise a type error when a wrong type is set for the channel number."""
    wrong_type = "42"
    with pytest.raises(TypeError) as exc_info:
        init_lst_proc.channel_data = wrong_type
    exc_msg = exc_info.value.args[0]
    assert exc_msg == "Channel number must be given as an integer."


def test_channel_tag(init_lst_proc):
    """Get / set the number of the channel the tag is in."""
    channel_number = 42
    init_lst_proc.channel_tag = channel_number
    assert init_lst_proc.channel_tag == channel_number


def test_channel_tag_wrong_type(init_lst_proc):
    """Raise a type error when a wrong type is set for the channel number."""
    wrong_type = "42"
    with pytest.raises(TypeError) as exc_info:
        init_lst_proc.channel_tag = wrong_type
    exc_msg = exc_info.value.args[0]
    assert exc_msg == "Channel number must be given as an integer."


@pytest.mark.parametrize("data_format", rimseval.data_io.LST2CRD.DataFormat)
def test_data_format(data_format):
    """Get / Set the data format."""
    cls = rimseval.data_io.LST2CRD()
    cls.data_format = data_format
    assert cls.data_format == data_format


def test_data_format_type_error(init_lst_proc):
    """Raise a TypeError when data format is not the correct object."""
    wrong_data_format = "ASCII_6B"
    with pytest.raises(TypeError):
        init_lst_proc.data_format = wrong_data_format


def test_file_name(init_lst_proc):
    """Get / set a filename and path."""
    test_path = Path("./test.txt")
    init_lst_proc.file_name = test_path
    assert init_lst_proc.file_name == test_path


def test_file_name_wrong_type(init_lst_proc):
    """Raise a TypeError when wrong file tpe was given."""
    wrong_type = 42
    with pytest.raises(TypeError) as exc_info:
        init_lst_proc.file_name = wrong_type
    exc_msg = exc_info.value.args[0]
    assert (
        exc_msg == f"Path must be a `pathlib.Path` object but is a {type(wrong_type)}."
    )


# METHODS #


def test_write_crd_no_data(init_lst_proc):
    """Raise ValueError if data has not been read yet."""
    with pytest.raises(ValueError) as err_info:
        init_lst_proc.write_crd()
    err_msg = err_info.value.args[0]
    assert err_msg == "No data has been read in yet."
