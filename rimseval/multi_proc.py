"""Process multiple CRD files, open them, handle individually, enable batch runs."""

import gc
from pathlib import Path
from typing import List, Union

from rimseval.processor import CRDFileProcessor


class MultiFileProcessor:
    """Class to process multiple CRD files at ones.

    Todo: Example
    """

    def __init__(self, crd_files: List[Path]):
        """Initialize the multiple file processor.

        :param crd_files: List of pathes to the CRD files.
        """
        self._num_of_files = len(crd_files)
        self.crd_files = crd_files

        self._files = None

    # PROPERTIES #

    @property
    def files(self) -> List[CRDFileProcessor]:
        """Return a list of files.

        If the files are not opened, it will open and read them.
        """
        if self._files is None:
            self.open_files()
        return self._files

    @property
    def num_of_files(self) -> int:
        """Get the number of files that are in the multiprocessor."""
        return self._num_of_files

    # METHODS #

    def apply_to_all(self, id: Union[int, CRDFileProcessor]):
        """Take the configuration for the ID file and apply it to all files."""
        if isinstance(id, int):
            crd_main = self.files[id]
        else:
            crd_main = id

        # todo: grab the config from main file and apply to the others

    def close_files(self) -> None:
        """Destroys the files and frees the memory."""
        del self._files
        gc.collect()  # garbage collector
        self._files = None

    def open_files(self) -> None:
        """Open the files and store them in the list."""
        files = [CRDFileProcessor(fname) for fname in self.crd_files]
        self._files = files

    def read_files(self) -> None:
        """Run spectrum_full on all CRD files."""
        for file in self.files:
            file.spectrum_full()
