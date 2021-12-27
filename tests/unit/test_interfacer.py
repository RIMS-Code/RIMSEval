"""Unit tests for the interfacer."""

from pathlib import Path

import pytest
import numpy as np

from rimseval import CRDFileProcessor, interfacer


def test_read_lion_eval_calfile(legacy_files_path, crd_file):
    """Read and apply an old LIONEval calibration file."""
    cal_fname = Path(legacy_files_path).joinpath("all_cals.cal")

    _, _, _, fname = crd_file
    crd = CRDFileProcessor(Path(fname))

    interfacer.read_lion_eval_calfile(crd, cal_fname)

    # make sure none of them are `None`
    assert crd.def_mcal is not None
    assert crd.def_integrals is not None
    assert crd.def_backgrounds is not None


def test_read_lion_eval_calfile_no_filename(crd_file):
    """Provide no filename will create one and error out because it does not exist."""
    _, _, _, fname = crd_file
    crd = CRDFileProcessor(Path(fname))

    with pytest.raises(IOError) as err:
        interfacer.read_lion_eval_calfile(crd)

    err_msg = err.value.args[0]
    assert (
        err_msg == f"The requested calibration file {Path(fname).with_suffix('.cal')} "
        f"does not exist."
    )


def test_calfile_load_io_error(crd_file):
    """Raise IOError if file does not exist."""
    _, _, _, fname = crd_file
    crd = CRDFileProcessor(Path(fname))

    fname = Path("does_not_exist")

    with pytest.raises(IOError) as err:
        interfacer.load_cal_file(crd, fname)

    err_msg = err.value.args[0]
    assert err_msg == f"The requested calibration file {fname} does not exist."


def test_calfile_save_reapply_full_file(legacy_files_path, crd_file, tmpdir):
    """Save a calibration, apply to a second file, and assure they are identical."""
    _, _, _, fname = crd_file

    # first CRD file that we are going to open
    crd_1 = CRDFileProcessor(Path(fname))

    lion_cal = Path(legacy_files_path).joinpath("all_cals.cal")  # contains it all!
    interfacer.read_lion_eval_calfile(crd_1, lion_cal)

    settings_file = tmpdir.join("settings.json")  # temporary settings file
    interfacer.save_cal_file(crd_1, settings_file)

    # now open a second one and apply the same settings file
    crd_2 = CRDFileProcessor(Path(fname))
    interfacer.load_cal_file(crd_2, settings_file)

    # ensure they are equal
    np.testing.assert_equal(crd_1.def_mcal, crd_2.def_mcal)

    assert crd_1.def_integrals[0] == crd_2.def_integrals[0]
    np.testing.assert_equal(crd_1.def_integrals[1], crd_2.def_integrals[1])

    assert crd_1.def_backgrounds[0] == crd_2.def_backgrounds[0]
    np.testing.assert_equal(crd_1.def_backgrounds[1], crd_2.def_backgrounds[1])


def test_calfile_save_reapply_mcal_only(legacy_files_path, crd_file, tmpdir):
    """Save a mass calibration to default, reload again, and ensure it works."""
    _, _, _, fname = crd_file

    # first CRD file that we are going to open
    crd_1 = CRDFileProcessor(Path(fname))
    crd_1.def_mcal = np.array([[1, 1], [2, 2]])

    interfacer.save_cal_file(crd_1)
    interfacer.load_cal_file(crd_1)
