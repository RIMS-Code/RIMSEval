"""Processes a CRD file."""

from pathlib import Path
import warnings

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

    def dead_time_correction(self, dbins: int) -> None:
        """Perform a dead time correction on the whole spectrum.

        :param dbins: Number of dead bins
        :type dbins: int
        """

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

        print(bin_start, bin_end)
        print(self.crd.all_tofs.min(), self.crd.all_tofs.max())

        if self.tof.shape != self.data.shape:
            warnings.warn(
                "Bin ranges in CRD file were of bad length. Creating ToF "
                "array without CRD header input."
            )
            self.tof = np.arange(len(self.data)) * bin_length
