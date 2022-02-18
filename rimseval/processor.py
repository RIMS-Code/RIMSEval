"""Processes a CRD file.

Note: Interfacing with external files is done in the `interfacer.py` library.
"""

from pathlib import Path
import sys
from typing import Any, List, Tuple, Union
import warnings

import numpy as np

from . import processor_utils
from .data_io.crd_reader import CRDReader
from .utilities import peirce, utils


class CRDFileProcessor:
    """Process a CRD file in this class, dead time corrections, etc.

    Computationally expensive routines are sourced out into processor_utils.py for
    jitting.

    Example:
        >>> my_file = Path("crd_files/my_file.crd")
        >>> crd = CRDFileProcessor(my_file)  # open the file
        >>> crd.spectrum_full()  # create a spectrum
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

        # dictionary for what was run already - to be saved out
        self.applied_filters = {}

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
        self._params_backgrounds = None  # bg_correction
        self._peak_fwhm = 0.0646  # peak fwhm in us
        self._us_to_chan = None  # how to change microseconds to channel / bin number

        # file info
        self.nof_shots = self.crd.nof_shots
        self.nof_shots_pkg = None

    # PROPERTIES #

    @property
    def def_backgrounds(self) -> Tuple[List[str], np.ndarray]:
        """Background definitions for integrals.

        The definitions consist of a tuple of a list and a np.ndarray.
        The list contains first the names of the integrals.
        The np.ndarray then contains in each row the lower and upper limit in amu of
        the peak that needs to be integrated.

        .. note:: The format for defining backgrounds is the same as the format for
            defining integrals, except that peaks can occur multiple times for
            multiple backgrounds.

        :return: Background definitions.

        :raise ValueError: Data Shape is wrong

        Example:
            >>> data = CRDFileProcessor("my_data.crd")
            >>> peak_names = ["54Fe", "54Fe"]
            >>> peak_limits = np.array([[53.4, 53.6], [54.4, 54.6]])
            >>> data.def_integrals = (peak_names, peak_limits)
        """
        return self._params_backgrounds

    @def_backgrounds.setter
    def def_backgrounds(self, value):
        if not value:  # empty list is passed
            self._params_backgrounds = None
        else:
            if len(value) != 2:
                raise ValueError("Data tuple must be of length 2.")
            if len(value[0]) != len(value[1]):
                raise ValueError("Name and data array must have the same length.")
            if value[1].shape[1] != 2:
                raise ValueError("The data array must have 2 entries for every line.")

            self._params_backgrounds = value

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

        The definitions consist of a tuple of a list and a np.ndarray.
        The list contains first the names of the integrals.
        The np.ndarray then contains in each row the lower and upper limit in amu of
        the peak that needs to be integrated.

        :return: Integral definitions.

        :raise ValueError: Data Shape is wrong
        :raise ValueError: More than one definition exist for a given peak.

        Example:
            >>> data = CRDFileProcessor("my_data.crd")
            >>> peak_names = ["54Fe", "64Ni"]
            >>> peak_limits = np.array([[53.8, 54.2], [63.5, 64.5]])
            >>> data.def_integrals = (peak_names, peak_limits)
        """
        return self._params_integrals

    @def_integrals.setter
    def def_integrals(self, value):
        if not value:  # empty list is passed
            self._params_integrals = None
            self._params_backgrounds = None
        else:
            if len(value) != 2:
                raise ValueError("Data tuple must be of length 2.")
            if len(value[0]) != len(value[1]):
                raise ValueError("Name and data array must have the same length.")
            if value[1].shape[1] != 2:
                raise ValueError("The data array must have 2 entries for every line.")
            if len(value[0]) != len(set(value[0])):
                raise ValueError(
                    "The peak names for integral definitions must be unique."
                )

            # delete backgrounds that are unused
            if self._params_backgrounds is not None:
                ind_to_delete = []
                for it, name in enumerate(self._params_backgrounds[0]):
                    if name not in value[0]:
                        ind_to_delete.append(it)
                if len(ind_to_delete) == len(self._params_backgrounds[0]):
                    self._params_backgrounds = None
                else:  # remove existing
                    bg_names = [
                        ele
                        for id, ele in enumerate(self._params_backgrounds[0])
                        if id not in ind_to_delete
                    ]
                    bg_vals = np.delete(
                        self._params_backgrounds[1], ind_to_delete, axis=0
                    )
                    self._params_backgrounds = bg_names, bg_vals

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

    @property
    def us_to_chan(self) -> float:
        """Conversion factor for microseconds to channel / bin number.

        :return: Conversion factor
        """
        return self._us_to_chan

    @us_to_chan.setter
    def us_to_chan(self, value: float) -> None:
        self._us_to_chan = value

    # METHODS #

    def apply_individual_shots_filter(self, shots_rejected: np.ndarray):
        """Routine to finish filtering for individual shots.

        This will end up setting all the data. All routines that filter shots only
        have to provide a list of rejected shots. This routine does the rest, including.
        the handling of the data if packages exist.

        ToDo: rejected shots should be stored somewhere.

        :param shots_rejected: Indices of rejected shots.
        """
        len_indexes = len(self.ions_per_shot)

        # reject filtered packages, i.e., remove ions from deleted packages
        if self._filter_max_ion_per_pkg_applied:
            (
                shots_indexes,
                shots_rejected,
            ) = processor_utils.remove_shots_from_filtered_packages_ind(
                shots_rejected,
                len_indexes,
                self._filter_max_ion_per_pkg_ind,
                self._pkg_size,
            )
        else:
            shots_indexes = utils.not_index(shots_rejected, len_indexes)

        all_tofs_filtered = self._all_tofs_filtered(shots_indexes)

        self.data = processor_utils.sort_data_into_spectrum(
            all_tofs_filtered,
            self.crd.all_tofs.min(),
            self.crd.all_tofs.max(),
        )

        # remove the rejected shots from packages
        if self.data_pkg is not None:
            (
                self.data_pkg,
                self.nof_shots_pkg,
            ) = processor_utils.remove_shots_from_packages(
                self._pkg_size,
                shots_rejected,
                self.ions_to_tof_map,
                self.all_tofs,
                self.data_pkg,
                self.nof_shots_pkg,
                self._filter_max_ion_per_pkg_ind,
            )

        self.ions_per_shot = self.ions_per_shot[shots_indexes]
        self.ions_to_tof_map = self.ions_to_tof_map[shots_indexes]
        self.nof_shots = len(shots_indexes)

    def calculate_applied_filters(self):
        """Check for which filters are available and then recalculate all from start."""
        self.spectrum_full()  # reset all filters

        def get_arguments(key: str) -> Union[List, None]:
            """Get arguments from the dictionary or None.

            :param key: Key in dictionary ``self.applied_filters``

            :return: List if the key exists, None otherwise
            """
            try:
                return self.applied_filters[key]
            except KeyError:
                return

        # reset packages if not toggled
        if vals := get_arguments("packages"):
            if not vals[0]:
                self.data_pkg = None
                self._filter_max_ion_per_pkg_applied = False
                self._pkg_size = None
                self._filter_max_ion_per_pkg_ind = None
                self.integrals_pkg = None
                self.nof_shots_pkg = None

        # run through calculations
        if vals := get_arguments("spectrum_part"):
            if vals[0]:
                self.spectrum_part(vals[1])

        if vals := get_arguments("max_ions_per_shot"):
            if vals[0]:
                self.filter_max_ions_per_shot(vals[1])

        if vals := get_arguments("max_ions_per_time"):
            if vals[0]:
                self.filter_max_ions_per_time(vals[1], vals[2])

        if vals := get_arguments("max_ions_per_tof_window"):
            if vals[0]:
                self.filter_max_ions_per_tof_window(vals[1], np.array(vals[2]))

        if vals := get_arguments("packages"):
            if vals[0]:
                self.packages(vals[1])

        if vals := get_arguments("max_ions_per_pkg"):
            if vals[0]:
                self.filter_max_ions_per_pkg(vals[1])

        # fixme: after pierce criterion is done!
        # if get_arguments("pkg_peirce_rejection"):
        #     self.filter_pkg_peirce_countrate()

        if vals := get_arguments("macro"):
            if vals[0]:
                self.run_macro(Path(vals[1]))

        if vals := get_arguments("dead_time_corr"):
            if vals[0]:
                self.dead_time_correction(vals[1])

    def dead_time_correction(self, dbins: int) -> None:
        """Perform a dead time correction on the whole spectrum.

        If packages were set, the dead time correction is performed on each package
        individually as well.
        :param dbins: Number of dead bins after original bin (total - 1).

        :warning.warn: There are no shots left in the package. No deadtime
            correction can be applied.
        """
        self.applied_filters["dead_time_corr"] = [True, dbins]

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

        :raises ValueError: Invalid range for number of ions.
        :raises OSError: No package data available.
        """
        if max_ions < 1:
            raise ValueError("The maximum number of ions must be larger than 1.")
        if self.data_pkg is None:
            raise OSError("There is no packaged data. Please create packages first.")

        # update filter dictionary
        self.applied_filters["max_ions_per_pkg"] = [True, max_ions]

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

        :raises ValueError: Invalid range for number of ions.
        """
        if max_ions < 1:
            raise ValueError("The maximum number of ions must be >=1.")

        self.applied_filters["max_ions_per_shot"] = [True, max_ions]

        shots_rejected = np.where(self.ions_per_shot > max_ions)[0]

        self.apply_individual_shots_filter(shots_rejected)

    def filter_max_ions_per_time(self, max_ions: int, time_us: float) -> None:
        """Filter shots with >= max ions per time, i.e., due to ringing.

        :param max_ions: Maximum number of ions that is allowed within a time window.
        :param time_us: Width of the time window in microseconds (us)
        """
        self.applied_filters["max_ions_per_time"] = [True, max_ions, time_us]

        time_chan = int(time_us * self.us_to_chan)

        shots_to_check = np.where(self.ions_per_shot > max_ions)[0]

        if shots_to_check.shape == (0,):  # nothing needs to be done
            return

        all_tofs_filtered = self._all_tofs_filtered(shots_to_check)

        shot_mask = processor_utils.mask_filter_max_ions_per_time(
            self.ions_per_shot[shots_to_check], all_tofs_filtered, max_ions, time_chan
        )
        shots_rejected = shots_to_check[shot_mask]

        if shots_rejected.shape != (0,):
            self.apply_individual_shots_filter(shots_rejected)

    def filter_max_ions_per_tof_window(
        self, max_ions: int, tof_window: np.ndarray
    ) -> None:
        """Filer out maximum number of ions in a given ToF time window.

        :param max_ions: Maximum number of ions in the time window.
        :param tof_window: The time of flight window that the ions would have to be in.
            Array of start and stop time of flight (2 entries).

        :raises ValueError: Length of `tof_window` is wrong.
        """
        if len(tof_window) != 2:
            raise ValueError(
                "ToF window must be specified with two entries: the start "
                "and the stop time of the window."
            )

        if not isinstance(tof_window, np.ndarray):
            tof_window = np.array(tof_window)

        self.applied_filters["max_ions_per_tof_window"] = [
            True,
            max_ions,
            tof_window.tolist(),
        ]

        # convert to int to avoid weird float issues
        channel_window = np.array(tof_window * self.us_to_chan, dtype=int)

        shots_to_check = np.where(self.ions_per_shot > max_ions)[0]

        if shots_to_check.shape == (0,):  # nothing needs to be done
            return

        all_tofs_filtered = self._all_tofs_filtered(shots_to_check)

        shot_mask = processor_utils.mask_filter_max_ions_per_tof_window(
            self.ions_per_shot[shots_to_check],
            all_tofs_filtered,
            max_ions,
            channel_window,
        )
        shots_rejected = shots_to_check[shot_mask]

        if shots_rejected.shape != (0,):
            self.apply_individual_shots_filter(shots_rejected)

    def filter_pkg_peirce_countrate(self) -> None:
        """Filter out packages based on Peirce criterion for total count rate.

        Fixme: This needs more thinking and testing
        Now we are going to directly use all the integrals to get the sum of the counts,
        which we will then feed to the rejection routine. Maybe this can detect blasts.

        .. warning:: Running this more than once might lead to weird results. You have
            been warned!

        """  # noqa: D202

        self.applied_filters["pkg_peirce_rejection"] = True

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

    def integrals_calc(self, bg_corr=True) -> None:
        """Calculate integrals for data and packages (if present).

        The integrals to be set per peak are going to be set as an ndarray.
        Each row will contain one entry in the first column and its associated
        uncertainty in the second.

        :param bg_corr: If false, will never do background correction. Otherwise
            (default), background correction will be applied if available. This is a
            toggle to switch usage while leaving backgrounds defined.

        :raises ValueError: No integrals were set.
        :raises ValueError: No mass calibration has been applied.
        """

        def integral_windows(limits_tmp: np.array) -> List:
            """Create windows list for given limits.

            :param limits_tmp: Window limits.

            :return: List with all the windows that need to be calculated.
            """
            windows_tmp = []
            for low_lim, upp_lim in limits_tmp:
                windows_tmp.append(
                    np.where(np.logical_and(self.mass >= low_lim, self.mass <= upp_lim))
                )
            return windows_tmp

        if self._params_integrals is None:
            raise ValueError("No integrals were set.")
        if self.mass is None:
            raise ValueError("A mass calibration needs to be applied first.")

        names, limits = self.def_integrals

        windows = integral_windows(limits)

        self.integrals, self.integrals_pkg = processor_utils.integrals_summing(
            self.data, tuple(windows), self.data_pkg
        )

        # background correction
        if bg_corr and self._params_backgrounds is not None:
            names_bg, limits_bg = self.def_backgrounds

            windows_bgs = integral_windows(limits_bg)

            bgs, bgs_pkg = processor_utils.integrals_summing(
                self.data, tuple(windows_bgs), self.data_pkg
            )

            # determine channel lengths
            peak_ch_length = np.array([len(it) for it in windows])
            bgs_ch_length = np.array([len(it) for it in windows_bgs])

            # call the processor and do the background correction
            self.integrals, self.integrals_pkg = processor_utils.integrals_bg_corr(
                self.integrals,
                np.array(names),
                peak_ch_length,
                bgs,
                np.array(names_bg),
                bgs_ch_length,
                self.integrals_pkg,
                bgs_pkg,
            )

    def mass_calibration(self) -> None:
        r"""Perform a mass calibration on the data.

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

        :raises ValueError: No mass calibration set.
        """
        if self._params_mcal is None:
            raise ValueError("No mass calibration was set.")

        self.mass = processor_utils.mass_calibration(self.def_mcal, self.tof)

    def optimize_mcal(self, offset: float = None) -> None:
        """Take an existing mass calibration and finds maxima within a FWHM.

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

        :raises ValueError: Number of shots out of range
        """
        if shots < 1 or shots >= self.nof_shots:
            raise ValueError(
                f"Number of shots per package must be between 1 and "
                f"{self.nof_shots}, but is {shots}."
            )

        self.applied_filters["packages"] = [True, shots]

        self._pkg_size = shots

        self.data_pkg, self.nof_shots_pkg = processor_utils.create_packages(
            shots, self.ions_to_tof_map, self.all_tofs
        )

    def run_macro(self, fname: Path) -> None:
        """Run your own macro.

        The macro will be imported here and then run. Details on how to write a macro
        can be found in the documentation.

        :param fname: Filename to the macro.
        """
        self.applied_filters["macro"] = [True, str(fname.absolute())]

        pyfile = fname.with_suffix("").name
        file_path = fname.absolute().parent
        print("fname")
        print(fname)

        sys.path.append(str(file_path))

        exec(f"import {pyfile}") in globals(), locals()  # noqa: S102
        macro = vars()[pyfile]
        macro.calc(self)

        sys.path.remove(str(file_path))

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
        self.ions_per_shot = self.crd.ions_per_shot
        self.ions_to_tof_map = self.crd.ions_to_tof_map
        self.all_tofs = self.crd.all_tofs
        self.nof_shots = self.crd.nof_shots

        # set up ToF
        self.tof = (
            np.arange(bin_start, bin_end + 1, 1) * bin_length / 1e6 + delta_t * 1e6
        )
        self.data = processor_utils.sort_data_into_spectrum(
            self.all_tofs, self.all_tofs.min(), self.all_tofs.max()
        )

        # set constants
        self.us_to_chan = 1e6 / self.crd.header["binLength"]  # convert us to bins

        if self.tof.shape != self.data.shape:
            warnings.warn(
                "Bin ranges in CRD file were of bad length. Creating ToF "
                "array without CRD header input."
            )
            self.tof = np.arange(len(self.data)) * bin_length / 1e6

    def spectrum_part(self, rng: Union[Tuple[Any], List[Any]]) -> None:
        """Create ToF for a part of the spectra.

        Select part of the shot range. These ranges will be 1 indexed! Always start
        with the full data range.

        :param rng: Shot range, either as a tuple (from, to) or as a tuple of multiple
            ((from1, to1), (from2, to2), ...).

        :raises ValueError: Ranges are not defined from, to where from < to
        :raises ValueError: Tuples are not mutually exclusive.
        """
        self.applied_filters["spectrum_part"] = [True, rng]

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
                all_tofs_filtered, self.crd.all_tofs.min(), self.crd.all_tofs.max()
            )

        # set back values
        self.ions_per_shot = self.ions_per_shot[ion_indexes]
        self.ions_to_tof_map = ions_to_tof_map_filtered
        self.all_tofs = all_tofs_filtered
        self.nof_shots = len(ion_indexes)

    # PRIVATE ROUTINES #

    def _all_tofs_filtered(self, shots_indexes: np.array) -> np.array:
        """Filter time of flights based on the indexes of the shots.

        This function is heavily used in filters.

        :param shots_indexes: Array with indexes of the shots.

        :return: All time of flight bins for the given shots
        """
        rng_all_tofs = self.ions_to_tof_map[shots_indexes]
        tof_indexes = processor_utils.multi_range_indexes(rng_all_tofs)
        return self.all_tofs[tof_indexes]
