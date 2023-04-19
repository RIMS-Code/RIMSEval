"""Evaluation class for integral files.


"""

from enum import Enum

from pathlib import Path
from typing import Dict, List, Union

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

    class Mode(Enum):
        """Evaluation mode.

        .. note:: The value of the modes is used as explanations of function, e.g.,
            for the GUI.

        - ``Mode.SUM``: Sum all the integrals (default).
        - ``Mode.AVERAGE``: Average the individual integrals.
        """

        SUM = "Sum of integrals"
        AVERAGE = "Average of integrals"

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

        # default settings
        self._mode = self.Mode.SUM

    # PROPERTIES #

    @property
    def integral_dict(self) -> Dict:
        """Return a dictionary with all integrals."""
        return self._integral_dict

    @property
    def mode(self) -> Mode:
        """Get / set the evaluation mode.

        :raises TypeError: If the mode is not of type ``IntegralEvaluator.Mode``.
        """
        return self._mode

    @mode.setter
    def mode(self, value):
        if not isinstance(value, self.Mode):
            raise TypeError(f"Mode must be of type {self.Mode}")
        self._mode = value

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
        :raises KeyError: If the name already exists and ``overwrite`` is `False`.
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
