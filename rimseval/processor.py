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
        self.ions_per_shot = self.crd.ions_per_shot
        self.ions_to_tof_map = self.crd.ions_to_tof_map
        self.all_tofs = self.crd.all_tofs

        # create ToF spectrum
        self.tof = None
        self.mass = None
        self.data = None
        self.data_pkg = None

        # file info
        self.nof_shots = self.crd.nof_shots
        self.nof_shots_pkg = None

    def dead_time_correction(self, dbins: int) -> None:
        """Perform a dead time correction on the whole spectrum.

        If packages were set, the dead time correction is performed on each package
        individually as well.

        :param dbins: Number of dead bins after original bin (total - 1).
        """
        self.data = processor_utils.dead_time_correction(
            self.data.reshape(1, self.data.shape[0]),
            np.array(self.nof_shots).reshape(1),
            dbins,
        )

        if self.data_pkg is not None:
            self.data_pkg = processor_utils.dead_time_correction(
                self.data_pkg, self.nof_shots_pkg, dbins
            )

    def filter_max_ions_per_pkg(self, max_ions: int) -> None:
        """Filter out packages with too many ions.

        :param max_ions: Maximum number of ions per package.

        :raise ValueError: Invalid range for number of ions.
        :raise IOError: No package data available.
        """
        if max_ions < 1:
            raise ValueError("The maximum number of ions must be larger than 1.")
        if self.data_pkg is None:
            raise IOError("There is no packaged data. Please create packages first.")

        total_ions_per_pkg = np.sum(self.data_pkg, axis=1)

        self.data_pkg = np.delete(
            self.data_pkg, np.where(total_ions_per_pkg > max_ions)[0], axis=0
        )
        self.nof_shots_pkg = np.delete(
            self.nof_shots_pkg, np.where(total_ions_per_pkg > max_ions)[0], axis=0
        )

    def filter_max_ions_per_shot(self, max_ions: int) -> None:
        """Filter out shots that have more than the max_ions defined.

        :param max_ions: Maximum number of ions allowed in a shot.

        :raise ValueError: Invalid range for number of ions.
        """
        if max_ions < 1:
            raise ValueError("The maximum number of ions must be larger than 1.")

        ion_indexes = np.where(self.ions_per_shot <= max_ions)[0]

        rng_all_tofs = self.ions_to_tof_map[ion_indexes]
        tof_indexes = processor_utils.multi_range_indexes(rng_all_tofs)

        all_tofs_filtered = self.all_tofs[tof_indexes]
        self.data = processor_utils.sort_data_into_spectrum(
            all_tofs_filtered,
            self.all_tofs.min(),
            self.all_tofs.max(),
        )

        self.ions_per_shot = self.ions_per_shot[ion_indexes]
        self.ions_to_tof_map = self.ions_to_tof_map[ion_indexes]
        self.all_tofs = all_tofs_filtered
        self.nof_shots = len(ion_indexes)

    def packages(self, shots: int) -> None:
        """Break data into packages.

        :param shots: Number of shots per package. The last package will have the rest.

        :raise ValueError: Number of shots out of range
        """
        if shots < 1 or shots >= self.nof_shots:
            raise ValueError(
                f"Number of shots per package must be between 1 and "
                f"{self.nof_shots}, but is {shots}."
            )

        self.data_pkg, self.nof_shots_pkg = processor_utils.create_packages(
            shots, self.ions_to_tof_map, self.all_tofs
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

        # reset the data
        self.ions_to_tof_map = self.crd.ions_to_tof_map
        self.all_tofs = self.crd.all_tofs

        # set up ToF
        self.tof = np.arange(bin_start, bin_end + 1, 1) * bin_length + delta_t
        self.data = processor_utils.sort_data_into_spectrum(
            self.all_tofs, self.all_tofs.min(), self.all_tofs.max()
        )

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

        Select part of the shot range. These ranges will be 1 indexed! Always start
        with the full data range.

        :rng: Shot range, either as a tuple (from, to) or as a tuple of multiple
            ((from1, to1), (from2, to2), ...).

        :raises ValueError: Ranges are not defined from, to where from < to
        :raises ValueError: Tuples are not mutually exclusive.
        """
        # reset current settings
        self.ions_to_tof_map = self.crd.ions_to_tof_map
        self.all_tofs = self.crd.all_tofs

        # range
        rng = np.array(rng)
        if len(rng.shape) == 1:  # only one entry
            rng = rng.reshape(1, 2)

        # subtract 1 from start range -> zero indexing plus upper limit inclusive now
        rng[:, 0] -= 1

        # sort by first entry
        rng = rng[rng[:, 0].argsort()]

        # check if any issues with the
        if any(rng[:, 1] < rng[:, 0]):
            raise ValueError(
                "The `from, to` values in your range are not defined "
                "such that `from` < `to`."
            )

        # check that mutually exclusive
        for it in range(1, len(rng)):
            if rng[it - 1][1] > rng[it][0]:
                raise ValueError("Your ranges are not mutually exclusive.")

        # filter ions per shot
        ion_indexes = processor_utils.multi_range_indexes(rng)

        # create all_tof ranges and filter
        rng_all_tofs = self.ions_to_tof_map[ion_indexes]
        tof_indexes = processor_utils.multi_range_indexes(rng_all_tofs)

        all_tofs_filtered = self.all_tofs[tof_indexes]
        ions_to_tof_map_filtered = self.ions_to_tof_map[ion_indexes]

        # if empty shape: we got no data!
        if len(tof_indexes) == 0:
            self.data = np.zeros_like(self.data)
        else:
            self.data = processor_utils.sort_data_into_spectrum(
                all_tofs_filtered, all_tofs_filtered.min(), all_tofs_filtered.max()
            )

        # set back values
        self.ions_per_shot = self.ions_per_shot[ion_indexes]
        self.ions_to_tof_map = ions_to_tof_map_filtered
        self.all_tofs = all_tofs_filtered
        self.nof_shots = len(ion_indexes)
