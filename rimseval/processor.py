"""Processes a CRD file.

Note: Interfacing with external files is done in the `interfacer.py` library.
"""

from pathlib import Path
from typing import List, Tuple, Union
import warnings

from iniabu import ini
from numba import jit, njit
import numpy as np
from scipy.optimize import curve_fit

from .data_io.crd_reader import CRDReader
from . import processor_utils
from .utilities import string_transformer, peirce


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
        self.fname = fname
        self.crd = CRDReader(fname)
        self.ions_per_shot = self.crd.ions_per_shot
        self.ions_to_tof_map = self.crd.ions_to_tof_map
        self.all_tofs = self.crd.all_tofs

        # Data, ToF, and Masses
        self.tof = None
        self.mass = None
        self.data = None
        self.data_pkg = None

        # variables for filtered packages
        self._filter_max_ion_per_pkg_applied = False  # was max ions per pkg run?
        self._pkg_size = None  # max ions filtered with
        self._filter_max_ion_per_pkg_ind = None  # indices of pkgs that were trashed

        # Integrals
        self.integrals = None
        self.integrals_pkg = None

        # parameters for calibration and evaluation
        self._params_mcal = None  # mass calibration
        self._params_integrals = None  # integral definitions
        self._params_bg_corr = None  # bg_correction
        self._peak_fwhm = 0.0646  # peak fwhm in us

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

    @property
    def peak_fwhm(self) -> float:
        """Get / Set the FWHM of the peak.

        :return: FWHM of the peak in us.
        """
        return self._peak_fwhm

    @peak_fwhm.setter
    def peak_fwhm(self, value: float) -> None:
        self._peak_fwhm = value

    # METHODS #

    def dead_time_correction(self, dbins: int) -> None:
        """Perform a dead time correction on the whole spectrum.

        If packages were set, the dead time correction is performed on each package
        individually as well.

        :param dbins: Number of dead bins after original bin (total - 1).

        :warning.warn: There are no shots left in the package. No deadtime
            correction can be applied.
        """
        if self.nof_shots == 0:
            warnings.warn("No data available; maybe all shots were filtered out?")
            return

        self.data = processor_utils.dead_time_correction(
            self.data.reshape(1, self.data.shape[0]),
            np.array(self.nof_shots).reshape(1),
            dbins,
        )[
            0
        ]  # want to shape it back the way it was!

        if self.data_pkg is not None:
            self.data_pkg = processor_utils.dead_time_correction(
                self.data_pkg, self.nof_shots_pkg, dbins
            )

    def filter_max_ions_per_pkg(self, max_ions: int) -> None:
        """Filter out packages with too many ions.

        .. note:: Only run more than once if filtering out more. Otherwise, you need
            to reset the dataset first.

        :param max_ions: Maximum number of ions per package.

        :raise ValueError: Invalid range for number of ions.
        :raise IOError: No package data available.
        """
        if max_ions < 1:
            raise ValueError("The maximum number of ions must be larger than 1.")
        if self.data_pkg is None:
            raise IOError("There is no packaged data. Please create packages first.")

        # update helper variables
        self._filter_max_ion_per_pkg_applied = True

        total_ions_per_pkg = np.sum(self.data_pkg, axis=1)

        self._filter_max_ion_per_pkg_ind = np.where(total_ions_per_pkg > max_ions)[0]

        self.data_pkg = np.delete(
            self.data_pkg, self._filter_max_ion_per_pkg_ind, axis=0
        )
        self.nof_shots_pkg = np.delete(
            self.nof_shots_pkg, self._filter_max_ion_per_pkg_ind, axis=0
        )

        self.data = np.sum(self.data_pkg, axis=0)
        self.nof_shots = np.sum(self.nof_shots_pkg)

    def filter_max_ions_per_shot(self, max_ions: int) -> None:
        """Filter out shots that have more than the max_ions defined.

        .. note:: Only run more than once if filtering out more. Otherwise, you need
            to reset the dataset first.

        :param max_ions: Maximum number of ions allowed in a shot.

        :raise ValueError: Invalid range for number of ions.
        """
        if max_ions < 1:
            raise ValueError("The maximum number of ions must be >=1.")

        shots_indexes = np.where(self.ions_per_shot <= max_ions)[0]
        shots_rejected = np.where(self.ions_per_shot > max_ions)[0]

        # reject filtered packages, i.e., remove ions from deleted packages
        if self._filter_max_ion_per_pkg_applied:
            for pkg_it in self._filter_max_ion_per_pkg_ind:
                lower_lim = pkg_it * self._pkg_size
                upper_lim = lower_lim + self._pkg_size
                shots_indexes = shots_indexes[
                    np.where(
                        np.logical_or(
                            shots_indexes < lower_lim, shots_indexes >= upper_lim
                        )
                    )
                ]
                shots_rejected = shots_rejected[
                    np.where(
                        np.logical_or(
                            shots_rejected < lower_lim, shots_rejected >= upper_lim
                        )
                    )
                ]

        rng_all_tofs = self.ions_to_tof_map[shots_indexes]
        tof_indexes = processor_utils.multi_range_indexes(rng_all_tofs)

        all_tofs_filtered = self.all_tofs[tof_indexes]
        self.data = processor_utils.sort_data_into_spectrum(
            all_tofs_filtered,
            self.all_tofs.min(),
            self.all_tofs.max(),
        )

        # remove the rejected shots from packages
        if self.data_pkg is not None:
            for shot_rej in shots_rejected:
                # calculate index of package
                pkg_ind = shot_rej // self._pkg_size
                # need to subtract number of filtered packages up to here!
                pkg_rej_until = len(
                    np.where(self._filter_max_ion_per_pkg_ind < pkg_ind)
                )
                pkg_ind -= pkg_rej_until

                # get tofs to subtract from package and set up array with proper sizes
                rng_tofs = self.ions_to_tof_map[shot_rej]
                ions_to_sub = self.all_tofs[rng_tofs[0] : rng_tofs[1]]
                array_to_sub = np.zeros_like(self.data_pkg[pkg_ind])
                array_to_sub[ions_to_sub - self.all_tofs.min()] += 1

                self.data_pkg[pkg_ind] -= array_to_sub
                self.nof_shots_pkg[pkg_ind] -= 1

        self.ions_per_shot = self.ions_per_shot[shots_indexes]
        self.ions_to_tof_map = self.ions_to_tof_map[shots_indexes]
        self.all_tofs = all_tofs_filtered
        self.nof_shots = len(shots_indexes)

        assert self.nof_shots == self.nof_shots_pkg.sum()  # a simple, quick test

    def filter_pkg_peirce_countrate(self) -> None:
        """Filter out packages based on Peirce criterion for total count rate.

        .. note:: Only run more than once if filtering out more. Otherwise, you need
            to reset the dataset first.

        Now we are going to directly use all the integrals to get the sum of the counts,
        which we will then feed to the rejection routine. Maybe this can detect blasts.
        """
        sum_integrals = self.integrals_pkg[:, :, 0].sum(axis=1)
        _, _, _, rejected_indexes = peirce.reject_outliers(sum_integrals)

        print(
            f"Peirce criterion rejected "
            f"{len(rejected_indexes)} / {len(self.integrals_pkg)} "
            f"packages"
        )
        index_list = list(map(int, rejected_indexes))
        integrals_pkg = np.delete(self.integrals_pkg, index_list, axis=0)
        self.nof_shots_pkg = np.delete(self.nof_shots_pkg, index_list)
        self.nof_shots = np.sum(self.nof_shots_pkg)

        # integrals
        integrals = np.zeros_like(self.integrals)
        integrals[:, 0] = integrals_pkg.sum(axis=0)[:, 0]
        integrals[:, 1] = np.sqrt(np.sum(integrals_pkg[:, :, 1] ** 2, axis=0))

        # write back
        self.integrals = integrals
        self.integrals_pkg = integrals_pkg

    def filter_pkg_peirce_delta(self, ratios: List[Tuple[str, str]]) -> None:
        """Filter out packages based on Peirce criterion for delta values.

        # fixme: this routine needs to be deleted!

        For the given ratios, calculate the isotope ratio for each package, then
        calculate the delta values using Solar System abundances. Based on these values,
        apply Peirce's criterion to reject outliers and delete them from the packages.
        Ultimately, create the total sum of the integrals again.

        # fixme there's a lot to do here...

        :param ratios: Ratios to consider, e.g., (("46Ti", "48Ti"), ("47Ti", "48Ti")).
            These ratios must have the same names as the integrals and must be valid
            isotope names.
        """
        peaks = self.def_integrals[0]
        integrals = self.integrals_pkg[:, :, 0]

        rejected_indexes = []  # we will append numpy arrays here
        for ratio in ratios:
            int_ratio = (
                integrals[:, peaks.index(ratio[0])]
                / integrals[:, peaks.index(ratio[1])]
            )
            int_delta = ini.iso_delta(
                string_transformer.iso_to_iniabu(ratio[0]),
                string_transformer.iso_to_iniabu(ratio[1]),
                int_ratio,
            )
            _, _, _, indexes = peirce.reject_outliers(int_delta)
            rejected_indexes.append(indexes)

        # now create a set out of the indexes and then sort them to become a list
        index_set = set(rejected_indexes[0])
        for ind in range(1, len(rejected_indexes)):
            index_set = index_set.union(rejected_indexes[ind])

        index_list = sorted(map(int, index_set))

        print(
            f"Peirce criterion rejected {len(index_list)} / {len(self.integrals_pkg)} "
            f"packages"
        )

        integrals_pkg = np.delete(self.integrals_pkg, index_list, axis=0)
        self.nof_shots_pkg = np.delete(self.nof_shots_pkg, index_list)
        self.nof_shots = np.sum(self.nof_shots_pkg)

        # integrals
        integrals = np.zeros_like(self.integrals)
        integrals[:, 0] = integrals_pkg.sum(axis=0)[:, 0]
        integrals[:, 1] = np.sqrt(np.sum(integrals_pkg[:, :, 1] ** 2, axis=0))

        # write back
        self.integrals = integrals
        self.integrals_pkg = integrals_pkg

    def integrals_calc(self) -> None:
        """Calculate integrals for data and packages (if present).

        The integrals to be set per peak are going to be set as an ndarray.
        Each row will contain one entry in the first column and its associated
        uncertainty in the second.

        # ToDo Will require special handling once background correction incorporated.

        :return: None

        :raise ValueError: No integrals were set.
        :raise ValueError: No mass calibration has been applied.
        """
        if self._params_integrals is None:
            raise ValueError("No integrals were set.")
        if self.mass is None:
            raise ValueError("A mass calibration needs to be applied first.")

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

        self.mass = processor_utils.mass_calibration(self.def_mcal, self.tof)

    def optimize_mcal(self, offset: float = None) -> None:
        """Takes an existing mass calibration and finds maxima within a FWHM.

        This will act on small corrections for drifts in peaks.

        :param offset: How far do you think the peak has wandered? If None, it will be
            set to the FWHM value.
        """
        if offset is None:
            offset = self.peak_fwhm

        positions = self.def_mcal[:, 0]
        positions_new = np.zeros_like(positions) * np.nan  # nan array

        for it, pos in enumerate(positions):
            min_time = pos - offset - 2 * self.peak_fwhm
            max_time = pos + offset + 2 * self.peak_fwhm
            if max_time > self.tof.max():  # we don't have a value here
                continue
            window = np.where(np.logical_and(self.tof > min_time, self.tof < max_time))
            tofs = self.tof[window]
            data = self.data[window]
            positions_new[it] = processor_utils.gaussian_fit_get_max(tofs, data)

        mcal_new = self.def_mcal.copy()
        index_to_del = []
        for it, posn in enumerate(positions_new):
            if np.abs(mcal_new[it][0] - posn) < offset:
                mcal_new[it][0] = posn
            else:
                index_to_del.append(it)

        mcal_new = np.delete(mcal_new, index_to_del, axis=0)
        if len(mcal_new) < 2:
            warnings.warn(
                "Automatic mass calibration optimization did not find enough peaks."
            )
        else:
            self.def_mcal = mcal_new

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

        self._pkg_size = shots

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

        :param rng: Shot range, either as a tuple (from, to) or as a tuple of multiple
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
