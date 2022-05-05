"""Test Excel writer function."""

from pathlib import Path

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
