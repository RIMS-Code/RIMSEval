"""Function tests for the multi file processor class."""

from pathlib import Path

import rimseval
from rimseval.multi_proc import MultiFileProcessor as mfp
from rimseval.processor import CRDFileProcessor


def test_mfp_num_of_files():
    """Return the number of files given to the multi processor."""
    files = [Path("a.crd"), Path("b.crd"), Path("c.crd")]

    crds = mfp(files)
    assert crds.num_of_files == len(files)


def test_mfp_peak_fwhm(crd_file):
    """Get / set the peak FWHM of the multip processor."""
    val = 42.0
    _, _, _, fname = crd_file
    files = [Path(fname)]

    crds = mfp(files)
    crds.peak_fwhm = val
    assert crds.peak_fwhm == val


def test_mfp_close_files(crd_file):
    """Close and delete a crd file, and associate it with None."""
    _, _, _, fname = crd_file
    files = [Path(fname)]

    crds = mfp(files)
    crds.open_files()

    crds.close_files()
    assert crds._files is None


def test_mfp_close_selected_files(crd_file):
    """Close 2 out of three selected files."""
    _, _, _, fname = crd_file
    files = [Path(fname)] * 5

    crds = mfp(files)
    crds.open_files()

    main_id = 3  # the main file

    ids_to_del = [0, 2]
    new_main_id = crds.close_selected_files(ids_to_del, main_id=main_id)
    assert new_main_id == 1  # main id update
    assert len(crds.files) == len(files) - len(ids_to_del)

    # delete main file
    assert crds.close_selected_files([new_main_id], main_id=new_main_id) == 0

    # delete one more without a main id file -> returns zero
    assert crds.close_selected_files([0]) == 0
    assert len(crds.files) == len(files) - len(ids_to_del) - 2


def test_mfp_open_crd_file(crd_file):
    """Open a single file in the multifileprocessor."""
    _, _, _, fname = crd_file
    files = [Path(fname)]

    crds = mfp(files)
    crds.open_files()
    assert crds.files is not None
    for crd in crds.files:
        assert isinstance(crd, CRDFileProcessor)


def test_mfp_open_additional_file(crd_file):
    """Open additional file in MFP with single file already opened."""
    _, _, _, fname = crd_file

    crds = mfp([Path(fname)])
    crds.read_files()

    assert len(crds.files) == 1

    crds.open_additional_files([Path(fname), Path(fname)], read_files=True)
    assert len(crds.files) == 3

    # ensure all files were read
    for crd in crds.files:
        assert crd.tof is not None


def test_mfp_read_crd_file(crd_file):
    """Read a single crd file without opening it (opening happens automatically)."""
    _, _, _, fname = crd_file
    files = [Path(fname)]

    crds = mfp(files)
    crds.read_files()

    for crd in crds.files:
        assert crd.tof is not None
