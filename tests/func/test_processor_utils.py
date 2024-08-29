"""Tests for processors utilities."""

from hypothesis import given, strategies as st
import matplotlib.pyplot as plt
import numpy as np
import pytest

import rimseval
import rimseval.data_io.crd_utils as crdu
import rimseval.processor_utils as pu
import rimseval.utilities.delta


@pytest.mark.parametrize(
    "int_vals",
    [
        [None, False],
        [np.array([[2, 3]]), False],
        [np.array([[2, 3], [1, 2], [5, 7], [9.2, 10.2]]), False],
        [np.array([[2, 3], [5.2, 7.2], [7.0, 9.0], [10, 12]]), True],
        [np.array([[5, 6], [2, 9]]), True],
    ],
)
def test_check_peak_overlap(int_vals):
    """Check if peak definitions overlap."""
    peak_limits = int_vals[0]
    result_exp = int_vals[1]

    assert pu.check_peaks_overlap(peak_limits) == result_exp


def test_create_packages():
    """Create packages from data."""
    ions_per_shot = np.array([0, 0, 1, 0, 2, 0, 3, 2, 1, 4])
    all_tofs = np.array([20, 25, 70, 53, 68, 11, 54, 12, 68, 99, 65, 48, 7])
    bin_start = all_tofs.min()
    bin_end = all_tofs.max()
    len_data = bin_end - bin_start + 1
    tofs_mapper = crdu.shot_to_tof_mapper(ions_per_shot)
    assert ions_per_shot.sum() == len(all_tofs)
    assert all_tofs.max() < len_data + bin_start  # sanity checks for setup

    # packages expected
    pkg_length = 4
    nof_pkg = len(ions_per_shot) // pkg_length
    if len(ions_per_shot) % pkg_length > 0:
        nof_pkg += 1

    pkg_nof_shots_exp = np.zeros(nof_pkg) + pkg_length
    if (tmp := len(ions_per_shot) % pkg_length) > 0:
        pkg_nof_shots_exp[-1] = tmp

    pkg_data_exp = np.zeros((nof_pkg, len_data))

    for it, _ in enumerate(ions_per_shot):
        pkg_it = it // pkg_length
        mapper = tofs_mapper[it]
        tofs = all_tofs[mapper[0] : mapper[1]]
        for tof in tofs:
            pkg_data_exp[pkg_it][int(tof) - bin_start] += 1

    pkg_data_rec, pkg_nof_shots_rec = pu.create_packages(
        pkg_length, tofs_mapper, all_tofs
    )
    np.testing.assert_equal(pkg_nof_shots_rec, pkg_nof_shots_exp)
    np.testing.assert_equal(pkg_data_rec, pkg_data_exp)


def test_gaussian_fit():
    """Do a Gaussian feed on fixed-seed random data."""
    np.random.seed(42)
    mu, sigma = 0, 0.1
    sampl = np.random.normal(mu, sigma, 1000)

    ydat, bin_edges, _ = plt.hist(sampl, 25)
    xdat = (bin_edges[1:] + bin_edges[:-1]) / 2

    max_calc = pu.gaussian_fit_get_max(xdat, ydat)
    assert mu == pytest.approx(max_calc, abs=0.01)


def test_gaussian_fit_verbosity_warning(mocker):
    """Warn if verbosity level is set to >=2."""
    rimseval.VERBOSITY = 2
    xdat = np.arange(10)
    ydat = np.zeros_like(xdat)

    mock = mocker.patch("warnings.simplefilter")

    _ = pu.gaussian_fit_get_max(xdat, ydat)
    mock.assert_not_called()


