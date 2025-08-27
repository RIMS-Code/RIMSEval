"""Transform KORE's lst files and ini files to CRD files."""

from datetime import datetime
import os
from pathlib import Path
import struct
import warnings

import numpy as np

import rimseval.data_io.crd_utils as crd_utils


class KORE2CRD:
    """Convert KORE list files to CRD files."""

    def __init__(self, file_name: Path) -> None:
        """Initialize the converter with a file name.

        After initialization of the class, please run `write_crd()` method
        to create the CRD file.

        :param file_name: Path to the KORE lst or ini file without extension.

        :raises FileNotFoundError: If the ini or lst file does not exist.
        """
        self.file_lst = file_name.with_suffix(".lst")
        self.file_ini = file_name.with_suffix(".ini")

        if not self.file_ini.exists():
            raise FileNotFoundError(f"INI file {self.file_ini} does not exist.")
        if not self.file_lst.exists():
            raise FileNotFoundError(f"LST file {self.file_lst} does not exist.")

        self._acq_datetime = None
        self._bin_width_ns = None
        self._first_bin = None
        self._last_bin = None
        self._num_scans = None
        self._num_shots = None
        self._shots_per_pixel = None
        self._shot_pattern = None

        self._parse_ini_file()

    def _parse_ini_file(self):
        """Parse the ini file an set the required attributes of the class."""
        with open(self.file_ini) as ini_file:
            for line in ini_file:
                if line.startswith("Experiment type="):
                    exp_tp = get_right(line)
                    if exp_tp != "Mapping":
                        raise ValueError(
                            f"Unsupported experiment type: {exp_tp}. Only 'Mapping' is supported."
                        )
                    else:
                        self._shot_pattern = 32  # see CRD pdf
                elif line.startswith("Acq start time="):
                    ts = get_right(line)
                    fmt = "%Y-%m-%d %H:%M:%S"
                    self._acq_datetime = datetime.strptime(ts, fmt)
                elif line.startswith("Time unit ns="):
                    self._bin_width_ns = float(get_right(line))
                elif line.startswith("First bin="):
                    self._first_bin = int(get_right(line))
                elif line.startswith("Last bin="):
                    self._last_bin = int(get_right(line))
                elif line.startswith("Frames="):
                    self._num_scans = int(get_right(line))
                elif line.startswith("Number of cycles="):
                    self._num_shots = int(get_right(line))
                elif line.startswith("Cycles per point="):
                    self._shots_per_pixel = int(get_right(line))

        if self.shot_pattern is None:
            raise ValueError("Experiment type not found in the INI file.")
        if self._acq_datetime is None:
            raise ValueError("Acquisition date not found in the INI file.")
        if self._bin_width_ns is None:
            raise ValueError("Bin width not found in the INI file.")
        if self.first_bin is None:
            raise ValueError("First bin not found in the INI file.")
        if self.last_bin is None:
            raise ValueError("Last bin not found in the INI file.")
        if self.num_scans is None:
            raise ValueError("Number of scans not found in the INI file.")
        if self.num_shots is None:
            raise ValueError("Number of shots not found in the INI file.")
        if self.shots_per_pixel is None:
            raise ValueError("Shots per pixel not found in the INI file.")

    @property
    def acq_datetime(self) -> str:
        """Return the acquisition date in CRD format.

        The date is formatted as 'YYYY:MM:DD hh:mm:ss'.
        """
        fmt = "%Y:%m:%d %H:%M:%S"
        return self._acq_datetime.strftime(fmt)

    @property
    def bin_width_ps(self) -> int:
        """Return the bin width in picoseconds."""
        return int(self._bin_width_ns * 1000)

    @property
    def first_bin(self) -> int:
        """Return the first bin number."""
        return self._first_bin

    @property
    def last_bin(self) -> int:
        """Return the last bin number."""
        return self._last_bin

    @property
    def num_pixels(self) -> int:
        """Calculate and return the number of pixels.

        Calculated as an integer of number of shots / shots per pixel / number of scans.
        """
        return int(self._num_shots / self._shots_per_pixel / self._num_scans)

    @property
    def num_scans(self) -> int:
        """Return the number of scans."""
        return self._num_scans

    @property
    def num_shots(self) -> int:
        """Return the number of shots."""
        return self._num_shots

    @property
    def shot_pattern(self) -> int:
        """Return the shot pattern used in the experiment."""
        return self._shot_pattern

    @property
    def shots_per_pixel(self) -> int:
        """Return the number of shots per pixel."""
        return self._shots_per_pixel

    @property
    def xdim(self) -> int:
        """Return the x dimension of the image in pixels."""
        return int(np.sqrt(self.num_pixels))

    @property
    def ydim(self) -> int:
        """Return the y dimension of the image in pixels - assume square image always."""
        return self.xdim

    def write_crd(self):
        """Write the CRD file based on the parsed ini file and the lst file."""
        crd_name = self.file_lst.with_suffix(".crd")
        default = crd_utils.CURRENT_DEFAULTS

        with open(crd_name, "wb") as crd_out:
            # Write the header
            crd_out.write(default["fileID"])
            crd_out.write(struct.pack("20s", bytes(self.acq_datetime, "utf-8")))
            crd_out.write(default["minVer"])
            crd_out.write(default["majVer"])
            crd_out.write(default["sizeOfHeaders"])
            crd_out.write(struct.pack("<I", self.shot_pattern))
            crd_out.write(default["tofFormat"])
            crd_out.write(default["polarity"])
            crd_out.write(struct.pack("<I", self.bin_width_ps))
            crd_out.write(struct.pack("<I", self.first_bin))
            crd_out.write(struct.pack("<I", self.last_bin))
            crd_out.write(struct.pack("<I", self.xdim))
            crd_out.write(struct.pack("<I", self.ydim))
            crd_out.write(struct.pack("<I", self.shots_per_pixel))
            crd_out.write(struct.pack("<I", self.num_pixels))
            crd_out.write(struct.pack("<I", self.num_scans))
            crd_out.write(struct.pack("<I", self.num_shots))
            crd_out.write(default["deltaT"])

            # Read and write the data
            num_shots = 0
            try:
                for shot in self._get_next_shot():
                    num_shots += 1
                    length = len(shot)
                    crd_out.write(struct.pack("<I", length))
                    for value in shot:
                        crd_out.write(struct.pack("<I", value))
            except OSError as e:
                os.remove(crd_name)
                raise OSError(f"Error reading the lst file: {e}")

            if num_shots != self.num_shots:
                warnings.warn(
                    f"Number of shots in the LST file ({num_shots}) does not match the number in the INI file ({self.num_shots}).",
                    UserWarning,
                    stacklevel=1,
                )

            # Write EoF
            crd_out.write(default["eof"])

    def _get_next_shot(self) -> list[int]:
        """Generator that gets the next shot from the lst file and yields the data as a list of integers."""
        out_lst = []
        get_next_byte = self._get_next_byte()
        for next_byte in get_next_byte:
            if next_byte == 0:  # found a start, yield the list and reset it
                yield out_lst
                out_lst = []
            elif next_byte >> 8 == 0xFFFF:  # do nothing
                pass
            else:  # it's a regular byte, append it to the list
                out_lst.append(next_byte)
        # finally, no more bytes, so let's yield the leftovers
        yield out_lst

    def _get_next_byte(self) -> int:
        """Generator that opens the lst file and yields the next byte as an integer."""
        with open(self.file_lst, "rb") as lst_file:
            # toss the first 3 bytes but ensure it's a 0
            first = lst_file.read(3)
            if first == b"":
                raise OSError("The lst file is empty.")
            elif first != b"\x00\x00\x00":
                raise ValueError("The first three bytes are not a start.")

            while data := lst_file.read(3):
                yield int(data.hex(), 16)


def get_right(line: str) -> str:
    """Return the right part of a line after the '=' sign."""
    return line.split("=")[1].strip() if "=" in line else line.strip()
