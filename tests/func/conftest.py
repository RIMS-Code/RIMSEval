"""Fixtures for functional tests."""

from pathlib import Path

import pytest
import numpy as np

from rimseval.processor import CRDFileProcessor


@pytest.fixture
def crd_int_delta(crd_file) -> CRDFileProcessor:
    """Initialize a CRDFileProcessor file, set some integrals, and return it.

    The integrals set are fake, no actual calculation takes place. This fixture simply
    serves to test functionality (i.e., delta calculation) after processing of the CRD
    file.

    :return: CRDFileProcessor instance with integrals defined and set.
    """
    _, _, _, fname = crd_file
    crd = CRDFileProcessor(Path(fname))

    peak_names = ["54Fe", "56Fe", "57Fe", "58Fe", "244Pu", "238Pu", "bg"]
    peak_limits = np.array(
        [
            [53.8, 54.2],
            [55.8, 56.2],
            [56.8, 57.2],
            [57.8, 58.2],
            [243.8, 244.2],
            [237.8, 238.2],
            [238.5, 238.7],
        ]
    )
    crd.def_integrals = peak_names, peak_limits
    crd.integrals = np.array(
        [
            [5.84500000e04, 2.41764348e02],
            [9.17540000e05, 9.57883083e02],
            [2.11900000e04, 1.45567854e02],
            [2.82000000e03, 5.31036722e01],
            [10000, 100],
            [144, 12],
            [34212, 185],
        ]
    )
    crd.integrals_pkg = np.array([crd.integrals, crd.integrals])
    return crd


@pytest.fixture
def data_files_path(request) -> Path:
    """Provides the path to the `data_files` folder.

    :return: Path to the folder
    """
    curr = Path(request.fspath).parents[0]
    return Path(curr).joinpath("data_files").absolute()
