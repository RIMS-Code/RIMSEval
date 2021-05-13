"""This file contains utilities for processing list files."""

from numba import njit
import numpy as np


def ascii_to_ndarray(data_list, fmt, channel, tag=None):
    """Turn ASCII LST data to a numpy array.

    Fixme: Might want to break this into two routines, with and without tag

    Takes the whole data block and returns the data in a properly formatted numpy array.
    For speed, using numba JITing.

    :param data_list: Data, directly supplied from the TDC block.
    :type data_list: List[str]
    :param fmt: Format of the data
    :type fmt: LST2CRD.DataFormat
    :param channel: Channel the data is in
    :type channel: int
    :param tag: Channel the tag is in, or None if no tag
    :type tag: int/None

    :return: Data, Tag Data
    :rtype: ndarray, ndarray/None

    :raises TypeError: Wrong data format encountered.
    """
    # prepare the data and list
    data_arr = np.empty((len(data_list), 2), dtype=np.uint32)
    data_arr_tag = None
    # initalize stuff for tags
    if tag is not None:
        data_arr_tag = np.empty(
            len(data_list), dtype=np.uint32
        )  # only sweep, not the channel

    # some helper variables for easy conversion
    binary_width = fmt.value[1]
    boundaries = fmt.value[2]

    # counter for ions in the right channel
    ion_counter = 0

    tag_counter = 0

    # transform to bin number with correct length
    for it, data in enumerate(data_list):
        if data != "":
            bin_tmp = f"{int(data, 16):{binary_width}b}".replace(" ", "0")
            # parse data
            tmp_channel = int(bin_tmp[boundaries[2][0] : boundaries[2][1]], 2)
            if tmp_channel == channel:
                swp_val, time_val = get_sweep_time_ascii(
                    bin_tmp, boundaries[0], boundaries[1]
                )
                data_arr[ion_counter][0] = swp_val
                data_arr[ion_counter][1] = time_val
                ion_counter += 1
            elif tmp_channel == tag:
                swp_val, _ = get_sweep_time_ascii(bin_tmp, boundaries[0], boundaries[1])
                data_arr_tag[tag_counter] = swp_val
                tag_counter += 1

    data_arr = data_arr[:ion_counter]
    if tag is not None:
        data_arr_tag = data_arr_tag[:tag_counter]
    return data_arr, data_arr_tag


def get_sweep_time_ascii(data, sweep_b, time_b):
    """Get sweep and time from a given ASCII string.

    :param data: ASCII string
    :type data: str
    :param sweep_b: Boundaries of sweep
    :type sweep_b: (int, int)
    :param time_b: Boundaries of time
    :type time_b: (int, int)

    :return: sweep, time
    :rtype: int, int
    """
    sweep_val = int(data[sweep_b[0] : sweep_b[1]], 2)
    time_val = int(data[time_b[0] : time_b[1]], 2)
    return sweep_val, time_val


@njit
def transfer_lst_to_crd_data(data_in, max_sweep, ion_range):
    """Transfer lst file specific data to the crd format.

    :param data: Array: One ion per line, two entries: sweep first (shot), then time
    :type data: ndarray
    :param max_sweep: the maximum sweep that can be represented by data resolution
    :type max_sweep: int
    :param ion_range: Valid range of the data in multiples of 100ps bins
    :type ion_range: int

    :return: Array of how many ions are in each shot, Array of all arrival times of
        these ions
    :rtype: ndarray, ndarray
    """
    data = data_in.copy()

    # go through and sort out max range issues
    threshold = max_sweep // 2
    multiplier = 0
    last_shot = data[0][0]
    for it in range(1, data.shape[0]):
        curr_shot = data[it][0]
        if (
            curr_shot < threshold < last_shot and last_shot - curr_shot > threshold
        ):  # need to flip forward
            multiplier += 1
        elif (
            last_shot < threshold < curr_shot and curr_shot - last_shot > threshold
        ):  # flip back
            multiplier -= 1
        # modify data
        adder = multiplier * max_sweep
        data[it][0] += adder
        last_shot = curr_shot

    # now sort the np array
    data_sort = data[data[:, 0].argsort()]

    # now create the shots and ions arrays and fill them
    shots = np.zeros(data_sort[:, 0].max(), dtype=np.uint32)
    ions = np.empty(
        len(data_sort[:, 1][np.where(data_sort[:, 1] <= ion_range)]), dtype=np.uint32
    )

    it = 0
    for shot, ion in data_sort:
        if ion <= ion_range:
            shots[shot - 1] += 1  # zero versus one based
            ions[it] = ion
            it += 1

    return shots, ions