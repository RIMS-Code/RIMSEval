"""Example: Re-implementation of maximum ions per shot."""

import numpy as np

from rimseval.processor import CRDFileProcessor


def calc(crd: CRDFileProcessor) -> None:
    """Macro to filter out all shots with more than 3 ions.

    :param crd: CRD file processor that will be passed to the macro.
    """
    # maximum ions per shot to be filtered out
    max_ions = 120

    # create a numpy mask that selects the filters we want to filter
    shots_rejected = np.where(crd.ions_per_shot > max_ions)[0]

    # pass the rejected shots array to the routine that will filter everything
    crd.apply_individual_shots_filter(shots_rejected)
