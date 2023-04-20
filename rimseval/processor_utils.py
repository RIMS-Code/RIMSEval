"""Utilities for CRD processors. Mostly methods that can be jitted."""

from typing import List, Tuple, Union
import warnings

from numba import njit
import numpy as np
from scipy import optimize

import rimseval
from .utilities import fitting, ini, utils


def check_peaks_overlap(peak_limits: np.ndarray) -> bool:
    """Check if peaks overlap and return the result.

    If any two peaks overlap, this will return `True`, otherwise `False`.

    :param peak_limits: Range of peaks, n x 2 array
    :return: Do the peaks overlap?
    """
    if peak_limits is None:
        return False
    if len(peak_limits) <= 1:  # no overlap is possible
        return False

    for it, lims in enumerate(peak_limits):
        other_peaks = np.delete(peak_limits, it, axis=0)
        mask_low = np.logical_and(
            lims[0] < other_peaks[:, 0], lims[1] <= other_peaks[:, 0]
        )
        mask_high = np.logical_and(
            lims[0] >= other_peaks[:, 1], lims[1] > other_peaks[:, 1]
        )
        mask = mask_low == mask_high
        if any(mask):  # some peaks overlap!
            return True

    # all good!
    return False


@njit
def create_packages(
    shots: int,
    tofs_mapper: np.ndarray,
    all_tofs: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray]:  # pragma: nocover
    """Create packages from data.

    :param shots: Number of shots per package
    :param tofs_mapper: mapper for ions_per_shot to tofs
    :param all_tofs: all arrival times / bins of ions

    :return: Data array where each row is a full spectrum, each line a package and a
        shot array on how many shots are there per pkg
    """
    bin_start = all_tofs.min()
    bin_end = all_tofs.max()

    nof_pkgs = len(tofs_mapper) // shots
    nof_shots_last_pkg = len(tofs_mapper) % shots
    if nof_shots_last_pkg > 0:
        nof_pkgs += 1

    # number of shots per package
    nof_shots_pkg = np.zeros(nof_pkgs) + shots
    if nof_shots_last_pkg != 0:
        nof_shots_pkg[-1] = nof_shots_last_pkg

    pkg_data = np.zeros((nof_pkgs, bin_end - bin_start + 1))
    for it, tof_map in enumerate(tofs_mapper):
        pkg_it = it // shots
        ions = all_tofs[tof_map[0] : tof_map[1]]
        for ion in ions:
            pkg_data[pkg_it][ion - bin_start] += 1

    return pkg_data, nof_shots_pkg


@njit
def dead_time_correction(
    data: np.ndarray, nof_shots: np.ndarray, dbins: int
) -> np.ndarray:  # pragma: nocover
    """Calculate dead time for a given spectrum.

    :param data: Data array, histogram in bins. 2D array (even for 1D data!)
    :param nof_shots: Number of shots, 1D array of data
    :param dbins: Number of dead bins after original bin (total - 1).

    :return: Dead time corrected data array.
    """
    dbins += 1  # to get total bins

    for lit in range(len(data)):
        ndash = np.zeros(len(data[lit]))  # initialize array to correct with later
        for it in range(len(ndash)):
            # create how far the sum should go
            if it < dbins:
                k = it
            else:
                k = dbins - 1
            # now calculate the sum
            sum_tmp = 0
            for jt in range(k):
                sum_tmp += data[lit][it - (jt + 1)]
            # calculate and add ndash
            ndash[it] = nof_shots[lit] - sum_tmp
        # correct the data
        for it in range(len(data[lit])):
            data[lit][it] = -nof_shots[lit] * np.log(1 - data[lit][it] / ndash[it])

    return data


def gaussian_fit_get_max(xdata: np.ndarray, ydata: np.ndarray) -> float:
    """Fit a Gaussian to xdata and ydata and return the xvalue of the peak.

    :param xdata: X-axis data
    :param ydata: Y-axis data

    :return: Maximum mof the peak on the x-axis
    """
    mu = xdata[ydata.argmax()]
    sigma = (xdata[-1] - xdata[0]) / 6  # guess
    height = ydata.max()

    coeffs = np.array([mu, sigma, height])

    # need some more error checking here to make sure there really is a peak

    with warnings.catch_warnings():
        if rimseval.VERBOSITY < 2:
            warnings.simplefilter("ignore", category=RuntimeWarning)
        params = optimize.leastsq(
            fitting.residuals_gaussian, coeffs, args=(ydata, xdata)
        )
    return params[0][0]


