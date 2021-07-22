"""Processes a CRD file.

Note: Interfacing with external files is done in the `interfacer.py` library.
"""

from pathlib import Path
from typing import List, Tuple, Union
import warnings

from numba import jit, njit
import numpy as np
from scipy.optimize import curve_fit

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

        # Data, ToF, and Masses
        self.tof = None
        self.mass = None
        self.data = None
        self.data_pkg = None

        # Integrals
        self.integrals = None
        self.integrals_pkg = None

        # parameters for calibration and evaluation
        self._params_mcal = None  # mass calibration
        self._params_integrals = None  # integral definitions
        self._params_bg_corr = None  # bg_correction

        # file info
        self.nof_shots = self.crd.nof_shots
        self.nof_shots_pkg = None

    # PROPERTIES #

    @property
    def def_mcal(self) -> np.ndarray:
        """Mass calibration definitions.

        :return: Mass calibration definitions. The columns are as following:
            1st: ToF (us)
            2nd: Mass (amu)

        :raise TypeError: Value is not a numpy ndarray
        :raise ValueError: At least two parameters must be given for a mass calibration.
        :raise ValueError: The array is of the wrong shape.
        """
        return self._params_mcal

    @def_mcal.setter
    def def_mcal(self, value):
        if not isinstance(value, np.ndarray):
            raise TypeError(
                f"Mass calibration definition must be given as a numpy "
                f"ndarray but is a {type(value)}."
            )
        if value.shape[0] < 2:
            raise ValueError("At least two mass calibration points must be given.")
        if value.shape[1] != 2:
            raise ValueError("The mass calibration definition is of the wrong shape.")
        self._params_mcal = value

    @property
    def def_integrals(self) -> Tuple[List[str], np.ndarray]:
        """Integral definitions.

        The definitions consist of a tuple of a list and an np.ndarray.
        The list contains first the names of the integrals.
        The np.ndarray then contains in each row the lower and upper limit in amu of
        the peak that needs to be integrated.

        :return: Integral definitions.

        :raise ValueError: Data Shape is wrong
        """
        return self._params_integrals

    @def_integrals.setter
    def def_integrals(self, value):
        if not value:  # empty list is passed
            self._params_integrals = None
        else:
            if len(value[0]) != len(value[1]):
                raise ValueError("Name and data array must have the same length.")
            if value[1].shape[1] != 2:
                raise ValueError("The data array must have 2 entries for every line.")

            self._params_integrals = value

    # METHODS #

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

    def integrals_calc(self) -> None:
        """Calculate integrals for data and packages (if present).

        The integrals to be set per peak are going to be set as an ndarray.
        Each row will contain one entry in the first column and its associated
        uncertainty in the second.

        # ToDo Will require special handling once background correction incorporated.

        :return: None

        :raise ValueError: No integrals were set.
        """
        if self._params_integrals is None:
            raise ValueError("No integrals were set.")

        names, limits = self.def_integrals

        windows = []  # integrals defined in mass windows
        for lower, upper in limits:
            windows.append(
                np.where(np.logical_and(self.mass >= lower, self.mass <= upper))
            )

        self.integrals, self.integrals_pkg = processor_utils.integrals_summing(
            self.data, tuple(windows), self.data_pkg
        )

    def mass_calibration(self) -> None:
        """Perform a mass calibration on the data.

        Let m be the mass and t the respective time of flight. We can then write:

            .. math::
                t \propto \sqrt[a]{m}

        Usually it is assumed that $a=2$, i.e., that the square root is taken.
        We don't have to assume this though. In the generalized form we can now
        linearize the mass calibration such that:

            .. math::
                \log(m) = a \log(t) + b

        Here, :math:`a` is, as above, the exponent, and :math:`b` is a second constant.
        With two values or more for :math:`m` and :math:`t`, we can then make a
        linear approximation for the mass calibration :math:`m(t)`.

        :return: None

        :raise ValueError: No mass calibration set.
        """
        if self._params_mcal is None:
            raise ValueError("No mass calibration was set.")

        params = self.def_mcal

        # function to return mass with a given functional form
        calc_mass = processor_utils.calculate_mass_square

        # calculate the initial guess for scipy fitting routine
        ch1 = params[0][0]
        m1 = params[0][1]
        ch2 = params[1][0]
        m2 = params[1][1]
        t0 = (ch1 * np.sqrt(m2) - ch2 * np.sqrt(m1)) / (np.sqrt(m2) - np.sqrt(m1))
        b = np.sqrt((ch1 - t0) ** 2.0 / m1)

        # fit the curve and store the parameters
        params_fit = curve_fit(calc_mass, params[:, 0], params[:, 1], p0=(t0, b))

        self.mass = calc_mass(self.tof, params_fit[0][0], params_fit[0][1])

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
        self.tof = (
            np.arange(bin_start, bin_end + 1, 1) * bin_length / 1e6 + delta_t * 1e6
        )
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
            self.tof = np.arange(len(self.data)) * bin_length / 1e6

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
