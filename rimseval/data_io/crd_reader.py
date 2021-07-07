"""CRD reader to handle any kind of header and version (currently v1)."""

from datetime import datetime
from pathlib import Path
import struct
import warnings

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

        For this parsing to work, everything has to be just right, i.e., the number
        of shots have to be exactly defined and the data should have the right length.
        If not, this needs to throw a warning and move on to parse in a slower way.

        :param data: Binary string of all the data according to CRD specification.
        :type data: bytes

        :warning: Number of Shots do not agree with the number of shots in the list or
            certain ions are outside the binRange. Fallback to slower reading routine.
        :warning: There is more data in this file than indicated by the number of Shots.
        """
        n_shots = self.header["nofShots"]
        bin_start = self.header["binStart"]
        # fixme: There's going to be a problem here if bin_start is not zero or 1!
        n_bins = self.header["binEnd"] - self.header["binStart"]
        tof_data = np.zeros((n_shots, n_bins), dtype=np.int32)

        # loop through the data
        shot = 0
        curr_ind = 0
        warning_occured = False  # bool if we had a warning and need to take it slow
        while shot < n_shots:
            for it in range(struct.unpack("<I", data[curr_ind : curr_ind + 4])[0]):
                try:
                    curr_ind += 4
                    channel = struct.unpack("<I", data[curr_ind : curr_ind + 4])[0]
                    # fixme problem with start bin!
                    tof_data[shot][channel] += 1
                except IndexError as e:
                    print(f"nofShots: {n_shots}")
                    print(e)
                    warnings.warn(
                        "The CRD file is of bad form: Either there are ions "
                        "in it that are outside the specified bin range, or "
                        "there are fewer shots in it than expected. I will "
                        "now fall back to a slow reading method."
                    )
                    warning_occured = True
                    shot = n_shots  # to break out of while loop
                    break
            curr_ind += 4
            shot += 1

        if warning_occured:
            self.parse_data_fallback(data)
            return
        elif curr_ind != len(data):
            warnings.warn(
                "It seems like there is more data in this CRD file than "
                "the number of shots header entry show. I will now fall back "
                "to a slow reading method."
            )
            self.parse_data_fallback(data)
            return
        else:
            self._tof_data = tof_data

    def parse_data_fallback(self, data):
        """Slow reading routine in case the CRD file is corrupt.

        Here we don't assume anything and just try to read the data into lists and
        append them. Sure, this is going to be slow, but better than no data at all.
        """
        raise NotImplementedError

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