def integrals_bg_corr(
    integrals: np.ndarray,
    int_names: np.ndarray,
    int_ch: np.ndarray,
    bgs: np.ndarray,
    bgs_names: np.ndarray,
    bgs_ch: np.ndarray,
    int_pkg: np.ndarray = None,
    bgs_pkg: np.ndarray = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """Calculate background correction for integrals with given backgrounds.

    This takes the integrals that already exist and updates them by subtracting the
    backgrounds. Multiple backgrounds per integral can be defined. Important is that the
    names of the backgrounds are equal to the names of the integrals that they
    need to be subtracted from and that the names of the integrals are unique. The
    latter point is tested when defining the integrals.

    .. note:: This routine currently cannot be jitted since we are using an
        ``np.where`` statement. If required for speed, we can go an replace that
        statement. Most likely, this is plenty fast enough though.

    :param integrals: Integrals and uncertianties for all defined peaks.
    :param int_names: Name of the individual peaks. Must be unique values!
    :param int_ch: Number of channels for the whole peak width.
    :param bgs: Backgrounds and their uncertianties for all defined backgrounds.
    :param bgs_names: Peaks each backgrounds go with, can be multiple.
    :param bgs_ch: Number of channels for background width.
    :param int_pkg: Packaged integrals, if exist: otherwise provide ``None``
    :param bgs_pkg: Packaged backgrounds, if exist: otherwise provide ``None``

    :return: Corrected data and data_packages.
    """
    integrals_corr = np.zeros_like(integrals)
    if int_pkg is None:
        integrals_corr_pkg = None
    else:
        integrals_corr_pkg = np.zeros_like(int_pkg)

    def do_correction(
        integrals_in,
        int_names_in,
        int_ch_in,
        bgs_in,
        bgs_names_in,
        bgs_ch_in,
    ):
        """Run the correction, same variable names as outer scope."""
        integrals_corr_in = np.zeros_like(integrals_in)

        bgs_cnt = bgs_in[:, 0]  # get only the counts in the backgrounds, no uncertainty
        bgs_norm = bgs_cnt / bgs_ch_in
        bgs_norm_unc = np.sqrt(bgs_cnt) / bgs_ch_in

        for it in range(len(integrals_in)):
            int_value = integrals_in[it][0]
            bg_indexes = np.where(bgs_names_in == int_names_in[it])[0]
            if len(bg_indexes) > 0:  # background actually exists
                bg_norm = np.sum(bgs_norm[bg_indexes]) / len(bg_indexes)
                bg_norm_unc = np.sum(bgs_norm_unc[bg_indexes]) / len(bg_indexes)

                # write out the corrected values
                integrals_corr_in[it][0] = int_value - int_ch_in[it] * bg_norm
                integrals_corr_in[it][1] = np.sqrt(
                    int_value + bg_norm_unc**2
                )  # sqrt stat, assumes integral uncertainty is sqrt(integral)
            else:
                integrals_corr_in[it][0] = int_value
                integrals_corr_in[it][1] = np.sqrt(int_value)
        return integrals_corr_in

    # for integrals, not packages
    integrals_corr = do_correction(integrals, int_names, int_ch, bgs, bgs_names, bgs_ch)

    if integrals_corr_pkg is not None:
        for it_pkg in range(len(integrals_corr_pkg)):
            integrals_corr_pkg[it_pkg] = do_correction(
                int_pkg[it_pkg], int_names, int_ch, bgs_pkg[it_pkg], bgs_names, bgs_ch
            )

    return integrals_corr, integrals_corr_pkg


@njit
def integrals_summing(
    data: np.ndarray, windows: Tuple[np.ndarray], data_pkg: np.ndarray = None
) -> Tuple[np.ndarray, np.ndarray]:  # pragma: nocover
    """Sum up the integrals within the defined windows and return them.

    :param data: Data to be summed over.
    :param windows: The windows to be investigated (using numpy views)
    :param data_pkg: Package data (optional), if present.

    :return: integrals for data, integrals for data_pkg
    """
    integrals = np.zeros((len(windows), 2))

    # packages
    integrals_pkg = None
    if data_pkg is not None:
        integrals_pkg = np.zeros((data_pkg.shape[0], len(windows), 2))
        for ht in range(len(data_pkg)):
            for it, window in enumerate(windows):
                integrals_pkg[ht][it][0] = data_pkg[ht][window].sum()
                integrals_pkg[ht][it][1] = np.sqrt(integrals_pkg[ht][it][0])
        # define all integrals as the sum of the packages -> allow for filtering
        integrals[:, 0] = integrals_pkg.sum(axis=0)[:, 0]
        integrals[:, 1] = np.sqrt(np.sum(integrals_pkg[:, :, 1] ** 2, axis=0))
    else:
        for it, window in enumerate(windows):
            integrals[it][0] = data[window].sum()
            integrals[it][1] = np.sqrt(integrals[it][0])

    return integrals, integrals_pkg


@njit
def mask_filter_max_ions_per_time(
    ions_per_shot: np.array,
    tofs: np.array,
    max_ions: int,
    time_chan: int,
) -> np.array:  # pragma: nocover
    """Return indices where more than wanted shots are in a time window.

    :param ions_per_shot: How many ions are there per shot? Also defines the shape of
        the return array.
    :param tofs: All ToFs. Must be of length ions_per_shot.sum().
    :param max_ions: Maximum number of ions that are allowed in channel window.
    :param time_chan: Width of the window in channels (bins).

    :return: Boolean array of shape like ions_per_shot if more are in or not.
    """
    return_mask = np.zeros_like(ions_per_shot)  # initialize return mask

    start_ind = 0

    for it, ips in enumerate(ions_per_shot):
        end_ind = start_ind + ips
        tofs_shot = tofs[start_ind:end_ind]

        # run the filter
        for tof in tofs_shot:
            tofs_diff = np.abs(tofs_shot - tof)  # differences
            ions_in_window = len(
                np.where(tofs_diff <= time_chan)[0]
            )  # where diff small
            if ions_in_window > max_ions:  # comparison with max allowed
                return_mask[it] = 1
                break  # break this for loop: one true is enough to kick the shot

        start_ind = end_ind

    return np.where(return_mask == 1)[0]


@njit
def mask_filter_max_ions_per_tof_window(
    ions_per_shot: np.array,
    tofs: np.array,
    max_ions: int,
    tof_window: np.array,
) -> np.array:  # pragma: nocover
    """Return indices where more than wanted shots are in a given ToF window.

    :param ions_per_shot: How many ions are there per shot? Also defines the shape of
        the return array.
    :param tofs: All ToFs. Must be of length ions_per_shot.sum().
    :param max_ions: Maximum number of ions that are allowed in channel window.
    :param tof_window: Start and stop time of the ToF window in channel numbers.

    :return: Boolean array of shape like ions_per_shot if more are in or not.
    """
    return_mask = np.zeros_like(ions_per_shot)  # initialize return mask

    start_ind = 0

    for it, ips in enumerate(ions_per_shot):
        end_ind = start_ind + ips
        tofs_shot = tofs[start_ind:end_ind]

        if tofs_shot.shape[0] == 0:
            continue

        filtered_tofs = np.where(
            np.logical_and(tofs_shot >= tof_window[0], tofs_shot <= tof_window[1])
        )[0]
        nof_tofs_win = len(filtered_tofs)

        if nof_tofs_win > max_ions:
            return_mask[it] = 1

        start_ind = end_ind

    return np.where(return_mask == 1)[0]


def mass_calibration(
    params: np.array, tof: np.array, return_params: bool = False
) -> Union[np.array, Tuple[np.array]]:
    """Perform the mass calibration.

    :param params: Parameters for mass calibration.
    :param tof: Array with all the ToFs that need a mass equivalent.
    :param return_params: Return parameters as well? Defaults to False

    :return: Mass for given ToF.
    """
    # function to return mass with a given functional form
    calc_mass = tof_to_mass

    # calculate the initial guess for scipy fitting routine
    ch1 = params[0][0]
    m1 = params[0][1]
    ch2 = params[1][0]
    m2 = params[1][1]
    t0 = (ch1 * np.sqrt(m2) - ch2 * np.sqrt(m1)) / (np.sqrt(m2) - np.sqrt(m1))
    b = np.sqrt((ch1 - t0) ** 2.0 / m1)

    # fit the curve and store the parameters
    with warnings.catch_warnings():
        if rimseval.VERBOSITY < 2:
            warnings.simplefilter("ignore", category=RuntimeWarning)
        params_fit = optimize.curve_fit(
            calc_mass, params[:, 0], params[:, 1], p0=(t0, b)
        )

    mass = calc_mass(tof, params_fit[0][0], params_fit[0][1])

    if return_params:
        return mass, params_fit[0]
    else:
        return mass


def mass_to_tof(
    m: Union[np.ndarray, float], tm0: float, const: float
) -> Union[np.ndarray, float]:
    r"""Functional prescription to turn mass into ToF.

    Returns the ToF with the defined functional description for a mass calibration.
    Two parameters are required. The equation, with parameters defined as below,
    is as following:

    .. math:: t = \sqrt{m} \cdot \mathrm{const} + t_{0}

    :param m: mass
    :param tm0: parameter 1
    :param const: parameter 2

    :return: time
    """
    return np.sqrt(m) * const + tm0


def multi_range_indexes(rng: np.array) -> np.array:
    """Create multi range indexes.

    If a range is given as (from, to), the from will be included, while the to will
    be excluded.

    :param rng: Range, given as a numpy array of two entries each.

    :return: A 1D array with all the indexes spelled out. This allows for viewing
        numpy arrays for multiple windows.
    """
    num_shots = 0
    ind_tmp = []
    for rit in rng:
        if rit[0] != rit[1]:
            arranged_tmp = np.arange(rit[0], rit[1])
            ind_tmp.append(arranged_tmp)
            num_shots += len(arranged_tmp)

    indexes = np.zeros(num_shots, dtype=int)
    ind_b = 0
    for rit in ind_tmp:
        ind_e = ind_b + len(rit)
        indexes[ind_b:ind_e] = rit
        ind_b = ind_e
    return indexes


def peak_background_overlap(
    def_integrals: Tuple[List, np.ndarray], def_backgrounds: Tuple[List, np.ndarray]
) -> Tuple[Tuple[List, np.ndarray], Tuple[List, np.ndarray]]:
    """Check if the backgrounds and peaks overlap and correct if they do.

    Two types of overlap are possible: Overlap of the background with its own peak and
    overlap of the background with another peak. Two background definitions are
    returned: One where only the peak itself is cut out but other overlaps are kept and
    one where both are cut out. The user ultimately needs to specify which one
    gets applied.
    Backgrounds that are not present in integrals are deleted.

    :param def_integrals: Integral definitions
    :param def_backgrounds: Background definitions

    :return: Integral definitions corrected for peaks of bgs,
        Integral definitions corrected for all overlapping peaks
    """
    int_names, int_vals = def_integrals
    bg_names, bg_vals = def_backgrounds

    # delete backgrounds that are unused
    ind_to_delete = []
    for it, name in enumerate(bg_names):
        if name not in int_names:
            ind_to_delete.append(it)
    if len(ind_to_delete) == len(bg_names):
        return ([], np.empty(0)), ([], np.empty(0))
    else:  # remove existing
        bg_names = [ele for id, ele in enumerate(bg_names) if id not in ind_to_delete]
        bg_vals = np.delete(bg_vals, ind_to_delete, axis=0)

    # cut backgrounds such that they don't overlap with their own peak
    bg_names_self, bg_vals_self = [], []
    for it, bg_name in enumerate(bg_names):
        int_low, int_high = int_vals[int_names.index(bg_name)]
        bg_low, bg_high = bg_vals[it]
        if bg_low < int_low and bg_high > int_high:  # bg passes through peak:
            bg_names_self.append(bg_name)
            bg_vals_self.append(np.array([bg_low, int_low]))
            bg_names_self.append(bg_name)
            bg_vals_self.append(np.array([int_high, bg_high]))
        elif bg_low < int_low and bg_high > int_low:  # overlap on negative side
            bg_names_self.append(bg_name)
            bg_vals_self.append(np.array([bg_low, int_low]))
        elif bg_low < int_high and bg_high > int_high:  # overlap on positive side
            bg_names_self.append(bg_name)
            bg_vals_self.append(np.array([int_high, bg_high]))
        elif (bg_low < int_low and bg_high <= int_low) or (
            bg_low >= int_high and bg_high > int_high
        ):  # all good!
            bg_names_self.append(bg_name)
            bg_vals_self.append(np.array([bg_low, bg_high]))

    def_bg_self_corr = sort_backgrounds((bg_names_self, np.array(bg_vals_self)))

    # sorted integrals values:
    int_vals_sorted = int_vals[int_vals[:, 0].argsort()]

    # cut backgrounds such that they don't overlap with any peak
    bg_names_all, bg_vals_all = [], []
    for it, bg_name in enumerate(bg_names):
        bg_low, bg_high = bg_vals[it]
        # peak limits that are within bounds
        boundaries = int_vals_sorted[
            np.logical_and(int_vals_sorted > bg_low, int_vals_sorted < bg_high)
        ]
        if len(boundaries) == 0:  # no overlap
            test_mask = np.logical_and(
                bg_low >= int_vals_sorted[:, 0], bg_high <= int_vals_sorted[:, 1]
            )
            if not test_mask.any():  # if any of these are true, bg inside a peak
                bg_names_all.append(bg_name)
                bg_vals_all.append(bg_vals[it])
            continue
        # add the lower and upper boundaries if of bg, if necessary
        if bg_low < boundaries[0] and any(boundaries[0] == int_vals_sorted[:, 0]):
            boundaries = np.insert(boundaries, 0, bg_low)
        if bg_high > boundaries[-1] and any(boundaries[-1] == int_vals_sorted[:, 1]):
            boundaries = np.insert(boundaries, len(boundaries), bg_high)

        all_values = boundaries.reshape(int(len(boundaries) / 2), 2)

        for val in all_values:
            bg_names_all.append(bg_name)
            bg_vals_all.append(val)

    def_bg_all_corr = sort_backgrounds((bg_names_all, np.array(bg_vals_all)))

    return def_bg_self_corr, def_bg_all_corr


@njit
def remove_shots_from_filtered_packages_ind(
    shots_rejected: np.array,
    len_indexes: int,
    filtered_pkg_ind: np.array,
    pkg_size: int,
) -> Tuple[np.array, np.array]:  # pragma: nocover
    """Remove packages that were already filtered pkg from ion filter indexes.

    This routine is used to filter indexes in case a package filter has been applied,
    and now an ion / shot based filter needs to be applied.

    :param shots_rejected: Array of indexes with rejected shots.
    :param len_indexes: length of the indexes that the rejected shots are from.
    :param pkg_size: Size of the packages that were created.
    :param filtered_pkg_ind: Array with indexes of packages that have been filtered.

    :return: List of two Arrays with shots_indexes and shots_rejected, but filtered.
    """
    shots_indexes = utils.not_index(shots_rejected, len_indexes)
    for pkg_it in filtered_pkg_ind:
        lower_lim = pkg_it * pkg_size
        upper_lim = lower_lim + pkg_size
        shots_indexes = shots_indexes[
            np.where(
                np.logical_or(shots_indexes < lower_lim, shots_indexes >= upper_lim)
            )
        ]
        shots_rejected = shots_rejected[
            np.where(
                np.logical_or(shots_rejected < lower_lim, shots_rejected >= upper_lim)
            )
        ]
    return shots_indexes, shots_rejected


@njit
def remove_shots_from_packages(
    pkg_size: int,
    shots_rejected: np.array,
    ions_to_tof_map: np.array,
    all_tofs: np.array,
    data_pkg: np.array,
    nof_shots_pkg: np.array,
    pkg_filtered_ind: np.array = None,
) -> Tuple[np.array, np.array]:  # pragma: nocover
    """Remove shots from packages.

    This routine can take a list of individual ions and remove them from fully
    packaged data. In addition, it can also take a list of packages that, with respect
    to the raw data, have previously been removed. This is useful in order to filter
    individual shots from packages after packages themselves have been filtered.

    :param pkg_size: How many shots were grouped into a package originally?
    :param shots_rejected: Index array of the rejected shots.
    :param ions_to_tof_map: Mapping array where ions are in all_tof array.
    :param all_tofs: Array containing all the ToFs.
    :param data_pkg: Original data_pkg before filtering.
    :param nof_shots_pkg: Original nof_shots_pkg before filtering.
    :param pkg_filtered_ind: Indexes where the filtered packages are.

    :return: Filtered data_pkg and nof_shots_pkg arrays.
    """
    for shot_rej in shots_rejected:
        # calculate index of package
        pkg_ind = shot_rej // pkg_size

        if pkg_filtered_ind is not None:
            # need to subtract number of filtered packages up to here!
            pkg_rej_until = len(np.where(pkg_filtered_ind < pkg_ind))
            pkg_ind -= pkg_rej_until

        # get tofs to subtract from package and set up array with proper sizes
        rng_tofs = ions_to_tof_map[shot_rej]
        ions_to_sub = all_tofs[rng_tofs[0] : rng_tofs[1]]
        array_to_sub = np.zeros_like(data_pkg[pkg_ind])
        array_to_sub[ions_to_sub - all_tofs.min()] += 1

        data_pkg[pkg_ind] -= array_to_sub
        nof_shots_pkg[pkg_ind] -= 1

        return data_pkg, nof_shots_pkg


def sort_backgrounds(
    def_backgrounds: Tuple[List[str], np.ndarray]
) -> Tuple[List[str], np.ndarray]:
    """Sort a background list and return the sorted list.

    Sorting takes place first by Z, then by A, finally by start of the background area.
    Backgrounds given to this routine cannot be None.

    :param def_backgrounds: Background definition.
    :return: Sorted background definition.
    """
    names, values = def_backgrounds

    zz = []  # number of protons per isotope - first sort key
    for name in names:
        try:
            zz.append(ini.iso[name].z)
        except IndexError:
            zz.append(999)  # at the end of everything

    mass = []  # mass - second sort key
    for name in names:
        try:
            mass.append(ini.iso[name].mass)
        except IndexError:
            mass.append(999)

    sort_ind = sorted(
        np.arange(len(names)), key=lambda x: (zz[x], mass[x], values[x, 0])
    )

    if (sort_ind == np.arange(len(names))).all():  # already sorted
        return names, values

    names_sorted = list(np.array(names)[sort_ind])
    return names_sorted, values[sort_ind]


def sort_integrals(
    def_integrals: Tuple[List[str], np.ndarray]
) -> Tuple[Tuple[List[str], np.ndarray], Union[np.ndarray, None]]:
    """Sort integral definitions and return them plus the sorting array.

    The latter is required to also sort the already calculated integrals.
    Sorting takes place first by Z, then by A.

    :param def_integrals: Integral definitions.
    :return: Sorted integral definition, sorting array (None if already sorted).
    """
    names, values = def_integrals

    zz = []  # number of protons per isotope - first sort key
    for name in names:
        try:
            zz.append(ini.iso[name].z)
        except IndexError:
            zz.append(999)  # at the end of everything

    sort_ind = sorted(np.arange(len(names)), key=lambda x: (zz[x], values[x, 0]))

    if (sort_ind == np.arange(len(names))).all():  # already sorted
        return (names, values), None

    names_sorted = list(np.array(names)[sort_ind])
    return (names_sorted, values[sort_ind]), sort_ind


@njit
def sort_data_into_spectrum(
    ions: np.ndarray, bin_start: int, bin_end: int
) -> np.ndarray:  # pragma: nocover
    """Sort ion data in 1D array into an overall array and sum them up.

    :param ions: Arrival time of the ions - number of time bin
    :param bin_start: First bin of spectrum
    :param bin_end: Last bin of spectrum

    :return: arrival bins summed up
    """
    data = np.zeros(bin_end - bin_start + 1)
    for ion in ions:
        data[ion - bin_start] += 1
    return data


def tof_to_mass(
    tm: Union[np.ndarray, float], tm0: float, const: float
) -> Union[np.ndarray, float]:
    r"""Functional prescription to turn ToF into mass.

    Returns the mass with the defined functional description for a mass calibration.
    Two parameters are required. The equation, with parameters defined as below,
    is as following:

    .. math:: m = \left(\frac{tm - tm_{0}}{\mathrm{const}}\right)^{2}

    :param tm: time or channel
    :param tm0: parameter 1
    :param const: parameter 2

    :return: mass m
    """
    return ((tm - tm0) / const) ** 2