def test_integrals_bg_corr():
    """Background correction for defined integrals."""
    integrals = np.array([[10, np.sqrt(10)], [40, np.sqrt(40)]])
    int_names = np.array(["28Si", "29Si"])
    int_ch = np.array([30, 40])
    bgs = np.array([[1, np.sqrt(1)], [2, np.sqrt(2)], [3, np.sqrt(3)]])
    bgs_names = np.array(["28Si", "28Si", "29Si"])
    bgs_ch = np.array([20, 10, 50])

    # manual calculations for expected values
    bgs_cnt = bgs[:, 0]
    bgs_norm = np.array(
        [(bgs_cnt[0] / bgs_ch[0] + bgs_cnt[1] / bgs_ch[1]) / 2, bgs_cnt[2] / bgs_ch[2]]
    )
    bgs_norm_unc = np.array(
        [
            (np.sqrt(bgs_cnt[0]) / bgs_ch[0] + np.sqrt(bgs_cnt[1]) / bgs_ch[1]) / 2,
            np.sqrt(bgs_cnt[2]) / bgs_ch[2],
        ]
    )
    integrals_corr = integrals[:, 0] - int_ch * bgs_norm
    integrals_corr_unc = np.sqrt(integrals[:, 0] + bgs_norm_unc**2)

    integrals_exp = np.array(
        [
            [integrals_corr[it], integrals_corr_unc[it]]
            for it in range(len(integrals_corr))
        ]
    )

    integrals_rec, integrals_pkg_rec = pu.integrals_bg_corr(
        integrals, int_names, int_ch, bgs, bgs_names, bgs_ch
    )
    np.testing.assert_equal(integrals_rec, integrals_exp)
    assert integrals_pkg_rec is None


def test_integrals_bg_corr_pkg():
    """Background correction for defined integrals with packages."""
    integrals = np.array([[10, np.sqrt(10)], [40, np.sqrt(40)]])
    integrals_pkg = np.array([integrals])
    int_names = np.array(["28Si", "29Si"])
    int_ch = np.array([30, 40])
    bgs = np.array([[1, np.sqrt(1)], [2, np.sqrt(2)], [3, np.sqrt(3)]])
    bgs_pkg = np.array([bgs])
    bgs_names = np.array(["28Si", "28Si", "29Si"])
    bgs_ch = np.array([20, 10, 50])

    # manual calculations for expected values
    bgs_cnt = bgs[:, 0]
    bgs_norm = np.array(
        [(bgs_cnt[0] / bgs_ch[0] + bgs_cnt[1] / bgs_ch[1]) / 2, bgs_cnt[2] / bgs_ch[2]]
    )
    bgs_norm_unc = np.array(
        [
            (np.sqrt(bgs_cnt[0]) / bgs_ch[0] + np.sqrt(bgs_cnt[1]) / bgs_ch[1]) / 2,
            np.sqrt(bgs_cnt[2]) / bgs_ch[2],
        ]
    )
    integrals_corr = integrals[:, 0] - int_ch * bgs_norm
    integrals_corr_unc = np.sqrt(integrals[:, 0] + bgs_norm_unc**2)

    integrals_exp = np.array(
        [
            [integrals_corr[it], integrals_corr_unc[it]]
            for it in range(len(integrals_corr))
        ]
    )

    # no packages
    integrals_rec, integrals_pkg_rec = pu.integrals_bg_corr(
        integrals, int_names, int_ch, bgs, bgs_names, bgs_ch
    )
    np.testing.assert_equal(integrals_rec, integrals_exp)
    assert integrals_pkg_rec is None

    # packages
    integrals_rec, integrals_pkg_rec = pu.integrals_bg_corr(
        integrals, int_names, int_ch, bgs, bgs_names, bgs_ch, integrals_pkg, bgs_pkg
    )
    np.testing.assert_equal(integrals_rec, integrals_exp)
    np.testing.assert_equal(integrals_pkg_rec[0], integrals_exp)
    assert len(integrals_pkg_rec) == 1


def test_integrals_summing():
    """Sum integrals for given data."""
    data = np.arange(100) * 2  # *2 such that index not equal to value
    window = (np.arange(10), np.arange(5) + 50)  # two windows

    integral_values = [np.sum(data[0:10]), np.sum(data[50:55])]
    integrals_exp = np.array([[it, np.sqrt(it)] for it in integral_values])

    integrals_rec, integrals_pkg_rec = pu.integrals_summing(data, window)
    np.testing.assert_equal(integrals_rec, integrals_exp)
    assert integrals_pkg_rec is None


