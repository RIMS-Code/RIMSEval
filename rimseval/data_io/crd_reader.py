"""CRD reader to handle any kind of header and version (currently v1)."""

from pathlib import Path
import struct
from typing import Tuple
import warnings

import numpy as np

from . import crd_utils


class CRDReader:
    """Read CRD Files and make the data available.

    ToDo: Example
    """

    def __init__(self, fname: Path) -> None:
        """Read in a CRD file and make all header arguments available.

        :param fname: Filename

        :raises TypeError: Fname must be a valid path.
        """
        if not isinstance(fname, Path):
            raise TypeError("Filename must be given as a valid Path using pathlib.")
        self.fname = fname

        # header dictionary
        self.header = {}

        # data
        self._ions_per_shot = None
        self._all_tofs = None
        self._ions_to_tof_map = None

        # some quick-available variables
        self._nof_shots = None
        self._nof_ions = None

        # init end of file
        self.eof = False

        # now read the stuff
        self.read_data()

    @property
    def all_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """Get the data.

        :return: 1D array with ions per shot, 1D array with bin in which ions arrived
        """
        return self._ions_per_shot, self._all_tofs

    @property
    def all_tofs(self) -> np.ndarray:
        """Get all time of flight bins.

        :return: 1D array with bin in which ions arrived
        """
        return self._all_tofs

    @property
    def ions_per_shot(self) -> np.ndarray:
        """Get ions per shot array.

        :return: 1D array with ions per shot
        """
        return self._ions_per_shot

    @property
    def ions_to_tof_map(self) -> np.ndarray:
        """Get the index mapper for ions_per_shot -> tof.

        :return: Mapper with indexes where tofs are in all_tofs
        """
        return self._ions_to_tof_map

    @property
    def nof_ions(self) -> int:
        """Get the number of shots.

        :return: Number of shots.
        """
        return self._nof_ions

    @property
    def nof_shots(self) -> int:
        """Get the number of ions.

        :return: Number of ions.
        """
        return self._nof_shots

    # FUNCTIONS #

    def parse_data(self, data: bytes) -> None:
        """Parse the actual data out and put into the appropriate array.

        For this parsing to work, everything has to be just right, i.e., the number
        of shots have to be exactly defined and the data should have the right length.
        If not, this needs to throw a warning and move on to parse in a slower way.

        :param data: Binary string of all the data according to CRD specification.

        :warning: Number of Shots do not agree with the number of shots in the list or
            certain ions are outside the binRange. Fallback to slower reading routine.
        :warning: There is more data in this file than indicated by the number of Shots.
        """
        nof_shots = self.header["nofShots"]
        self._nof_shots = nof_shots

        ions_per_shot = np.zeros(nof_shots, dtype=np.int32)
        # calculate number of ions from filesize
        nof_ions = len(data) // 4 - nof_shots
        self._nof_ions = nof_ions
        all_tofs = np.zeros(nof_ions, dtype=np.int32)

        # loop through the data
        shot_ind = 0  # index in ions_per_shot array
        all_tof_ind = 0  # index in all_tofs array
        bin_ind = 0  # index in binary file
        warning_occured = False  # bool if we had a warning and need to take it slow
        while shot_ind < nof_shots:
            # ions in the given shot
            curr_ions_in_shot = struct.unpack("<I", data[bin_ind : bin_ind + 4])[0]
            ions_per_shot[shot_ind] = curr_ions_in_shot
            # now write out the times
            for _ in range(curr_ions_in_shot):
                try:
                    bin_ind += 4
                    curr_time_bin = struct.unpack("<I", data[bin_ind : bin_ind + 4])[0]
                    all_tofs[all_tof_ind] = curr_time_bin
                    all_tof_ind += 1
                except IndexError:
                    warning_occured = True
                    shot_ind = nof_shots  # to break out of while loop
                    break
            bin_ind += 4
            shot_ind += 1

        if warning_occured or bin_ind != len(data):
            warnings.warn(
                f"This CRD file does not adhere to the specifications and might be "
                f"corrupt. I will try a slow reading routine now in order to get the "
                f"data. Some information: \n"
                f"nof_shots: {self.nof_shots}\n"
                f"nof_ions: {self.nof_ions}\n"
            )
            self.parse_data_fallback(data)
            return
        else:
            self._ions_per_shot = ions_per_shot
            self._all_tofs = all_tofs

    def parse_data_fallback(self, data: bytes) -> None:
        """Slow reading routine in case the CRD file is corrupt.

        Here we don't assume anything and just try to read the data into lists and
        append them. Sure, this is going to be slow, but better than no data at all.

        :param data: Array of all the data.
        """
        ions_per_shot = []
        all_tofs = []

        bin_ind = 0  # index inside of binary `data`
        while bin_ind < len(data):
            curr_ions_in_shot = struct.unpack("<I", data[bin_ind : bin_ind + 4])[0]
            ions_per_shot.append(curr_ions_in_shot)
            # now append the times
            for _ in range(curr_ions_in_shot):
                bin_ind += 4
                curr_time_bin = struct.unpack("<I", data[bin_ind : bin_ind + 4])[0]
                all_tofs.append(curr_time_bin)
            bin_ind += 4

        self._nof_shots = len(ions_per_shot)
        self._ions_per_shot = np.array(ions_per_shot)
        self._nof_ions = len(all_tofs)
        self._all_tofs = np.array(all_tofs)

    def read_data(self) -> None:
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
            except KeyError as exc:
                raise KeyError(
                    f"The header version of this CRD file is {crd_version}, "
                    f"which is not available."
                ) from exc

            for (name, size, fmt) in hdr_description:
                self.header[name] = struct.unpack(fmt, f_in.read(size))[0]

            # now read in the rest of the file
            rest = f_in.read()

        if len(rest) % 4 != 0:
            raise OSError(
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

        # now call the mapper routine
        self._ions_to_tof_map = crd_utils.shot_to_tof_mapper(self._ions_per_shot)
