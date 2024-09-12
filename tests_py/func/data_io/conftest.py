"""PyTest fixtures for func tests in data_io."""

from pathlib import Path

import numpy as np
import pytest

import rimseval


@pytest.fixture
def mpa4a_data_ascii():
    """Provide data for the MCS6 TDC, header states [MPA4A] format.

    Provide data in ASCII format, also provide the correct formatting and channel that
    contains data.

    :return: A tuple with channel, format, and data
    :rtype: (int, DataFormat, list)
    """
    channel = 4
    fmt = rimseval.lst_processor.LST2CRD.ASCIIFormat.ASCII_1A
    data = [
        "000200b95a54",
        "000300b95a54",
        "000400b95a64",
        "000500b95a64",
        "000600b95a54",
        "000700b95a64",
        "000800b95a54",
        "000900b95a64",
        "000a00b95a54",
    ]
    return channel, fmt, data


@pytest.fixture
def crdproc_int(crd_file) -> rimseval.processor.CRDFileProcessor:
    """Provide a dummy CRDProcessor file with integrals.

    :param crd_file: Fixture for crd file return.

    :return: Dummy CRDProcessor file with integrals.
    """
    _, _, _, fname = crd_file
    crd = rimseval.processor.CRDFileProcessor(Path(fname))
    crd.spectrum_full()
    crd.def_mcal = np.array([[1, 2], [10, 20]])
    crd.mass_calibration()
    crd.def_integrals = ["Int1", "Int2"], np.array([[1, 2], [3, 4]])
    crd.integrals = np.array([[103, 104], [203, 204]])

    return crd