def test_integrals_summing_pkg():
    """Sum integrals for given data and packages."""
    data = np.arange(100) * 2  # *2 such that index not equal to value
    data_pkg = np.array([data])
    window = (np.arange(10), np.arange(5) + 50)  # two windows

    integral_values = [np.sum(data[0:10]), np.sum(data[50:55])]
    integrals_exp = np.array([[it, np.sqrt(it)] for it in integral_values])

    integrals_rec, integrals_pkg_rec = pu.integrals_summing(data, window, data_pkg)
    np.testing.assert_equal(integrals_rec, integrals_exp)
    np.testing.assert_equal(integrals_pkg_rec[0], integrals_exp)


def test_mask_filter_max_ions_per_time():
    """Filter maximum number of ions per time window."""
    ions_per_shot = np.array([4, 0, 4, 5, 4])
    tofs = np.array(
        [1, 2, 3, 4] + [] + [1, 3, 5, 10] + [10, 15, 20, 25, 30] + [9, 10, 11, 15]
    )  # looks weird, but easier to stich together by hand
    max_ions = 3
    time_window_chan = 4

    exp_mask = np.array([0, 4])  # where conditions are met
    rec_mask = pu.mask_filter_max_ions_per_time(
        ions_per_shot, tofs, max_ions, time_window_chan
    )
    np.testing.assert_equal(exp_mask, rec_mask)


def test_mask_filter_max_ions_per_tof_window():
    """Filter maximum number of ions per time window."""
    ions_per_shot = np.array([4, 0, 4, 5, 4])
    tofs = np.array(
        [1, 2, 3, 4] + [] + [1, 3, 5, 10] + [10, 15, 20, 25, 30] + [9, 10, 11, 15]
    )  # looks weird, but easier to stich together by hand
    max_ions = 2
    time_window_chan = np.array([1, 5])

    exp_mask = np.array([0, 2])  # where conditions are met
    rec_mask = pu.mask_filter_max_ions_per_tof_window(
        ions_per_shot, tofs, max_ions, time_window_chan
    )
    np.testing.assert_equal(exp_mask, rec_mask)


def test_mass_calibration(mocker):
    """Perform a mass calibration, functionality tested in unit tests."""
    mock = mocker.patch("warnings.simplefilter")
    rimseval.VERBOSITY = 2

    params = np.array([[1, 1], [10, 10], [20, 28.35]])
    tofs = np.arange(0, 20)

    mass, params_fit = pu.mass_calibration(params, tofs, return_params=True)

    assert tofs.shape == mass.shape
    assert params_fit is not None
    mock.assert_not_called()


def test_mass_to_tof():
    """Convert mass to time of flight."""
    m = 42.0
    tm0 = 13.0
    const = 0.7

    result_exp = np.sqrt(m) * const + tm0

    assert result_exp == pu.mass_to_tof(m, tm0, const)


def test_multi_range_indexes():
    """Create multi-range indexes for view on data."""
    ranges = np.array([[0, 2], [3, 6], [0, 0], [15, 22]])
    indexes_exp = np.array([0, 1, 3, 4, 5, 15, 16, 17, 18, 19, 20, 21], dtype=int)

    indexes_rec = pu.multi_range_indexes(ranges)
    np.testing.assert_equal(indexes_rec, indexes_exp)
    assert indexes_rec.dtype == int


def test_multi_range_indexes_empty():
    """Return empty index array if all ranges of zero length."""
    ranges = np.array([[0, 0], [0, 0]])
    indexes_exp = np.array([])
    np.testing.assert_equal(pu.multi_range_indexes(ranges), indexes_exp)


