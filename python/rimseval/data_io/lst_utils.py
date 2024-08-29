"""This file contains utilities for processing list files."""

from typing import List, Tuple

from numba import njit
import numpy as np

from .lst_to_crd import LST2CRD


def ascii_to_ndarray(
    data_list: List[str], fmt: LST2CRD.ASCIIFormat, channel: int, tag: int = None
) -> Tuple[np.ndarray, np.ndarray, List]:
    """Turn ASCII LST data to a numpy array.

    Takes the whole data block and returns the data in a properly formatted numpy array.
    If channels other than the selected ones are available, these are written to a
    List and also returned as ``other_channels``.

    :param data_list: Data, directly supplied from the TDC block.
    :param fmt: Format of the data
    :param channel: Channel the data is in
    :param tag: Channel the tag is in, or None if no tag

    :return: Data, Tag Data, Other Channels available
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
    binary_width = fmt.value[0]
    boundaries = fmt.value[1]

    # counter for ions in the right channel
    ion_counter = 0

    tag_counter = 0

    other_channels = []

    # transform to bin number with correct length
    for data in data_list:
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
            elif tmp_channel != 0:
                if tmp_channel not in other_channels:
                    other_channels.append(tmp_channel)

    data_arr = data_arr[:ion_counter]
    if tag is not None:
        data_arr_tag = data_arr_tag[:tag_counter]

    return data_arr, data_arr_tag, other_channels


def get_sweep_time_ascii(
    data: str, sweep_b: Tuple[int, int], time_b: Tuple[int, int]
) -> Tuple[int, int]:
    """Get sweep and time from a given ASCII string.

    :param data: ASCII string
    :param sweep_b: Boundaries of sweep
    :param time_b: Boundaries of time

    :return: sweep, time
    """
    sweep_val = int(data[sweep_b[0] : sweep_b[1]], 2)
    time_val = int(data[time_b[0] : time_b[1]], 2)
    return sweep_val, time_val


@njit
def transfer_lst_to_crd_data(
    data_in: np.ndarray, max_sweep: int, ion_range: int
) -> Tuple[np.ndarray, np.ndarray, bool]:  # pragma: nocover
    """Transfer lst file specific data to the crd format.

    :param data_in: Array: One ion per line, two entries: sweep first (shot), then time
    :param max_sweep: the maximum sweep that can be represented by data resolution
    :param ion_range: Valid range of the data in multiples of 100ps bins

    :return: Array of how many ions are in each shot, Array of all arrival times of
        these ions, and a bool if there are any ions out of range
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
    ions_out_of_range = False
    for shot, ion in data_sort:
        if ion <= ion_range:
            shots[shot - 1] += 1  # zero versus one based
            ions[it] = ion
            it += 1
        else:
            ions_out_of_range = True

    return shots, ions, ions_out_of_range


@njit
def separate_signal_with_tag(
    data_arr: np.ndarray, tag_arr: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:  # pragma: nocover
    """Separate a dataset into a tagged and an untagged data set.

    :param data_arr: Array with all the data, shot, bins.
    :param tag_arr: 1d array with shots that are tagged.

    :return: Tagged and untagged data (split) in same format as ``data_arr``
    """
    tmp_untagged = np.empty_like(data_arr)
    tmp_tagged = np.empty_like(data_arr)

    cnt_untagged = 0
    cnt_tagged = 0

    for dat in data_arr:
        if dat[0] in tag_arr:  # tagged data
            tmp_tagged[cnt_tagged] = dat
            cnt_tagged += 1
        else:  # untagged data
            tmp_untagged[cnt_untagged] = dat
            cnt_untagged += 1

    data_untagged = tmp_untagged[:cnt_untagged]
    data_tagged = tmp_tagged[:cnt_tagged]

    return data_untagged, data_tagged
