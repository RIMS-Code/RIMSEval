"""Multi processor unit tests."""

from pathlib import Path

import numpy as np

from rimseval.multi_proc import MultiFileProcessor as mfp


def test_mfp_apply_to_all(crd_file):
    """Apply settings from one crd file to all."""
    _, _, _, fname = crd_file
    files = [Path(fname), Path(fname)]
    id = 0  # id of main crd file
    bg_corr = True

    crds = mfp(files)
    crds.read_files()

    crd_main = crds.files[id]
    crd_main.def_mcal = np.array([[0.1, 10], [0.2, 22], [0.3, 33]])
    crd_main.mass_calibration()
    crd_main.def_integrals = ["Int1"], np.array([[6.0, 7.0]])
    crd_main.def_backgrounds = ["Int1"], np.array([[5.0, 6.0]])
    crd_main.packages(2)
    crd_main.filter_max_ions_per_pkg(5)
    crd_main.integrals_calc(bg_corr=bg_corr)

    # apply to all
    crds.apply_to_all(id=id, opt_mcal=False, bg_corr=bg_corr)

    for crd in crds.files:
        np.testing.assert_equal(crd.data, crd_main.data)
        np.testing.assert_equal(crd.mass, crd_main.mass)
        np.testing.assert_equal(crd.tof, crd_main.tof)
        np.testing.assert_equal(crd.data_pkg, crd_main.data_pkg)
        assert crd.nof_shots == crd_main.nof_shots
        np.testing.assert_equal(crd.nof_shots_pkg, crd_main.nof_shots_pkg)