def test_peak_background_overlap():
    """Remove overlaps of peaks and backgrounds, if they exist."""
    def_integrals = (
        ["p1", "p2", "p3", "p4"],
        np.array([[10.0, 11.0], [15.0, 16.0], [17.0, 18.0], [30, 31.0]]),
    )
    def_bg = (
        ["p1", "p2", "p2", "p2", "p3", "p4", "p4", "p4"],
        np.array(
            [
                [9.0, 12.0],
                [14.0, 15.0],
                [14.0, 15.5],
                [15.7, 17.0],
                [16.2, 17.3],
                [17.3, 31],
                [30.4, 30.9],
                [31.0, 33.0],
            ]
        ),
    )

    def_bg_self_corr = (
        ["p1", "p1", "p2", "p2", "p2", "p3", "p4", "p4"],
        np.array(
            [
                [9.0, 10.0],
                [11.0, 12.0],
                [14.0, 15.0],
                [14.0, 15.0],
                [16, 17.0],
                [16.2, 17.0],
                [17.3, 30.0],
                [31.0, 33.0],
            ]
        ),
    )
    def_bg_all_corr = (
        ["p1", "p1", "p2", "p2", "p2", "p3", "p4", "p4"],
        np.array(
            [
                [9.0, 10.0],
                [11.0, 12.0],
                [14.0, 15.0],
                [14.0, 15.0],
                [16, 17.0],
                [16.2, 17.0],
                [18, 30],
                [31.0, 33.0],
            ]
        ),
    )

    rec_self_corr, rec_all_corr = pu.peak_background_overlap(def_integrals, def_bg)

    assert rec_self_corr[0] == def_bg_self_corr[0]
    np.testing.assert_allclose(rec_self_corr[1], def_bg_self_corr[1])

    assert rec_all_corr[0] == def_bg_all_corr[0]
    np.testing.assert_allclose(rec_all_corr[1], def_bg_all_corr[1])


@given(bg=st.lists(st.floats(min_value=1, max_value=10), min_size=2, max_size=2))
def test_peak_background_overlap__excluded(bg):
    """Test with hypothesis that we don't have overlap."""
    if bg[0] < bg[1]:
        bg_low = bg[0]
        bg_high = bg[1]
    else:
        bg_low = bg[1]
        bg_high = bg[0]

    def_integral = (["p1", "p2", "p3"], np.array([[2, 4], [5, 7], [8, 9.5]]))
    def_bgs = (["p1"], np.array([[bg_low, bg_high]]))

    _, def_bgs_all_corr = pu.peak_background_overlap(def_integral, def_bgs)
    bgs = def_bgs_all_corr[1]
    for bg in bgs:
        # now we create a boolean mask for the bgs to compare if below or above
        bool_low = bg < def_integral[1]
        bool_high = bg > def_integral[1]

        # summing horizontally results in 0 (both false) or 2 (both true).
        assert not any(np.sum(bool_low, axis=1) % 2)
        assert not any(np.sum(bool_high, axis=1) % 2)


def test_peak_background_overlap_all_excluded():
    """Ensure that correct value is returned if all peaks are excluded."""
    def_integral = (["p1"], np.array([[2, 4]]))
    def_bgs = (["p1"], np.array([[2.5, 3.5]]))

    def_bgs_self_corr, def_bgs_all_corr = pu.peak_background_overlap(
        def_integral, def_bgs
    )
    assert not def_bgs_self_corr[0]
    assert not def_bgs_self_corr[1]
    assert not def_bgs_all_corr[0]
    assert not def_bgs_all_corr[1]


def test_sort_data_into_spectrum():
    """Sort some small data into a spectrum."""
    ions = np.array([0, 1, 5, 10, 9])
    assert ions.min() == 0  # requirement for this simple test
    spectrum_exp = np.zeros(ions.max() - ions.min() + 1)
    for ion in ions:
        spectrum_exp[ion] += 1
    spectrum_rec = pu.sort_data_into_spectrum(ions, ions.min(), ions.max())
    np.testing.assert_equal(spectrum_rec, spectrum_exp)
