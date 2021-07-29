"""Function tests for interfacer."""

from pathlib import Path

import pytest
import numpy as np

from rimseval import interfacer
from rimseval.processor import CRDFileProcessor


def test_read_lion_eval_calfile(mocker, crd_proc_mock):
    """Set crd file mass cal, integrals, and bg_corr from LIONEval cal file.

    Mocking getting a file since the LIONEvalCal is actually tested in its own unit
    tests with proper files. Here we just fake some data.

    ToDo: background correction stuff.
    """
    mcal_exp = np.array([[1, 1], [2, 2]])  # expected and returned
    integrals_ret = [["46Ti", 46.0, 0.2, 0.3], ["47Ti", 47.1, 0.3, 0.3]]
    integrals_exp = (["46Ti", "47Ti"], np.array([[45.8, 46.3], [46.8, 47.4]]))

    cal_mock = mocker.MagicMock()
    cal_mock_prop_mcal = mocker.PropertyMock(return_value=mcal_exp)
    cal_mock_prop_integrals = mocker.PropertyMock(return_value=integrals_ret)
    mocker.patch("rimseval.interfacer.LIONEvalCal", cal_mock)
    type(cal_mock()).mass_cal = cal_mock_prop_mcal
    type(cal_mock()).integrals = cal_mock_prop_integrals

    interfacer.read_lion_eval_calfile(crd=crd_proc_mock, fname=Path("."))

    np.testing.assert_equal(crd_proc_mock.def_mcal, mcal_exp)
    integrals_rec = crd_proc_mock.def_integrals
    assert integrals_rec[0] == integrals_exp[0]  # names
    np.testing.assert_almost_equal(integrals_rec[1], integrals_exp[1])
