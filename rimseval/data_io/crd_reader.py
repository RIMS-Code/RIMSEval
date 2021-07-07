"""CRD reader to handle any kind of header and version (currently v1)."""

from datetime import datetime
from pathlib import Path
import struct

import numpy as np
import pathlib

from . import crd_utils


class CRDReader:
    """Read CRD Files and make the data available.

    ToDo: Example
    """

    def __init__(self, fname):
        """Read in a CRD file and make all header arguments available.

        :param fname: Filename
        :type fname: Path

        :raises TypeError: Fname must be a valid path.
        """
        if not isinstance(fname, Path):
            raise TypeError("Filename must be given as a valid Path using pathlib.")
        self.fname = fname

        # header dictionary
        self.header = {}

        # data
        self._tof_data = None

        # init end of file
        self.eof = False

        # now read the stuff
        self.read_data()

    @property
    def tof_data(self):
        """Get the time of flight data."""
        return self._tof_data

    # FUNCTIONS #

    def parse_data(self, data):
        """Parse the actual data out and put into the appropriate array.

        :param data: Binary string of all the data according to CRD specification.
        :type data: bytes
        """
        # todo continue here
        pass

    def read_data(self):
        """Read in the data and parse out the header.

        The header information will be stored in the header dictionary. All entry
        names are as specified in the CRD format file for version 1.0.

        :raises KeyError: Header is not available.
        :raises IOError: Corrupt data length.
        """
        with open(self.fname, "rb") as f_in:
            # read start of the header
            for (name, size, fmt) in crd_utils.HEADER_START:
                self.header[name] = struct.unpack(fmt, f_in.read(size))[0]

            # get the rest of the header
            crd_version = f"v{self.header['majVer']}p{self.header['minVer']}"
            try:
                hdr_description = crd_utils.CRDHeader[crd_version].value
            except KeyError:
                raise KeyError(
                    f"The header version of this CRD file is {crd_version}, "
                    f"which is not available."
                )

            for (name, size, fmt) in hdr_description:
                self.header[name] = struct.unpack(fmt, f_in.read(size))[0]

            # now read in the rest of the file
            rest = f_in.read()

        if len(rest) % 4 != 0:
            raise IOError(
                "Data length does not agree with CRD format and seems to be corrupt."
            )

        # check for eof
        if struct.unpack("4s", rest[-4:])[0][:-1] == b"OK!":
            self.eof = True

        # prepare the data
        if self.eof:
            self.parse_data(rest[:-4])
        else:
            self.parse_data(rest)
