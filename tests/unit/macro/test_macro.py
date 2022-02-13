"""Test the macro capability."""

from pathlib import Path

import numpy as np

from rimseval.processor import CRDFileProcessor


def test_macro_max_ions_per_shot(crd_file):
    """Run macro to filter maximum ions per shot and assert it's functioning."""
    _, ions_per_shot, all_tofs, fname = crd_file

    crd_exp = CRDFileProcessor(Path(fname))
    crd_exp.spectrum_full()
    crd_exp.filter_max_ions_per_shot(3)

    macro_file = Path("ex_max_ions_per_shot.py")

    crd_macro = CRDFileProcessor(Path(fname))
    crd_macro.spectrum_full()
    crd_macro.run_macro(macro_file)

    np.testing.assert_equal(crd_exp.data, crd_macro.data)
    assert crd_exp.nof_shots == crd_macro.nof_shots
