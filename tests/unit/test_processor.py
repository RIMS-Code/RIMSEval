"""Unit tests for processor."""

from pathlib import Path

import numpy as np

from rimseval.processor import CRDFileProcessor


def test_packages(crd_file):
    """Simple test to ensure packages are made in two ways correctly."""
    _, ions_per_shot, _, fname = crd_file
    nof_shots = len(ions_per_shot)
    crd = CRDFileProcessor(Path(fname))
    crd.spectrum_full()
    # fixme the next few tests are shitty, change when incorporating hypothesis testing
    crd.packages(nof_shots // 2)
    assert crd.data_pkg.sum() == crd.data.sum()
    np.testing.assert_equal(crd.data_pkg.sum(axis=0), crd.data)
    assert crd.nof_shots_pkg.sum() == crd.nof_shots
    # now redo w/ a lower number of shots per pkg
    crd.packages(nof_shots // 4)
    assert crd.data_pkg.sum() == crd.data.sum()
    np.testing.assert_equal(crd.data_pkg.sum(axis=0), crd.data)
    assert crd.nof_shots_pkg.sum() == crd.nof_shots


def test_filter_max_ions_per_pkg(crd_file):
    """Filter the packages by maximum ion."""
    _, ions_per_shot, _, fname = crd_file
    max_ions = ions_per_shot.max() - 1  # filter one or so packages out
    sum_ions = 0
    for ion in ions_per_shot:
        if ion <= max_ions:
            sum_ions += ion

    crd = CRDFileProcessor(Path(fname))
    crd.spectrum_full()
    crd.packages(1)
    crd.filter_max_ions_per_pkg(max_ions)
    assert crd.data_pkg.sum() == sum_ions
