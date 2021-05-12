"""Test list file utilities."""

import pytest
import numpy as np

import rimseval.lst_processor.lst_utils as utl


def test_ascii_to_ndarray_ascii_1a_no_tag(init_lst_proc):
    """Convert ASCII_1A, data to numpy array, w/o tag."""
    data_list = [
        "0001000e7474",
        "0002000e7474",
        "0002000e7473",  # wrong channel
        "0003000e7474",
        "000000000000",  # zero
    ]
    fmt = init_lst_proc.DataFormat.ASCII_1A
    channel = 4
    expected_return = np.array([[1, 59207], [2, 59207], [3, 59207]], dtype=np.uint32)

    ret_data, ret_tag = utl.ascii_to_ndarray(data_list, fmt, channel)
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
    fmt = init_lst_proc.DataFormat.ASCII_1A
    channel = 4
    tag = 3
    expected_data = np.array([[1, 59207], [2, 59207], [3, 59207]], dtype=np.uint32)
    expected_tag = np.array([2], dtype=np.uint32)

    ret_data, ret_tag = utl.ascii_to_ndarray(data_list, fmt, channel, tag)

    np.testing.assert_equal(ret_data, expected_data)
    np.testing.assert_equal(ret_tag, expected_tag)


def test_transfer_lst_to_crd_data():
    data_in = np.array(
        [[1, 500], [2, 265], [1, 600], [5, 700], [1023, 200], [2, 100], [5, 5000]],
        dtype=np.uint32,
    )
    max_sweep = 1023
    range = 1000

    # expected shots array
    shots_array_exp = np.zeros(1023 + 5, dtype=np.uint32)
    shots_array_exp[0] = 2
    shots_array_exp[1] = 1
    shots_array_exp[4] = 1
    shots_array_exp[1022] = 1
    shots_array_exp[1024] = 1

    # expected ions array
    ions_array_exp = np.array([500, 600, 265, 700, 200, 100], dtype=np.uint32)

    shots_array_ret, ions_array_ret = utl.transfer_lst_to_crd_data(
        data_in, max_sweep, range
    )

    np.testing.assert_equal(shots_array_ret, shots_array_exp)
    np.testing.assert_equal(ions_array_ret, ions_array_exp)
