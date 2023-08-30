"""Test list file utilities."""

import numpy as np

import rimseval.data_io.lst_utils as utl


def test_ascii_to_ndarray_ascii_1a_no_tag(init_lst_proc):
    """Convert ASCII_1A, data to numpy array, w/o tag."""
    data_list = [
        "0001000e7474",
        "0002000e7474",
        "0002000e7473",  # wrong channel
        "0003000e7474",
        "000000000000",  # zero
    ]
    fmt = init_lst_proc.ASCIIFormat.ASC_1A
    channel = 4
    expected_return = np.array([[1, 59207], [2, 59207], [3, 59207]], dtype=np.uint32)

    ret_data, ret_tag, _ = utl.ascii_to_ndarray(data_list, fmt, channel)
    np.testing.assert_equal(ret_data, expected_return)
    assert ret_tag is None


def test_ascii_to_ndarray_ascii_1a_tag(init_lst_proc):
    """Convert ASCII_1A, data to numpy array, with tag."""
    data_list = [
        "0001000e7474",
        "0002000e7474",
        "0002000e7473",  # tag
        "0003000e7474",
        "000000000000",  # zero
    ]
    fmt = init_lst_proc.ASCIIFormat.ASC_1A
    channel = 4
    tag = 3
    expected_data = np.array([[1, 59207], [2, 59207], [3, 59207]], dtype=np.uint32)
    expected_tag = np.array([2], dtype=np.uint32)

    ret_data, ret_tag, _ = utl.ascii_to_ndarray(data_list, fmt, channel, tag)

    np.testing.assert_equal(ret_data, expected_data)
    np.testing.assert_equal(ret_tag, expected_tag)


def test_ascii_to_ndarray_ascii_1a_no_tag_other_channel(init_lst_proc):
    """Convert ASCII_1A, data to numpy array, w/o tag."""
    data_list = [
        "0001000e7474",
        "0002000e7474",
        "0002000e7473",  # wrong channel
        "0003000e7474",
        "000000000000",  # zero
    ]
    fmt = init_lst_proc.ASCIIFormat.ASC_1A
    other_channels_exp = [4]
    channel = 3

    _, _, other_channels_ret = utl.ascii_to_ndarray(data_list, fmt, channel)
    assert other_channels_ret == other_channels_exp


def test_get_sweep_time_ascii():
    """Transfer binary number to base 10 int based on boundaries."""
    bin_str = "1000101101"
    sweep_boundaries = (0, 5)
    time_boundaries = (5, 10)
    sweep_exp = int(bin_str[sweep_boundaries[0] : sweep_boundaries[1]], 2)
    time_exp = int(bin_str[time_boundaries[0] : time_boundaries[1]], 2)

    sweep_ret, time_ret = utl.get_sweep_time_ascii(
        bin_str, sweep_boundaries, time_boundaries
    )
    assert sweep_ret == sweep_exp
    assert time_ret == time_exp


def test_separate_signal_with_tag():
    """Separate a signal into tagged and untagged data."""
    signal_all = np.array([[1, 9207], [2, 5207], [3, 59207]], dtype=np.uint32)
    tag_location = np.array([2], dtype=np.uint32)

    untagged_exp = np.array([[1, 9207], [3, 59207]], dtype=np.uint32)
    tagged_exp = np.array([[2, 5207]], dtype=np.uint32)

    untagged_rec, tagged_rec = utl.separate_signal_with_tag(signal_all, tag_location)

    np.testing.assert_equal(untagged_rec, untagged_exp)
    np.testing.assert_equal(tagged_rec, tagged_exp)


def test_transfer_lst_to_crd_data():
    """Transfer list data to CRD data."""
    max_sweep = 1023
    data_in = np.array(
        [
            [1, 500],
            [2, 265],
            [1, 600],
            [5, 700],
            [500, 5000],
            [550, 2],
            [501, 55],
            [800, 50],
            [1023, 200],
            [2, 100],
            [1023, 13],
            [5, 5000],
        ],
        dtype=np.uint32,
    )
    ion_range = 1000

    # expected shots array
    shots_array_exp = np.zeros(1023 + 5, dtype=np.uint32)
    shots_array_exp[0] = 2
    shots_array_exp[1] = 1
    shots_array_exp[4] = 1
    shots_array_exp[500] = 1
    shots_array_exp[549] = 1
    shots_array_exp[799] = 1
    shots_array_exp[1022] = 2
    shots_array_exp[1024] = 1

    # expected ions array
    ions_array_exp = np.array(
        [500, 600, 265, 700, 55, 2, 50, 200, 13, 100], dtype=np.uint32
    )

    shots_array_ret, ions_array_ret, out_of_range = utl.transfer_lst_to_crd_data(
        data_in, max_sweep, ion_range
    )

    np.testing.assert_equal(shots_array_ret, shots_array_exp)
    np.testing.assert_equal(ions_array_ret, ions_array_exp)
    assert out_of_range  # some ions are above ion range
