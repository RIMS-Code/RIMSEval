"""Evaluation class for integral files."""

import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple, Union

import numpy as np

from rimseval import data_io
from rimseval.utilities import delta, utils


class IntegralEvaluator:
    """Evaluate RIMS integrals.

    This class facilitates the evaluation of RIMS integrals. It can be used to:
    - Combine multiple measurements of the same sample / standard.
    - Standard normalize the sample measurements.
    - Full error propagation and correlated uncertainty calculations.
    - Feature to save and reload the evaluation.

    Example:
        >>> integral_smp = Path("my_sample.csv")  # path to sample
        >>> integral_std = Path("my_standard.csv")  # path to standard
        >>> ev = IntegralEvaluator(integral_smp)  # load sample
        >>> std = IntegralEvaluator(integral_std)  # load standard
        >>> ev.standard = std  # define standard for sample
        >>> ev.deltas  # print delta values
        array([[23.1, 2.3], [-27.2, 8.1]])
    """

    def __init__(self, integrals_in: Path = None):
        """Initialize the IntegralEvaluator class.

        :param integrals_in: Path to an integral file.
            If `None` is given, the class is initialized empty (mainly used for loading
            from file).
        """
        self._name = None
        self._fnames = set()
        self._peaks = None
        self._integral_dict = {}
        self._timestamp_dict = {}

        self._deltas = None
        self._standard = None
        self._standard_timestamp = None  # timestamp of the standard, None if stable
        self._ratio_indexes = None
        self._correlation_set = set()  # set for correlations: to update

        if integrals_in is not None:
            self.add_integral(integrals_in)

    # PROPERTIES #

    @property
    def correlation_set(self) -> Set[Tuple[int, int]]:
        """Return the set of correlations that were calculated.

        :return: Set of correlations, where each entry is a tuple of the form (i, j),
            and i, j are the indexes of the delta-values that were correlated.

        :raise TypeError: Correlation set to load is not of type ``set``.
        """
        return self._correlation_set

    @correlation_set.setter
    def correlation_set(self, corr_set: Set[Tuple[int, int]]):
        if not isinstance(corr_set, set):
            raise TypeError("Correlation set to load is not of type ``set``.")

        self._correlation_set = corr_set

    @property
    def deltas(self) -> np.ndarray:
        """Return the deltas and their errors.

        Delta values are calculated with respect to the standard.

        :return: Deltas values.

        :raises TypeError: No standard is loaded
        """
        if self.standard is None:
            raise TypeError("No standard is loaded.")

        self._deltas, self._ratio_indexes = delta.delta_calc(
            self._peaks, self.integrals, self.standard.integrals, return_ind=True
        )

        return self._deltas

    @property
    def delta_labels(self) -> List[str]:
        """Return the labels for the delta values.

        Returns a list of strings, formatted to be displayed as the labels for the
        delta values. If the ratio for a given integral is undefined, the list will
        contain ``None``.

        If no delta values are available, they will be calculated first.

        :return: List of labels.
        """
        if self._deltas is None:
            _ = self.deltas

        labels = []
        for nomit, denomit in self._ratio_indexes:
            if nomit == -1 or denomit == -1:
                labels.append(None)
            else:
                labels.append(
                    utils.delta_label(self._peaks[nomit], self._peaks[denomit])
                )

        return labels

    @property
    def file_names(self) -> Set[Path]:
        """Return the set of file names that are loaded.

        :return: Set of file names.
        """
        return self._fnames

    @property
    def integrals(self) -> np.ndarray:
        """Return the integrals and their errors.

        Integrals are summed up and the error are propagated as the square root of the
        sum of the squared errors.

        :return: Integrals
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
        return integrals

    @property
    def integral_dict(self) -> Dict:
        """Return a dictionary with all integrals."""
        return self._integral_dict

    @property
    def name(self) -> str:
        """Name of the evaluator (equal to first sample name).

        :return: Name of the evaluator.
        """
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value

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

    @property
    def standard(self) -> "IntegralEvaluator":
        """Get/set the standard class.

        :return: Standard class.

        :raise TypeError: If the standard is not of type ``IntegralEvaluator``.
        :raise ValueError: Peak names of the standard and the sample do not match.
        """
        return self._standard

    @standard.setter
    def standard(self, value: "IntegralEvaluator"):
        if not isinstance(value, IntegralEvaluator):
            raise TypeError("Standard must be of type IntegralEvaluator.")
        if self._peaks != value.peaks:
            raise ValueError("Peak names of the standard and the sample do not match.")
        self._standard = value

    @property
    def standard_timestamp(self) -> datetime.datetime:
        """Get / set the timestamp of the standard.

        :return: Timestamp of the standard or None if all isotopes are stable and
            therefore no decay correction is required.

        :raise TypeError: If the timestamp is not of type ``datetime.datetime``.
        """
        return self._standard_timestamp

    @standard_timestamp.setter
    def standard_timestamp(self, value: datetime.datetime):
        if not isinstance(value, datetime.datetime) and value is not None:
            raise TypeError("Timestamp must be of type datetime.datetime.")
        self._standard_timestamp = value

    # METHODS #

    def add_integral(
        self, integrals_in: Union[Path, List], overwrite: bool = False
    ) -> None:
        """Add an integral file to the evaluator.

        :param integrals_in: Path to a integral file.
        :param overwrite: If `True`, the integrals will be overwritten if the name
            already exists.

        :raises ValueError: If the peak names are not the same.
        :raises KeyError: If the name already exists and ``overwrite`` is ``False`` or
            the file is already loaded and ``overwrite`` is ``False``.
        """
        (
            name,
            timestamp,
            peaks,
            integrals_tmp,
        ) = data_io.integrals.load(integrals_in)

        if integrals_in.absolute() in self._fnames:
            if not overwrite:
                raise KeyError(f"File {integrals_in} already loaded.")

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
        self._fnames.add(integrals_in.absolute())
        self._integral_dict[name] = integrals_tmp
        self._timestamp_dict[name] = timestamp

    def correlation_coefficient_delta(
        self,
        delta1: Union[Iterable, int, str],
        delta2: Union[Iterable, int, str],
    ) -> float:
        """Calculate the correlation factor between two delta values.

        For details, see ``rimseval.utils.delta.correlation_coefficient``.

        :param delta1: The first delta value. This can be either given as an iterable
            of indices indicating the numerator and denominator peak, as an integer
            indicating the position in the list of ratio indexes, or as a string
            indicating the name of the delta value, as in ``delta_labels``.
        :param delta2: The second delta value. This can be either given as an iterable
            of indices indicating the numerator and denominator peak, as an integer
            indicating the position in the list of ratio indexes, or as a string
            indicating the name of the delta value, as in ``delta_labels``.

        :return: Correlation coefficient rho.

        :raises ValueError: The denominators are not the same or the nominators are the
            same.
        :raises TypeError: The input is of invalid type.
        """
        if self._ratio_indexes is None:
            _ = self.deltas

        # if deltas are givenas string, convert to integer with position in list
        if isinstance(delta1, str):
            delta1_ind = self.delta_labels.index(delta1)
        elif hasattr(delta1, "__iter__"):
            delta1_ind = np.where(np.all(self._ratio_indexes == delta1, axis=1))[0][0]
        elif isinstance(delta1, int):
            delta1_ind = delta1
        else:
            raise TypeError(
                "Invalid input for delta1, needs to be string, iterable, or int"
            )

        if isinstance(delta2, str):
            delta2_ind = self.delta_labels.index(delta2)
        elif hasattr(delta2, "__iter__"):
            delta2_ind = np.where(np.all(self._ratio_indexes == delta2, axis=1))[0][0]
        elif isinstance(delta2, int):
            delta2_ind = delta2
        else:
            raise TypeError(
                "Invalid input for delta2, needs to be string, an iterable, or int"
            )

        delta1_ratio_ind = self._ratio_indexes[delta1_ind]
        delta2_ratio_ind = self._ratio_indexes[delta2_ind]

        if delta1_ratio_ind[1] != delta2_ratio_ind[1]:
            raise ValueError("The denominators are not the same.")

        if delta1_ratio_ind[0] == delta2_ratio_ind[0]:
            raise ValueError("The nominators are the same.")

        # prepare the data for correlation coefficient
        diak = self.deltas[delta1_ind]
        djak = self.deltas[delta2_ind]
        ik = self.integrals[delta1_ratio_ind[1]]
        sk = self.standard.integrals[delta1_ratio_ind[1]]

        # add requested correlations to the correlation set
        self._correlation_set.add((delta1_ind, delta2_ind))

        return delta.correlation_coefficient_delta(diak, djak, ik, sk)

    def reset_correlation_set(self) -> None:
        """Reset the correlation coefficients that were requested."""
        self._correlation_set = set()
