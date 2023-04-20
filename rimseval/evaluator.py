"""Evaluation class for integral files.


"""

from enum import Enum

from pathlib import Path
from typing import Dict, List, Tuple, Union

import numpy as np

from rimseval import data_io


class IntegralEvaluator:
    """Evaluate RIMS integrals.

    This class facilitates the evaluation of RIMS integrals. It can be used to:
    - Combine multiple measurements of the same sample / standard.
    - Standard normalize the sample measurements.
    - Full error propagation and correlated uncertainty calculations.
    - Export the data to csv files.
    - Feature to save and reload the evaluation.
    - Export the data to a LaTeX table.

    Example:
        >>> # todo
    """

    def __init__(self, integrals_in: Union[Path, List] = None):
        """Initialize the IntegralEvaluator class.

        :param integrals_in: Path to a directory containing integral files or a list of
            integral parameters. The file will be read with the
            ``rimseval.data_io.integrals.load`` method.
            If a list is given, it should contain the following entries:
                1. CRD file name (equiv to ``crd.name``)
                2. Timestamp (equiv to ``crd.timestamp``)
                3. Peak names (equiv to ``crd.def_integrals[0]``)
                4. Integrals (equiv to ``crd.integrals``)
            If `None` is given, the class is initialized empty (mainly used for loading
            from file).
        """
        self._name = None
        self._peaks = None
        self._integral_dict = {}
        self._timestamp_dict = {}

        if integrals_in is not None:
            self.add_integral(integrals_in)

    # PROPERTIES #

    @property
    def integrals(self) -> Tuple[List, np.ndarray]:
        """Return the integrals and their errors.

        Integrals are summed up and the error are propagated as the square root of the
        sum of the squared errors.

        :return: Tuple of peak names and integrals.
        """
        integrals = np.zeros((len(self._peaks), 2))
        for it in range(len(self._peaks)):
            peak_sum = 0
            peak_err_sum = 0
            for fl in self._integral_dict.keys():
                peak_sum += self._integral_dict[fl][it][0]
                peak_err_sum += self._integral_dict[fl][it][1] ** 2
            integrals[it, 0] = peak_sum
            integrals[it, 1] = np.sqrt(peak_err_sum)
        return self._peaks, integrals

    @property
    def integral_dict(self) -> Dict:
        """Return a dictionary with all integrals."""
        return self._integral_dict

    @property
    def name(self):
        """Name of the evaluator (equal to first sample name)."""
        return self._name

    @property
    def names(self) -> List:
        """Names of all the samples."""
        return list(self._integral_dict.keys())

    @property
    def peaks(self) -> List:
        """Peak names."""
        return self._peaks

    @property
    def timestamp_dict(self) -> Dict:
        """Return a dictionary with all timestamps."""
        return self._timestamp_dict

    # METHODS #

    def add_integral(
        self, integrals_in: Union[Path, List], overwrite: bool = False
    ) -> None:
        """Add an integral file to the evaluator.

        :param integrals_in: Path to a directory containing integral files or a list of
            integral parameters. The file will be read with the
            ``rimseval.data_io.integrals.load`` method.
            If a list is given, it should contain the following entries:
                1. CRD file name (equiv to ``crd.name``)
                2. Timestamp (equiv to ``crd.timestamp``)
                3. Peak names (equiv to ``crd.def_integrals[0]``)
                4. Integrals (equiv to ``crd.integrals``)
        :param overwrite: If `True`, the integrals will be overwritten if the name
            already exists.

        :raises ValueError: If the peak names are not the same.
        :raises KeyError: If the name already exists and ``overwrite`` is ``False``.
        """
        if isinstance(integrals_in, Path):
            (
                name,
                timestamp,
                peaks,
                integrals_tmp,
            ) = data_io.integrals.load(integrals_in)
        else:
            name, timestamp, peaks, integrals_tmp = integrals_in

        # check if the name already exists
        if name in self._integral_dict.keys():
            if not overwrite:
                raise KeyError(f"Name {name} already exists.")

        # check if the peaks are the same
        if self._peaks is not None:
            if peaks != self._peaks:
                raise ValueError("Peak names are not the same.")
        else:  # set the peaks for the first time
            self._peaks = peaks

        if self._name is None:
            self._name = name

        # add the integrals to the dictionary
        self._integral_dict[name] = integrals_tmp
        self._timestamp_dict[name] = timestamp
