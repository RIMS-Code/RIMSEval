"""Function tests for the multi file processor class."""

from pathlib import Path

from rimseval.multi_proc import MultiFileProcessor as mfp
from rimseval.processor import CRDFileProcessor


def test_mfp_num_of_files():
    """Return the number of files given to the multi processor."""
    files = [Path("a.crd"), Path("b.crd"), Path("c.crd")]

    crds = mfp(files)
    assert crds.num_of_files == len(files)


def test_mfp_close_files(crd_file):
    """Close and delete a crd file, and associate it with None."""
    _, _, _, fname = crd_file
    files = [Path(fname)]

    crds = mfp(files)
    crds.open_files()

    crds.close_files()
    assert crds._files is None


def test_mfp_open_crd_file(crd_file):
    """Open a single file in the multifileprocessor."""
    _, _, _, fname = crd_file
    files = [Path(fname)]

    crds = mfp(files)
    crds.open_files()
    assert crds.files is not None
    for crd in crds.files:
        assert isinstance(crd, CRDFileProcessor)


def test_mfp_read_crd_file(crd_file):
    """Read a single crd file without opening it (opening happens automatically)."""
    _, _, _, fname = crd_file
    files = [Path(fname)]

    crds = mfp(files)
    crds.read_files()

    for crd in crds.files:
        assert crd.tof is not None
