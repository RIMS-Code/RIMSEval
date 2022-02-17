"""Tests for processors utilities."""

import numpy as np

import rimseval.processor_utils as pu
import rimseval.data_io.crd_utils as crdu


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

    for it, shot in enumerate(ions_per_shot):
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


def test_sort_data_into_spectrum():
    """Sort some small data into a spectrum."""
    ions = np.array([0, 1, 5, 10, 9])
    assert ions.min() == 0  # requirement for this simple test
    spectrum_exp = np.zeros(ions.max() - ions.min() + 1)
    for ion in ions:
        spectrum_exp[ion] += 1
    spectrum_rec = pu.sort_data_into_spectrum(ions, ions.min(), ions.max())
    np.testing.assert_equal(spectrum_rec, spectrum_exp)
