"""Test Excel writer function."""

from pathlib import Path

import numpy as np

from rimseval import CRDFileProcessor
import rimseval.data_io.excel_writer as exw


def test_workup_file_writer_no_integrals(crd_file):
    """Assure nothing is done if no integrals were set."""
    _, _, _, fname = crd_file
    crd = CRDFileProcessor(Path(fname))

    # create a file for excel outptut - which won't get generated
    ex_fname = Path("test.xlsx")
    exw.workup_file_writer(crd, ex_fname)

    assert not ex_fname.is_file()


def test_workup_file_run_through(crd_file, tmpdir):
    """Run through excel writer and assure it creates an xlsx file."""
    _, _, _, fname = crd_file

    crd = CRDFileProcessor(Path(fname))
    crd.spectrum_full()

    # set some random mass cal from 1 to 2
    crd.def_mcal = np.array([[crd.tof.min(), 1.0], [crd.tof.max(), 2.0]])
    crd.mass_calibration()

    # now set the integrals to include everything
    crd.def_integrals = (
        ["Fe54", "Fe56", "FeO"],
        np.array([[0.9, 1.2], [1.2, 2.0], [2.0, 2.1]]),
    )
    crd.integrals_calc()

    # create a file for excel outptut - which won't get generated
    ex_fname = tmpdir.join("test.xlsx")
    exw.workup_file_writer(crd, Path(ex_fname), timestamp=True)
    assert ex_fname.isfile()
