"""Processes a CRD file."""

from pathlib import Path
from typing import List, Tuple, Union
import warnings

from numba import jit, njit
import numpy as np

from .data_io.crd_reader import CRDReader
from . import processor_utils


class CRDFileProcessor:
    """Process a CRD file in this class, dead time corrections, etc.

    Computationally expensive routines are sourced out into processor_utils.py for
    jitting.

    Todo example
    """

    def __init__(self, fname: Path) -> None:
        """Initialize the processor and read the CRD file that is wanted.

        :param fname: Filename of CRD file to be processed
        :type fname: Path
        """
        # read in the CRD file
        self.crd = CRDReader(fname)

        # create ToF spectrum
        self.tof = None
        self.mass = None
        self.data = None

        # file info
        self.nof_shots = self.crd.nof_shots

    def dead_time_correction(self, dbins: int) -> None:
        """Perform a dead time correction on the whole spectrum.

        :param dbins: Number of dead bins after original bin (total - 1).
        """
        self.data = processor_utils.dead_time_correction(
            self.data, self.crd.nof_shots, dbins
        )

    def spectrum_full(self) -> None:
        """Create ToF and summed ion count array for the full spectrum.

        The full spectrum is transfered to ToF and ion counts. The spectrum is then
        saved to:
            - ToF array is written to `self.tof`
            - Data array is written to `self.data`

        :warnings: Time of Flight and data have different shape
        """
        bin_length = self.crd.header["binLength"]
        bin_start = self.crd.header["binStart"]
        bin_end = self.crd.header["binEnd"]
        delta_t = self.crd.header["deltaT"]
        # set up ToF
        self.tof = np.arange(bin_start, bin_end + 1, 1) * bin_length + delta_t
        self.data = processor_utils.sort_data_into_spectrum(self.crd.all_tofs)

        if self.tof.shape != self.data.shape:
            # fixme remove print
            print(f"Header binStart: {bin_start}, binEnd: {bin_end}")
            print(
                f"File binStart: {self.crd.all_tofs.min()}, "
                f"binEnd {self.crd.all_tofs.max()}"
            )
            warnings.warn(
                "Bin ranges in CRD file were of bad length. Creating ToF "
                "array without CRD header input."
            )
            self.tof = np.arange(len(self.data)) * bin_length

    def spectrum_part(
        self, rng: Tuple[Tuple[int, int], Tuple[Tuple[int, int]]]
    ) -> None:
        """Create ToF for a part of the spectra.

        Select part of the shot range. These ranges will be 1 indexed!

        :rng: Shot range, either as a tuple (from, to) or as a tuple of multiple
            ((from1, to1), (from2, to2), ...).

        :raises ValueError: Ranges are not defined from, to where from < to
        :raises ValueError: Tuples are not mutually exclusive.
        """
        rng = np.array(rng)
        if len(rng.shape) == 1:  # only one entry
            rng = rng.reshape(1, 2)

        # subtract 1 such that zero indexed
        rng -= 1

        # sort by first entry
        rng = rng[rng[:, 0].argsort()]

        # check if any issues with the
        if all(rng[:, 1] < rng[:, 0]):
            raise ValueError(
                "The `from, to` values in your range are not defined "
                "such that `from` < `to`."
            )

        # check that mutually exclusive
        for it in range(1, len(rng)):
            if rng[it - 1][1] >= rng[it][0]:
                raise ValueError("Your ranges are not mutually exclusive.")

        # get ions such that they are a view on the range
        all_tofs = self.crd.all_tofs

        # filter ions per shot
        ion_indexes = processor_utils.multi_range_indexes(rng)

        # create all_tof ranges and filter
        rng_all_tofs = self.crd.ions_to_tof_map[ion_indexes]
        tof_indexes = processor_utils.multi_range_indexes(rng_all_tofs)

        # if empty shape: we got no data!
        if len(tof_indexes) == 0:
            self.data = np.zeros_like(self.data)
        else:
            self.data = processor_utils.sort_data_into_spectrum(all_tofs[tof_indexes])

        self.nof_shots = len(ion_indexes)
