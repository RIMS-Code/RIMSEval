"""Fixtures and configuration for pytest."""

import pytest

import rimseval


# FIXTURES #


@pytest.fixture(scope="function")
def init_lst_proc():
    """Clean initialization of class and reset to defaults after usage."""
    # spin up class
    cls = rimseval.lst_processor.LST2CRD()

    yield cls

    # set defaults back that are specified in initialization
    cls._file_name = None
    cls._channel_data = None
    cls._channel_tag = None
    cls._data_format = cls.DataFormat.ASCII_1A

    # reset all other variables
    cls._file_info = {}  # dictionary with parsed header info
    cls._file_data = None  # file data
