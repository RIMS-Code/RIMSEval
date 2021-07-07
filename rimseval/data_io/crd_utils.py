"""This file contains utilities for processing crd files."""

from enum import Enum
import struct

import numpy as np

# current default CRD header information, packed and ready to be written
CURRENT_DEFAULTS = {
    "fileID": struct.pack("4s", bytes("CRD", "utf-8")),
    "minVer": struct.pack("<H", 0),
    "majVer": struct.pack("<H", 1),
    "sizeOfHeaders": struct.pack("<I", 88),
    "shotPattern": struct.pack("<I", 0),
    "tofFormat": struct.pack("<I", 1),
    "polarity": struct.pack("<I", 1),
    "xDim": struct.pack("<I", 0),
    "yDim": struct.pack("<I", 0),
    "shotsPerPixel": struct.pack("<I", 0),
    "pixelPerScan": struct.pack("<I", 0),
    "nOfScans": struct.pack("<I", 0),
    "deltaT": struct.pack("<d", 0),
    "eof": struct.pack("4s", bytes("OK!", "utf-8")),
}

HEADER_START = (
    ("fileID", 4, "4s"),
    ("startDateTime", 20, "20s"),
    ("minVer", 2, "<H"),
    ("majVer", 2, "<H"),
    ("sizeOfHeaders", 4, "<I"),
)


class CRDHeader(Enum):
    """Enum class for CRD header.

    The start must always be the same as HEADER_START above, however, the other fields
    might vary depending on the header that is being used. The header is called by its
    version number. Note that the letter `v` precedes the number and that the period
    is replaced with the letter `p`.

    Format is always: Name, length, struct unpack qualifier
    """

    v1p0 = (
        ("shotPattern", 4, "<I"),
        ("tofFormat", 4, "<I"),
        ("polarity", 4, "<I"),
        ("binLength", 4, "<I"),
        ("binStart", 4, "<I"),
        ("binEnd", 4, "<I"),
        ("xDim", 4, "<I"),
        ("yDim", 4, "<I"),
        ("shotsPerPixel", 4, "<I"),
        ("pixelPerScan", 4, "<I"),
        ("nofScans", 4, "<I"),
        ("nofShots", 4, "<I"),
        ("deltaT", 8, "<d"),
    )
