"""Transform KORE's lst files and ini files to CRD files."""

from datetime import datetime
from pathlib import Path


class KORE2CRD:
    """Convert KORE list files to CRD files."""

    def __init__(self, file_name: Path):
        """Initialize the converter with a file name."""
        self.file_lst = file_name.with_suffix(".lst")
        self.file_ini = file_name.with_suffix(".ini")

        self._acq_datetime = None
        self._bin_width_ns = None
        self._first_bin = None
        self._last_bin = None
        self._num_shots = None

        # parse the ini file
        self._parse_ini_file()

    def _parse_ini_file(self):
        """Parse the ini file an set the required attributes of the class.

        Raises:
            FileNotFoundError: If the ini file does not exist.
        """
        if not self.file_ini.exists():
            raise FileNotFoundError(f"INI file {self.file_ini} does not exist.")

        with open(self.file_ini) as ini_file:
            for line in ini_file:
                if line.startswith("Time unit ns"):
                    self._bin_width_ns = float(line.split("=")[1].strip())
                elif line.startswith("First bin"):
                    self._first_bin = int(line.split("=")[1].strip())
                elif line.startswith("Last bin"):
                    self._last_bin = int(line.split("=")[1].strip())
                elif line.startswith("Number of cycles"):
                    self._num_shots = int(line.split("=")[1].strip())
                elif line.startswith("Acq start time"):
                    ts = line.split("=")[1].strip()
                    fmt = "%Y-%m-%d %H:%M:%S"
                    self._acq_datetime = datetime.strptime(ts, fmt)

        if not self._acq_datetime:
            raise ValueError("Acquisition date not found in the INI file.")

    @property
    def acq_datetime(self) -> str:
        """Return the acquisition date in CRD format.

        The date is formatted as 'YYYY:MM:DD hh:mm:ss'.
        """
        fmt = "%Y:%m:%d %H:%M:%S"
        return self._acq_datetime.strftime(fmt)

    @property
    def bin_width_ns(self) -> float:
        """Return the bin width in nanoseconds."""
        return self._bin_width_ns

    @property
    def first_bin(self) -> int:
        """Return the first bin number."""
        return self._first_bin

    @property
    def last_bin(self) -> int:
        """Return the last bin number."""
        return self._last_bin

    @property
    def num_shots(self) -> int:
        """Return the number of shots."""
        return self._num_shots
