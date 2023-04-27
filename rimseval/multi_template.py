"""Holds the class template for the MultiEvaluator and MultiFileProcessor classes."""

import gc
from pathlib import Path
from typing import Any, List

import rimseval
from rimseval.evaluator import IntegralEvaluator
from rimseval.processor import CRDFileProcessor


class MultiTemplate:
    """This class holds the template for the multi processor and evaluator classes.

    All implemented routines are generalized in here, routines that need to be
    adopted but are required will raise a `NotImplementedError`.
    """

    def __init__(self, file_paths: List[Path]):
        """Initialize the multiple file processor.

        :param file_paths: List of pathes to the files to read in.

        :raise TypeError: Class that is used for initialization has no loader defined.
        """
        self._num_of_files = len(file_paths)
        self.file_paths = file_paths

        self._files = None

        # define the loader, i.e., how to load files dependent on daughter class
        self._loader = None
        if self.__class__ == rimseval.multi_proc.MultiFileProcessor:
            self._loader = CRDFileProcessor
        elif self.__class__ == rimseval.multi_eval.IntegralEvaluator:
            self._loader = IntegralEvaluator
        else:
            raise TypeError(
                f"{self.__class__} can not be initialized, no loader defined."
            )

    @property
    def files(self) -> List[Any]:
        """Return a list of files.

        If the files are not opened, it will open and read them.

        :return: List of Evaluator or Processor instances with files opened
        """
        if self._files is None:
            self.open_files()
        return self._files

    @property
    def num_of_files(self) -> int:
        """Get the number of files that are in the multiprocessor."""
        return self._num_of_files

    def close_files(self) -> None:
        """Destroys the files and frees the memory."""
        del self._files
        gc.collect()  # garbage collector
        self._files = None
        self._num_of_files = 0

    def close_selected_files(self, ids: List[int], main_id: int = None) -> int:
        """Close selected files.

        Close the ided files and free the memory. If the main_id is given, the program
        will return the new ID of the main file in case it got changed. If the main
        file is gone or no main file was provided, zero is returned.

        :param ids: List of file IDs, i.e., where they are in ``self.files``.
        :param main_id: ID of the main file, an updated ID will be returned if main
            file is present, otherwise zero will be returned.

        :return: New ID of main file if present or given. Otherwise, return zero.
        """
        main_file = None
        if main_id is not None:
            main_file = self._files[main_id]

        ids.sort(reverse=True)
        for id in ids:
            del self._files[id]
        gc.collect()

        self._num_of_files = len(self._files)

        if main_id is None:
            return 0
        elif main_file not in self._files:
            return 0
        else:
            return self._files.index(main_file)

    def open_additional_files(self, fnames: List[Path]) -> None:
        """Open additional files to the ones already opened.

        Files will be appended to the list, no sorting.

        :param fnames: List of filenames for the additional files to be opened.
        """
        for fname in fnames:
            file_to_add = self._loader(fname)

            self._files.append(file_to_add)

        self._num_of_files = len(self._files)

    def open_files(self) -> None:
        """Open the files and store them in the list."""
        files = [self._loader(fname) for fname in self.file_paths]
        self._files = files
        self._num_of_files = len(files)
