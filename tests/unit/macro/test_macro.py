"""Test the macro capability."""

from pathlib import Path

import pytest
import numpy as np

from rimseval.processor import CRDFileProcessor


@pytest.fixture
def macro_path(request) -> Path:
    """Provides the path to this folder where the macros are.

    :return: Path to the folder
    """
    return Path(request.fspath).parents[0].absolute()


def test_macro_max_ions_per_shot(macro_path, crd_file):
    """Run macro to filter maximum ions per shot and assert it's functioning."""
    _, _, _, fname = crd_file

    crd_exp = CRDFileProcessor(Path(fname))
    crd_exp.spectrum_full()
    crd_exp.filter_max_ions_per_shot(3)

    macro_file = macro_path.joinpath("ex_max_ions_per_shot.py")

    crd_macro = CRDFileProcessor(Path(fname))
    crd_macro.spectrum_full()
    crd_macro.run_macro(macro_file)

    np.testing.assert_equal(crd_exp.data, crd_macro.data)
    assert crd_exp.nof_shots == crd_macro.nof_shots


def test_macro_max_ions_per_pkg(macro_path, crd_file):
    """Run macro to filter out packages with too many shots and compare to filter."""
    _, _, _, fname = crd_file

    crd_exp = CRDFileProcessor(Path(fname))
    crd_exp.spectrum_full()
    crd_exp.packages(2)
    crd_exp.filter_max_ions_per_pkg(4)

    macro_file = macro_path.joinpath("ex_max_ions_per_pkg.py")

    crd_macro = CRDFileProcessor(Path(fname))
    crd_macro.spectrum_full()
    crd_macro.packages(2)
    crd_macro.run_macro(macro_file)

    np.testing.assert_equal(crd_exp.data, crd_macro.data)
    assert crd_exp.nof_shots == crd_macro.nof_shots
    np.testing.assert_equal(crd_exp.data_pkg, crd_macro.data_pkg)
    np.testing.assert_equal(crd_exp.nof_shots_pkg, crd_macro.nof_shots_pkg)
