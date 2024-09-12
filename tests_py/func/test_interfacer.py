"""Function tests for interfacer."""

from pathlib import Path

import numpy as np
import pytest

from rimseval import interfacer


def test_read_lion_eval_calfile(mocker, crd_proc_mock):
    """Set crd file mass cal, integrals, and bg_corr from LIONEval cal file.

    Mocking getting a file since the LIONEvalCal is actually tested in its own unit
    tests with proper files. Here we just fake some data.

    :param mocker: Pytest mocker object.
    :param crd_proc_mock: Mock fixture for CRDFileProcessor instance.
    """
    mcal_exp = np.array([[1, 1], [2, 2]])  # expected and returned
    integrals_ret = [["46Ti", 46.0, 0.2, 0.3], ["47Ti", 47.1, 0.3, 0.3]]
    integrals_exp = (["46Ti", "47Ti"], np.array([[45.8, 46.3], [46.8, 47.4]]))
    backgrounds_ret = [["46Ti", 46.0, 44.2, 44.4, 46.4, 46.6]]
    backgrounds_exp = [["46Ti", "46Ti"], np.array([[44.2, 44.4], [46.4, 46.6]])]

    cal_mock = mocker.MagicMock()
    cal_mock_prop_mcal = mocker.PropertyMock(return_value=mcal_exp)
    cal_mock_prop_integrals = mocker.PropertyMock(return_value=integrals_ret)
    cal_mock_prop_backgrounds = mocker.PropertyMock(return_value=backgrounds_ret)
    mocker.patch("rimseval.interfacer.LIONEvalCal", cal_mock)
    type(cal_mock()).mass_cal = cal_mock_prop_mcal
    type(cal_mock()).integrals = cal_mock_prop_integrals
    type(cal_mock()).bg_corr = cal_mock_prop_backgrounds

    interfacer.read_lion_eval_calfile(crd=crd_proc_mock, fname=Path("."))

    np.testing.assert_equal(crd_proc_mock.def_mcal, mcal_exp)
    integrals_rec = crd_proc_mock.def_integrals
    backgrounds_rec = crd_proc_mock.def_backgrounds
    assert integrals_rec[0] == integrals_exp[0]  # names
    np.testing.assert_almost_equal(integrals_rec[1], integrals_exp[1])
    assert backgrounds_rec[0] == backgrounds_exp[0]
    np.testing.assert_almost_equal(backgrounds_rec[1], backgrounds_exp[1])


def test_read_lion_eval_calfile_read_error(data_files_path, crd_proc_mock):
    """Raise IOError if the calibration file cannot be read successfully."""
    cal_file = data_files_path.joinpath("faulty_cal_file.json")

    err_exp = f"Cannot open the calibration file {cal_file.name}. JSON decode error."

    with pytest.raises(IOError) as err:
        interfacer.load_cal_file(crd_proc_mock, cal_file)

    msg = err.value.args[0]
    assert msg == err_exp
