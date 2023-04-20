"""Utility file to calculate delta values and correlated uncertainties."""

import warnings
from typing import List

import numpy as np

import rimseval
from rimseval.utilities import ini


def delta_calc(names: List[str], integrals: np.ndarray) -> np.ndarray:
    """Calculate delta values for a given set of integrals.

    Use ``iniabu`` to calculate the delta values with respect to normalizing isotope.
    If the name of a peak is not valid or the major isotope not present, return
    ``np.nan`` for that entry. Appropriate error propagation is done as well.

    :param names: Names of the peaks as list.
    :param integrals: Integrals, as defined in ``CRDFileProcessor.integrals``.

    :return: List of delta values, same shape and format as ``integrals``.
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

    for it, iso in enumerate(names_iniabu):
        norm_iso = norm_iso_name[it]

        if iso is None or norm_iso not in names_iniabu:
            integrals_delta[it][0] = np.nan
            integrals_delta[it][1] = np.nan
        else:
            msr_nom = integrals[it][0]
            msr_nom_unc = integrals[it][1]
            msr_denom = integrals[integrals_dict[norm_iso]][0]
            msr_denom_unc = integrals[integrals_dict[norm_iso]][1]

            with warnings.catch_warnings():
                if rimseval.VERBOSITY < 2:
                    warnings.simplefilter("ignore", category=RuntimeWarning)
                msr_ratio = msr_nom / msr_denom
                integrals_delta[it][0] = ini.iso_delta(iso, norm_iso, msr_ratio)

                # error calculation
                std_ratio = ini.iso_ratio(iso, norm_iso)
                integrals_delta[it][1] = (
                    1000
                    / std_ratio
                    * np.sqrt(
                        (msr_nom_unc / msr_denom) ** 2
                        + (msr_nom * msr_denom_unc / msr_denom**2) ** 2
                    )
                )

    return integrals_delta
