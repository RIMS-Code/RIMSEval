"""Class to turn a list file to a CRD file."""

from datetime import datetime
from enum import Enum
import numpy as np
from pathlib import Path

from . import lst_utils


class LST2CRD:
    """Convert list files to CRD files.

    ToDo: Examples
    """

    class DataFormat(Enum):
        """Available formats for this routine that are already implemented.

        The name of the Data format consists of "ASCII" or "BIN" (self explanatory) and
        and time patch value that can be read from the
        The value is composed of a tuple of 3 entries. The first entry shows if it is
        ascii or binary. The second and third entries are as following:
        - For ASCII:
          - Second entry: width of the binary number (binary_width)
          - Third entry: Tuple of tuples with start, stop on where to read
            0: sweep - 1: time - 2: channel
        - For binary:
          - Second entry: Instructions on how to struct.unpack the binary
          - Position in this thus created list for 0: sweep - 1: time - 2: channel
        """

        ASCII_1A = ("ascii", 48, ((0, 16), (16, 44), (45, 48)))
        ASCII_9 = ("ascii", 64, ((1, 21), (21, 59), (60, 63)))

    def __init__(
        self,
        file_name=None,
        channel_data=None,
        channel_tag=None,
        data_format=DataFormat.ASCII_1A,
    ):
        """Initialize the LST2CRD class.

        :param file_name: File name and path of file to be read.
        :type file_name: pathlib.Path
        :param channel_data: Number of channel the data are in.
        :type channel_data: int
        :param channel_tag: Number of channel the tag is in, None for no tag.
        :type channel_tag: int
        :param data_format: Format the data is in.
        :type data_format: DataFormat instance (enum)
        """
        # set the default values
        self._channel_data = channel_data
        self._channel_tag = channel_tag
        self._file_name = file_name
        self._data_format = data_format

        # initialize values for future use
        self._file_info = {}  # dictionary with parsed header info
        self._data_signal = None  # data for signal
        self._data_tag = None  # data for tag

    # PROPERTIES #

    @property
    def channel_data(self):
        """Get / set the channel number of the data.

        :return: Channel number of data
        :rtype: int

        :raises TypeError: Channel number is not an integer.
        """
        return self._channel_data

    @channel_data.setter
    def channel_data(self, newval):
        if not isinstance(newval, int):
            raise TypeError("Channel number must be given as an integer.")
        self._channel_data = newval

    @property
    def channel_tag(self):
        """Get / set the channel number of the tag.

        :return: Channel number of tag
        :rtype: int

        :raises TypeError: Channel number is not an integer.
        """
        return self._channel_tag

    @channel_tag.setter
    def channel_tag(self, newval):
        if not isinstance(newval, int):
            raise TypeError("Channel number must be given as an integer.")
        self._channel_tag = newval

    @property
    def data_format(self):
        """Select the data format to use to convert the LST file to CRD.

        :return: The currently chosen data format.
        :rtype: DataFormat enum

        :raises TypeError: Data format is not a DataFormat enum.
        """
        return self._data_format

    @data_format.setter
    def data_format(self, newval):
        if not isinstance(newval, self.DataFormat):
            raise TypeError(
                f"Your data format {newval} is not a valid type. "
                f"You must choose an object from the `DataFormat` instance."
            )
        self._data_format = newval

    @property
    def file_name(self):
        """Get / set the file name for the file to be read / written.

        :return: The path and file name to the selected object.
        :rtype: `pathlib.Path`

        :raises TypeError: Path is not a `pathlib.Path` object.
        """
        return self._file_name

    @file_name.setter
    def file_name(self, newval):
        if not isinstance(newval, Path):
            raise TypeError(
                f"Path must be a `pathlib.Path` object but is a {type(newval)}."
            )
        self._file_name = newval

    # METHODS #

    def read_list_file(self):
        """Read a list file specified in `self.file_name`.

        This routine sets the following parameters of the class:
        - self._file_data
        - self._tag_data (if a tag was selected)

        This routine sets the following information parameters in self._file_info:
        - "range": shot range
        - "timestamp": Time and date of file recording
        - "no_ions": Number of ions in data

        :raises ValueError: File name not provided.
        :raises ValueError: Channel for data not provided
        :raises FileError: The Data Format is not available
        """
        if self.file_name is None:
            raise ValueError("Please set a file name.")
        if self.channel_data is None:
            raise ValueError("Please set a number for the data channel.")

        # read in the file
        with self.file_name.open() as f:
            content = f.read().split("\n")

        # find the data and save it into a data_ascii list
        index_start_data = content.index("[DATA]") + 1
        header = content[:index_start_data]
        data_ascii = content[index_start_data:]

        # Find date
        for it in range(len(header)):
            tmp_date_str = "cmline0="
            if header[it][0 : len(tmp_date_str)] == tmp_date_str:
                datetime_str = header[it].replace(tmp_date_str, "").split()
                date_tmp = datetime_str[0].split("/")  # month, day, year
                time_tmp = datetime_str[1].split(":")  # h, min, sec
                self._file_info["timestamp"] = datetime(
                    year=int(date_tmp[2]),
                    month=int(date_tmp[0]),
                    day=int(date_tmp[1]),
                    hour=int(time_tmp[0]),
                    minute=int(time_tmp[1]),
                    second=int(float(time_tmp[2])),
                )
                break

        # find the range
        for it in range(len(header)):
            if header[it][0:5] == "range":
                self._file_info["range"] = int(content[it].split("=")[1])
                break

        # find the data format or raise an error
        # todo

        data_sig, data_tag = lst_utils.ascii_to_ndarray(
            data_ascii, self.data_format, self.channel_data, self.channel_tag
        )
        self._data_signal = data_sig
        self._data_tag = data_tag

        # set number of ions
        self._file_info["no_ions"] = len(data_sig)

    def write_crd(self):
        """Write a CRD file from the data that is in the class.

        Note: A file must have been read first.

        :raises ValueError: No data has been read in.
        """
        if self._data_signal is None:
            raise ValueError("No data has been read in yet.")
