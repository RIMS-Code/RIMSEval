"""Utilities for CRD processors. Mostly methods that can be jitted."""

from typing import Tuple, Union

from numba import njit
import numpy as np
from scipy import optimize

from .utilities import fitting, utils


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

    params = optimize.leastsq(fitting.residuals_gaussian, coeffs, args=(ydata, xdata))
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
                    int_value + bg_norm_unc ** 2
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
    params_fit = optimize.curve_fit(calc_mass, params[:, 0], params[:, 1], p0=(t0, b))

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
