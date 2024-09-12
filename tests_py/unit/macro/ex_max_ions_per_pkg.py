"""Example: Re-implementation of maximum ions per package filter."""

import numpy as np

from rimseval.processor import CRDFileProcessor


def calc(crd: CRDFileProcessor) -> None:
    """Macro to filter out all packages with more than 4 ions.

    Here we assume, that you have already created packages using the built-in function.
    Package data is therefore available.

    :param crd: CRD file processor that will be passed to the macro.
    """
    # maximum ions per pkg to be filtered out
    max_ions = 4

    # calculate total ions in all the packages
    total_ions_per_pkg = np.sum(crd.data_pkg, axis=1)

    # find packages that need deletion
    pkg_to_delete = np.where(total_ions_per_pkg > max_ions)[0]

    # now delete the packages that are not needed
    crd.data_pkg = np.delete(crd.data_pkg, pkg_to_delete, axis=0)

    # update the number of shots per package array: delete entries of deleted packages
    crd.nof_shots_pkg = np.delete(crd.nof_shots_pkg, pkg_to_delete, axis=0)

    # finally, we need to update the ``crd.data`` and ``crd.nof_shots`` entries
    crd.data = np.sum(crd.data_pkg, axis=0)
    crd.nof_shots = np.sum(crd.nof_shots_pkg)
