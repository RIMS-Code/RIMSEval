"""PyTest fixtures for func tests in data_io."""

import pytest

import rimseval


@pytest.fixture
def mpa4a_data_ascii():
    """Provides data for the MCS6 TDC, header states [MPA4A] format.

    Provide data in ASCII format, also provide the correct formatting and channel that contains data.

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
