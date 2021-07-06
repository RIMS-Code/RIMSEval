"""This file contains utilities for processing crd files."""

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
