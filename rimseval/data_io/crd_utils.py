"""This file contains utilities for processing crd files."""

from enum import Enum
import struct

from numba import njit
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


@njit
def shot_to_tof_mapper(ions_per_shot: np.array) -> np.array:  # pragma: nocover
    """Mapper for ions_to_shot to all_tofs.

    Takes ions_per_shot array and creates a mapper that describes which ranges in the
    all_tofs array a given shot refers to.

    :param ions_per_shot: Ion per shots array.
    """
    mapper = np.zeros((ions_per_shot.shape[0], 2), dtype=np.int32)
    curr_ind = 0
    for it, ion_per_shot in enumerate(ions_per_shot):
        mapper[it][0] = curr_ind
        mapper[it][1] = curr_ind + ion_per_shot
        curr_ind += ion_per_shot
    return mapper
