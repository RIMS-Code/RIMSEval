"""Utility file to calculate delta values and correlated uncertainties."""

from typing import List, Tuple, Union
import warnings

import numpy as np

import rimseval
from .utils import ini


def correlation_coefficient_delta(
    diak: np.ndarray, djak: np.ndarray, ik: np.ndarray, sk: np.ndarray
) -> float:
    """Calculate and return the correlation coefficient for two delta-values.

    The correlation coefficient rho is returned. Details can be found in
    Stephan and Trappitsch (2023), equation (24).
    doi: 10.1016/j.ijms.2023.117053

    :param diak: Delta value and uncertainty of x-axis.
    :param djak: Delta value and uncertainty of y-axis.
    :param ik: Integral and uncertainty of common denominator of both axes for sample.
    :param sk: Integral and uncertainty of common denominator of both axes for standard.

    :return: Correlation coefficient rho.
    """
    return ((ik[1] / ik[0]) ** 2 + (sk[1] / sk[0]) ** 2) / (
        (diak[1] / (diak[0] + 1000)) * (djak[1] / (djak[0] + 1000))
    )


def delta_calc(
    names: List[str],
    integrals: np.ndarray,
    standards: np.ndarray = None,
    return_ind: bool = False,
) -> Union[np.ndarray, Tuple[np.ndarray, np.ndarray]]:
    """Calculate delta values for a given set of integrals.

    If a standard is given, the delta values are calculated with respect to this
    standard. Otherwise, use ``iniabu`` to calculate the delta values with respect to
    normalizing isotope. If the name of a peak is not valid or the major isotope not
    present, return ``np.nan`` for that entry. Appropriate error propagation is done
    as well.

    The normalizing isotope is always gathered from ``iniabu``.

    Error propagation follows Stephan and Trappitsch (2023), equation 24.
    doi: 10.1016/j.ijms.2023.117053

    :param names: Names of the peaks as list.
    :param integrals: Integrals, as defined in ``CRDFileProcessor.integrals``.
    :param standards: Standard to normalize to, same format as ``integrals``.
    :param return_ind: If ``True``, return the indices of the [nominator, denominator]
        isotope for each ratio (-1 for None).

    :return: List of delta values, same shape and format as ``integrals`` and
        (if ``return_ind = True``) a list of indices where the nominator, denominator
        of each isotopic ratio is located in the ``integrals`` and ``standard`` array.
    """
    # transform all names to valid ``iniabu`` names or call them ``None``
    names_iniabu = []
    for name in names:
        try:
            names_iniabu.append(ini.iso[name].name)
        except IndexError:
            names_iniabu.append(None)

    # find major isotope names
    norm_iso_name = []
    for name in names_iniabu:
        if name is None:
            norm_iso_name.append(None)
        else:
            ele = name.split("-")[0]
            maj = ini._get_norm_iso(ele)  # can't give index error if above passed
            norm_iso_name.append(maj)

    integrals_dict = dict(zip(names_iniabu, range(len(names_iniabu))))  # noqa: B905

    integrals_delta = np.zeros_like(integrals, dtype=float)

    integral_indexes = np.zeros((len(names_iniabu), 2), dtype=int) - 1  # all -1
    for it, iso in enumerate(names_iniabu):
        norm_iso = norm_iso_name[it]

        if iso is None or norm_iso not in names_iniabu:
            integrals_delta[it][0] = np.nan
            integrals_delta[it][1] = np.nan
        else:
            integral_indexes[it][0] = it
            integral_indexes[it][1] = integrals_dict[norm_iso]
            msr_nom = integrals[it][0]
            msr_nom_unc = integrals[it][1]
            msr_denom = integrals[integrals_dict[norm_iso]][0]
            msr_denom_unc = integrals[integrals_dict[norm_iso]][1]
            if standards is not None:
                std_nom = standards[it][0]
                std_nom_unc = standards[it][1]
                std_denom = standards[integrals_dict[norm_iso]][0]
                std_denom_unc = standards[integrals_dict[norm_iso]][1]

            with warnings.catch_warnings():
                if rimseval.VERBOSITY < 2:
                    warnings.simplefilter("ignore", category=RuntimeWarning)
                msr_ratio = msr_nom / msr_denom
                if standards is not None:
                    std_ratio = std_nom / std_denom
                    integrals_delta[it][0] = (msr_ratio / std_ratio - 1) * 1000
                else:
                    integrals_delta[it][0] = ini.iso_delta(iso, norm_iso, msr_ratio)

                # error calculation
                if standards is not None:
                    integrals_delta[it][1] = (integrals_delta[it][0] + 1000) * np.sqrt(
                        (msr_nom_unc / msr_nom) ** 2
                        + (msr_denom_unc / msr_denom) ** 2
                        + (std_nom_unc / std_nom) ** 2
                        + (std_denom_unc / std_denom) ** 2
                    )
                else:
                    integrals_delta[it][1] = (integrals_delta[it][0] + 1000) * np.sqrt(
                        (msr_nom_unc / msr_nom) ** 2 + (msr_denom_unc / msr_denom) ** 2
                    )

    return integrals_delta if not return_ind else (integrals_delta, integral_indexes)
