"""Class to turn a list file to a CRD file."""

from datetime import datetime
from enum import Enum
from pathlib import Path
import struct
import warnings

import numpy as np

from . import crd_utils
from . import lst_utils


class LST2CRD:
    """Convert list files to CRD files.

    Example:
        >>> from pathlib import Path
        >>> from rimseval.data_io import LST2CRD
        >>> file = Path("path/to/file.lst")
        >>> lst = LST2CRD(file_name=file, channel_data=1, tag_data=None)
        >>> lst.read_list_file()
        >>> lst.write_crd()
    """

    class BinWidthTDC(Enum):
        """Bin width defined by instrument.

        These are only FASTComTec instruments. The name of each entry is equal to
        the identifier that can be found in a datafile (lst).
        The entries of the enum are as following:

        - binwidth in ps
        """

        MPA4A = 100
        MCS8A = 80

    class ASCIIFormat(Enum):
        """Available formats for this routine that are already implemented.

        Various formats that are implemented when dealing with ASCII data.
        The value is composed of a tuple of 2 entries.

         - 0: entry: width of the binary number (binary_width)
         - 1: Tuple of tuples with start, stop on where to read
           0: sweep - 1: time - 2: channel
        """

        ASC_1A = (48, ((0, 16), (16, 44), (45, 48)))
        ASC_9 = (64, ((1, 21), (21, 59), (60, 64)))

    class DATFormat(Enum):
        """Available formats (time_patch) for binary data.

        Various binary data formats are incorporated. Value is compmosed of 2 entries:

          - 0: Data length in bytes
          - 1: Encoding of the binary value to read with struct.unpack()
          - 2: Tuple, Where in the decoded list are: 0: sweep - 1: time - 2: channel
        """

        DAT_9 = (8, "<")

    def __init__(
        self,
        file_name: Path = None,
        channel_data: int = None,
        channel_tag: int = None,
    ) -> None:
        """Initialize the LST2CRD class.

        :param file_name: File name and path of file to be read.
        :param channel_data: Number of channel the data are in.
        :param channel_tag: Number of channel the tag is in, None for no tag.
        """
        # set the default values
        self._channel_data = channel_data
        self._channel_tag = channel_tag
        self._file_name = file_name

        # initialize values for future use
        self._binary_file = False  # is this a binary file?
        self._file_info = {}  # dictionary with parsed header info
        self._data_format = None  # format of the data. auto set on reading
        self._data_signal = None  # data for signal (total)
        self._tags = None  # array for tagged shots
        self._other_channels = None  # List for other channels that have counts

    # PROPERTIES #

    @property
    def channel_data(self) -> int:
        """Get / set the channel number of the data.

        :return: Channel number of data

        :raises TypeError: Channel number is not an integer.
        """  # noqa: DAR402
        return self._channel_data

    @channel_data.setter
    def channel_data(self, newval: int) -> None:
        if not isinstance(newval, int):
            raise TypeError("Channel number must be given as an integer.")
        self._channel_data = newval

    @property
    def channel_tag(self) -> int:
        """Get / set the channel number of the tag.

        :return: Channel number of tag

        :raises TypeError: Channel number is not an integer.
        """  # noqa: DAR402
        return self._channel_tag

    @channel_tag.setter
    def channel_tag(self, newval):
        if not isinstance(newval, int):
            raise TypeError("Channel number must be given as an integer.")
        self._channel_tag = newval

    @property
    def data_format(self) -> ASCIIFormat:
        """Select the data format to use to convert the LST file to CRD.

        :return: The currently chosen data format.

        :raises TypeError: Data format is not a DataFormat enum.
        """  # noqa: DAR402
        return self._data_format

    @data_format.setter
    def data_format(self, newval: ASCIIFormat) -> None:
        if not isinstance(newval, self.ASCIIFormat):
            raise TypeError(
                f"Your data format {newval} is not a valid type. "
                f"You must choose an object from the `DataFormat` instance."
            )
        self._data_format = newval

    @property
    def file_name(self) -> Path:
        """Get / set the file name for the file to be read / written.

        :return: The path and file name to the selected object.

        :raises TypeError: Path is not a `pathlib.Path` object.
        """  # noqa: DAR402
        return self._file_name

    @file_name.setter
    def file_name(self, newval: Path) -> None:
        if not isinstance(newval, Path):
            raise TypeError(
                f"Path must be a `pathlib.Path` object but is a {type(newval)}."
            )
        self._file_name = newval

    # METHODS #

    def read_list_file(self) -> None:
        """Read a list file specified in `self.file_name`.

        This routine sets the following parameters of the class:

        - self._file_data
        - self._tag_data (if a tag was selected)

        This routine sets the following information parameters in self._file_info:

        - "bin_width": Sets the binwidth in ps, depending on the instrument
        - "calfact": Calibration factor, to scale range to bins
        - "data_type": Sets the data type, 'ascii' for ASCII or 'dat' for binary, str
        - "shot_range": shot range
        - "timestamp": Time and date of file recording
        - "time_patch": Data format, as reported by Fastcomtec as time_patch. as str

        :raises ValueError: File name not provided.
        :raises ValueError: Channel for data not provided.
        :raises OSError: The Data Format is not available / could not be found in file.
        :raises NotImplementedError: The current data format is not (yet) implemented.
        """
        if self.file_name is None:
            raise ValueError("Please set a file name.")
        if self.channel_data is None:
            raise ValueError("Please set a number for the data channel.")

        # read in the file
        try:
            with self.file_name.open() as f:
                content = f.read().splitlines()
        except UnicodeDecodeError:  # we might have a binary file:
            with self.file_name.open("rb") as f:
                content = f.read().splitlines()
                self._binary_file = True

        # find the data and save it into a data_ascii list
        fnd_str = b"[DATA]" if self._binary_file else "[DATA]"
        index_start_data = content.index(fnd_str) + 1
        header = content[:index_start_data]
        if self._binary_file:
            header = [it.decode("utf-8") for it in header]
        data_ascii = content[index_start_data:]

        # set the bin width - in ps
        bin_width = None
        for it in self.BinWidthTDC:
            if it.name.lower() in header[0].lower():
                bin_width = it.value
                break
        if bin_width is None:
            raise NotImplementedError(
                f"The current data format cannot be identified. "
                f"The datafile header starts with: {header[0]}. "
                f"Available instruments are the following: "
                f"{[it.name for it in self.BinWidthTDC]}"
            )
        else:
            self._file_info["bin_width"] = bin_width

        # find calfact - in ns
        calfact = None
        for head in header:
            if head[0:8] == "calfact=":
                calfact = float(head.split("=")[1])
                self._file_info["calfact"] = calfact
                break

        # find the range
        for head in header:
            if head[0:5] == "range":
                ion_range = int(head.split("=")[1])
                mult_fact = calfact / (bin_width / 1000)  # get range in bin_width
                self._file_info["ion_range"] = int(ion_range * mult_fact)
                break

        # find the data type, ascii or binary
        data_type = None
        for head in header:
            if head[0:6] == "mpafmt":
                data_type = head.split("=")[1]
                self._file_info["data_type"] = data_type
                break
        if data_type is None:
            raise OSError("Could not find a data type in the list file!")

        # find the time patch
        for head in header:
            if head[0:10] == "time_patch":
                time_patch = head.split("=")[1]
                self._file_info["time_patch"] = time_patch

        # Find timestamp
        for head in header:
            tmp_date_str = "cmline0="
            if head[0 : len(tmp_date_str)] == tmp_date_str:
                datetime_str = head.replace(tmp_date_str, "").split()
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

        # find the data format or raise an error
        self.set_data_format()

        # currently, only ascii data are supported. error checking in set_data_format()
        data_sig, tags, other_channels = lst_utils.ascii_to_ndarray(
            data_ascii, self._data_format, self.channel_data, self.channel_tag
        )

        self._data_signal = data_sig
        self._tags = tags
        self._other_channels = other_channels

        # set number of ions
        self._file_info["no_ions"] = len(data_sig)

    def write_crd(self) -> None:
        """Write CRD file(s) from the data that are in the class.

        .. note:: A file must have been read first. Also, this routine doesn't actually
            write the crd file itself, but it handles the tags, etc., and then
            sources the actual writing task out.

        :raises ValueError: No data has been read in.
        :raises OSError: Data is empty.
        """
        if self._data_signal is None:
            raise ValueError("No data has been read in yet.")

        if self._data_signal.shape[0] == 0:
            raise OSError(
                f"There are no counts present in this file. Please double "
                f"check that you are using the correct channel for the signal. "
                f"The file seems to have counts in channels {self._other_channels}."
            )

        # calculate the maximum number of sweeps that can be recorded
        max_sweeps = pow(
            2, self.data_format.value[1][0][1] - self.data_format.value[1][0][0]
        )

        ions_out_of_range_warning = False
        if self._channel_tag is not None:  # we have tagged data
            # prepare the data
            untagged_data, tagged_data = lst_utils.separate_signal_with_tag(
                self._data_signal, self._tags
            )
            (
                untagged_shots,
                untagged_ions,
                untagged_ions_out_of_range,
            ) = lst_utils.transfer_lst_to_crd_data(
                untagged_data, max_sweeps, self._file_info["ion_range"]
            )
            (
                tagged_shots,
                tagged_ions,
                tagged_ions_out_of_range,
            ) = lst_utils.transfer_lst_to_crd_data(
                tagged_data, max_sweeps, self._file_info["ion_range"]
            )

            # raise warning later?
            if untagged_ions_out_of_range or tagged_ions_out_of_range:
                ions_out_of_range_warning = True

            # write crd
            fname_untagged = self.file_name.with_suffix(".untagged.crd")
            self._write_crd(fname_untagged, untagged_shots, untagged_ions)
            fname_tagged = self.file_name.with_suffix(".tagged.crd")
            self._write_crd(fname_tagged, tagged_shots, tagged_ions)

        else:  # untagged
            # prepare the data
            (
                data_shots,
                data_ions,
                ions_out_of_range,
            ) = lst_utils.transfer_lst_to_crd_data(
                self._data_signal, max_sweeps, self._file_info["ion_range"]
            )

            # raise warning later?
            if ions_out_of_range:
                ions_out_of_range_warning = True

            # write crd
            fname = self.file_name.with_suffix(".crd")
            self._write_crd(fname, data_shots, data_ions)

        if ions_out_of_range_warning:
            warnings.warn(
                "The lst file contained ions that were outside the allowed "
                "range. These ions were not written to the crd file.",
                UserWarning,
                stacklevel=1,
            )

    def set_data_format(self):
        """Set the data format according to what is saved in file_info dictionary.

        The "data_type" and "time_patch" values must be present in the dictionary.
        Writes the information to itself, to the `_data_format` variable.

        :raises NotImplementedError: Binary data are currently not supported.
        :raises ValueError: Needs to be binary or ASCII data.
        """
        data_type = self._file_info["data_type"]
        time_patch = self._file_info["time_patch"]
        fmt_str = f"{data_type.upper()}_{time_patch.upper()}"
        if data_type.lower() == "asc":
            fmt = self.ASCIIFormat[fmt_str]
        elif data_type.lower() == "dat":
            raise NotImplementedError("Binary data is currently not supported.")
        else:
            raise ValueError(
                f"The data type {fmt_str} seems to be neither binary nor ASCII."
            )
        self._data_format = fmt

    def _write_crd(
        self, fname: Path, data_shots: np.ndarray, data_ions: np.ndarray
    ) -> None:
        """Write an actual CRD file as defined.

        Defaults of this writing are populated from the default dictionary in crd_utils.

        :param fname: File name to write to
        :param data_shots: Prepared array with all shots included.
        :param data_ions: Prepared array with all ions included.
        """
        default = crd_utils.CURRENT_DEFAULTS

        # prepare date and time
        dt = self._file_info["timestamp"]
        dt_fmt = (
            f"{dt.year:04}:{dt.month:02}:{dt.day:02} "
            f"{dt.hour:02}:{dt.minute:02}:{dt.second:02}"
        )

        # get the new bin range
        bin_start = data_ions.min()
        bin_end = data_ions.max()

        with open(fname, "wb") as fout:
            # header
            fout.write(default["fileID"])
            fout.write(struct.pack("20s", bytes(dt_fmt, "utf-8")))
            fout.write(default["minVer"])
            fout.write(default["majVer"])
            fout.write(default["sizeOfHeaders"])
            fout.write(default["shotPattern"])
            fout.write(default["tofFormat"])
            fout.write(default["polarity"])
            fout.write(struct.pack("<I", self._file_info["bin_width"]))
            fout.write(struct.pack("<I", bin_start))
            fout.write(struct.pack("<I", bin_end))
            fout.write(default["xDim"])
            fout.write(default["yDim"])
            fout.write(default["shotsPerPixel"])
            fout.write(default["pixelPerScan"])
            fout.write(default["nOfScans"])
            fout.write(struct.pack("<I", len(data_shots)))  # number of shots
            fout.write(default["deltaT"])

            # write the data
            ion_cnt = 0
            for shot in data_shots:
                fout.write(struct.pack("<I", shot))
                for _ in range(shot):
                    fout.write(struct.pack("<I", data_ions[ion_cnt]))
                    ion_cnt += 1

            # EoF
            fout.write(default["eof"])
