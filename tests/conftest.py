"""Fixtures and configuration for pytest."""

from pathlib import Path
import struct

from typing import Tuple
import pytest
import numpy as np

import rimseval


# FIXTURES #


@pytest.fixture(scope="function")
def crd_file(tmpdir) -> Tuple[dict, np.ndarray, np.ndarray, Path]:
    """Create and write a CRD file to a temporary folder, then return it.

    :return: Header as dictionary, ions_per_shot, arrival_bins, Path to file
    """
    binLength = 100
    ions_per_shot = np.array([1, 0, 4, 1, 2])
    all_tofs = np.array([231, 471, 182, 221, 959, 448, 281, 221])
    # set header values for the file
    header = {
        "fileID": b"CRD\0",
        "startDateTime": b"2021:07:10 11:41:13\0",
        "minVer": 0,
        "majVer": 1,
        "sizeOfHeaders": 88,
        "shotPattern": 1,
        "tofFormat": 1,
        "polarity": 1,
        "binLength": binLength,
        "binStart": all_tofs.min(),
        "binEnd": all_tofs.max(),
        "xDim": 0,
        "yDim": 0,
        "shotsPerPixel": 0,
        "pixelPerScan": 0,
        "nofScans": 0,
        "nofShots": ions_per_shot.shape[0],
        "deltaT": 0.0,
    }
    # data format for packing
    fmt_hdr = (
        ("fileID", "4s"),
        ("startDateTime", "20s"),
        ("minVer", "<H"),
        ("majVer", "<H"),
        ("sizeOfHeaders", "<I"),
        ("shotPattern", "<I"),
        ("tofFormat", "<I"),
        ("polarity", "<I"),
        ("binLength", "<I"),
        ("binStart", "<I"),
        ("binEnd", "<I"),
        ("xDim", "<I"),
        ("yDim", "<I"),
        ("shotsPerPixel", "<I"),
        ("pixelPerScan", "<I"),
        ("nofScans", "<I"),
        ("nofShots", "<I"),
        ("deltaT", "<d"),
    )
    # create crd content
    crd_cont = b""
    for hdr_name, fmt in fmt_hdr:  # write header
        crd_cont += struct.pack(fmt, header[hdr_name])
    bin_index = 0
    for ion in ions_per_shot:  # write data
        crd_cont += struct.pack("<I", ion)
        for it in range(ion):
            crd_cont += struct.pack("<I", all_tofs[bin_index])
            bin_index += 1
    crd_cont += struct.pack("4s", b"OK!\0")
    # write the CRD file
    fname = tmpdir.join("testfile.crd")
    fname.write_binary(crd_cont)
    return header, ions_per_shot, all_tofs, fname


@pytest.fixture(scope="function")
def crd_proc_mock(mocker):
    """Create a mocker instance for the CRDFileProcessor class and return it."""
    crd_mock = mocker.MagicMock()
    crd_mock.__class__ = rimseval.processor.CRDFileProcessor
    return crd_mock


@pytest.fixture(scope="function")
def init_lst_proc():
    """Clean initialization of class and reset to defaults after usage."""
    # spin up class
    cls = rimseval.data_io.LST2CRD()

    yield cls

    # set defaults back that are specified in initialization
    cls._file_name = None
    cls._channel_data = None
    cls._channel_tag = None

    # reset all other variables
    cls._file_info = {}  # dictionary with parsed header info
    cls._data_format = None
    cls._data_signal = None  # main signal data
    cls._data_tag = None  # tag data
