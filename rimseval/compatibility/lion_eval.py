"""Contains legacy routines that allow interaction with old LIONEval cal files."""

from pathlib import Path
from typing import List, Union
import warnings

import numpy as np


class LIONEvalCal:
    """Reads a calibration file from the LIONEval program."""

    def __init__(self, fname: Path) -> None:
        """Read all the data in and get ready to return them with properties only.

        :param fname: File name for old calibration file

        :raises TypeError: fname is not an instance of Path
        """
        if not isinstance(fname, Path):
            raise TypeError("Filename must be given as a valid Path using pathlib.")
        self._fname = fname

        self._mass_cal = None
        self._integrals = None
        self._bg_corr = None
        self._applied_filters = None

        self._process_file()

    @property
    def applied_filters(self) -> dict:
        """Return the applied filters.

        :return: Applied filters as loaded from LION cal file, in new format.
        """
        return self._applied_filters

    @property
    def mass_cal(self) -> np.ndarray:
        """Return the mass calibration from the file, if present.

        :return: Mass calibration as ndarray. Columns as following:
            1st: ToF (us)
            2nd: Mass (amu)
        """
        return self._mass_cal

    @property
    def integrals(self) -> List[List[Union[str, float]]]:
        """Return the integrals from the file, if present.

        :return: Integrals. Columns as following:
            1st: Name of the peak.
            2nd: Mass of the center (amu).
            3rd: Interval from center of mass to lower bound (amu).
            4th: Interval from center of mass to upper bound (amu).
        """
        return self._integrals

    @property
    def bg_corr(self) -> List[List[Union[str, float]]]:
        """Return background correction data of the peak, if present.

        :return: Background correction. Columns as following:
            1st: Name of the peak.
            2nd: Mass of the center (amu).
            3rd: Lower bound of background left of peak (amu).
            4th: Upper bound of background left of peak (amu).
            5th: Lower bound of background right of peak (amu).
            6th: Upper bound of background right of peak (amu).
        """
        return self._bg_corr

    def _process_file(self) -> None:
        """Read in the calibration file and process the various properties."""
        with self._fname.open("r") as f:
            data_in = []
            for line in f:
                data_in.append(line.rstrip())

        mcal_block = _extract_block(data_in, top_char="# Mass Calibration")
        integral_block = _extract_block(data_in, top_char="# Integral Calibration")
        bg_block = _extract_block(data_in, top_char="# Background Calibration")
        settings_block = _extract_block(
            data_in, top_char="# recalculation settings", bott_char="# EOF"
        )

        self._read_and_set_mcal(mcal_block)
        self._read_and_set_integrals(integral_block)
        self._read_and_set_bg_corr(bg_block)
        self._read_and_set_settings_calculation(settings_block)

    def _read_and_set_mcal(self, mcal_block: List[str]) -> None:
        """Read, parse, and set a mass calibration block."""
        if not mcal_block:
            return None

        mcal = []
        for line in mcal_block:
            entry = line.split()
            mcal.append([float(entry[0]), float(entry[1])])

        self._mass_cal = np.array(mcal)

    def _read_and_set_integrals(self, int_block: List[str]) -> None:
        """Read, parse, and set a integral block."""
        if not int_block:
            return None

        integrals = []
        for line in int_block:
            entry = line.split()
            integrals.append(
                [entry[0], float(entry[1]), float(entry[2]), float(entry[3])]
            )

        self._integrals = integrals

    def _read_and_set_bg_corr(self, bg_block: List[str]) -> None:
        """Read, parse, and set a background correction block."""
        if not bg_block:
            return None

        bg_corr = []
        for line in bg_block:
            entry = line.split()
            bg_corr.append(
                [
                    entry[0],
                    float(entry[1]),
                    float(entry[2]),
                    float(entry[3]),
                    float(entry[4]),
                    float(entry[5]),
                ]
            )

        self._bg_corr = bg_corr

    def _read_and_set_settings_calculation(self, settings_block: List[str]) -> None:
        """Read adn parse the parameters block."""
        if not settings_block:
            return None

        if len(settings_block) != 21:
            warnings.warn(
                "Calibration file contains the wrong number of settings. "
                "No calculation filters will be loaded.",
                stacklevel=1,
            )
            return None

        applied_filters = {
            "dead_time_corr": [
                bool(int(settings_block[0])),
                int(settings_block[1]),
            ],
            "packages": [
                bool(int(settings_block[2])),
                int(settings_block[3]),
            ],
            "max_ions_per_shot": [bool(int(settings_block[4])), int(settings_block[5])],
            "max_ions_per_pkg": [bool(int(settings_block[6])), int(settings_block[7])],
            "max_ions_per_time": [
                bool(int(settings_block[8])),
                int(settings_block[9]),
                float(settings_block[10]),
            ],
            "max_ions_per_tof_window": [
                bool(int(settings_block[11])),
                int(settings_block[12]),
                [float(settings_block[13]), float(settings_block[14])],
            ],
            "spectrum_part": [
                bool(int(settings_block[15])),
                [int(settings_block[16]), int(settings_block[17])],
            ],
        }

        self._applied_filters = applied_filters


def _extract_block(data: List[str], top_char: str, bott_char: str = "#") -> List[str]:
    """Extract a block from a given file.

    :param data: Data, i.e., the file content in a list with each line as an entry.
    :param top_char: Start of line above the block of interest (excluded)
    :param bott_char: Start of the line below the block of interest (excluded).
        Defaults to '#', i.e., a comment line.

    :return: List of all the lines that are in between the delimiting ones.
    """
    in_block = False
    data_block = []
    for line in data:
        if in_block:
            if line[: len(bott_char)] != bott_char:
                data_block.append(line)
            else:
                break

        # check for block starter, this is at the end since this line is excluded
        if line[: len(top_char)] == top_char:
            in_block = True

    return data_block
