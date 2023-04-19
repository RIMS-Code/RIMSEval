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

        # load integrals
        if integrals_in is not None:
            if isinstance(integrals_in, Path):
                (
                    self._name,
                    timestamp,
                    self._peaks,
                    integrals_tmp,
                ) = data_io.integrals.load(integrals_in)
            else:
                self._name, timestamp, self._peaks, integrals_tmp = integrals_in

            # create dictionaries for integrals and timestamps where the names are the keys
            self._integral_dict = {self._name: integrals_tmp}
            self._timestamp_dict = {self._name: timestamp}

        # default settings
        self._mode = self.Mode.SUM

    # PROPERTIES #

    @property
    def integrals(self) -> Dict:
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
    def timestamps(self) -> Dict:
        """Return a dictionary with all timestamps."""
        return self._timestamp_dict
