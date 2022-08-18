"""Utilities for tests."""

import numpy as np

from rimseval.data_io import CRDReader


def assert_crd_equal(crd1: CRDReader, crd2: CRDReader):
    """Test function to assert that two CRD files are equal.

    Test the content of the CRD file after reading to ensure that they are identical.

    :param crd1: First CRD file to compare.
    :param crd2: Second CRD file to compare.
    """
    np.testing.assert_equal(crd1.all_tofs, crd2.all_tofs)
    np.testing.assert_equal(crd1.ions_per_shot, crd2.ions_per_shot)
    np.testing.assert_equal(crd1.ions_to_tof_map, crd2.ions_to_tof_map)
    assert crd1.nof_ions == crd2.nof_ions
    assert crd1.nof_shots == crd2.nof_shots
