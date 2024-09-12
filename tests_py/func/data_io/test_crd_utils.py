"""Tests for processors utilities."""

import numpy as np

import rimseval.data_io.crd_utils as cu


def test_shot_to_tof_mapper():
    """Map ions per shot to all_tofs array."""
    ions_per_shot = np.array([0, 0, 3, 5, 0, 7])
    mapper_exp = np.array([[0, 0], [0, 0], [0, 3], [3, 8], [8, 8], [8, 15]])
    mapper_rec = cu.shot_to_tof_mapper(ions_per_shot)
    np.testing.assert_equal(mapper_rec, mapper_exp)
