"""Tests for saving/loading evaluator classes."""

import datetime
from pathlib import Path
import pytest
import numpy as np
import shutil

from rimseval import data_io
from rimseval.data_io import evaluator
from rimseval.evaluator import IntegralEvaluator


def assert_integral_evaluator_equal(ev1, ev2):
    """Assert that two integral evaluators are equal."""
    assert ev1.correlation_set == ev2.correlation_set
    assert ev1.name == ev2.name
    assert ev1.names == ev2.names
    np.testing.assert_equal(ev1.integrals, ev2.integrals)
    assert ev1.standard_timestamp == ev2.standard_timestamp


def test_save_load_integral_evaluator(tmpdir, integral_file):
    """Save and load an integral evaluator with a standard."""
    ev = IntegralEvaluator(integral_file)
    std = IntegralEvaluator(integral_file)
    ev.standard = std
    fout = Path(tmpdir).joinpath("test_w_std")

    evaluator.save_integral_evaluator(ev, fout)

    ev_loaded = evaluator.load_integral_evaluator(fout)

    assert_integral_evaluator_equal(ev, ev_loaded)
    assert_integral_evaluator_equal(ev.standard, ev_loaded.standard)


def test_save_load_integral_evaluator_file_not_found():
    """Raise IOError if file cannot be found."""
    with pytest.raises(IOError):
        evaluator.load_integral_evaluator(Path("some_file"))
    with pytest.raises(IOError):
        evaluator.load_integral_evaluator(Path("some_file"), cwd=Path("some_folder"))


def test_save_load_integral_evaluator_no_standard(tmpdir, integral_file):
    """Save an integral evaluator file without a standard."""
    ev = IntegralEvaluator(integral_file)
    fout = Path(tmpdir).joinpath("test_no_std")

    evaluator.save_integral_evaluator(ev, fout)

    ev_loaded = evaluator.load_integral_evaluator(fout)

    assert_integral_evaluator_equal(ev, ev_loaded)


def test_save_load_integral_evaluator_relative_path(tmpdir, crd_int_delta):
    """Save and load an integral evaluator when available in relative path only."""
    some_folder = "some_path"
    tmpdir.mkdir(some_folder)
    integral_fout = Path(tmpdir).joinpath(some_folder).joinpath("integrals.csv")
    data_io.integrals.export(crd_int_delta, integral_fout)

    ev = IntegralEvaluator(integral_fout)

    fout = Path(tmpdir).joinpath("test_no_std")

    evaluator.save_integral_evaluator(ev, fout)

    # move the integral to tmpdir location and ensure it's gone from current location
    shutil.move(integral_fout, tmpdir)
    assert not integral_fout.absolute().exists()
    assert Path(tmpdir).joinpath(integral_fout.name).exists()

    ev_loaded = evaluator.load_integral_evaluator(fout, cwd=Path(tmpdir))

    assert_integral_evaluator_equal(ev, ev_loaded)


def test_save_load_integral_evaluator_w_std_timestamp(tmpdir, integral_file):
    """Save and load an integral evaluator with a standard and timestamp."""
    ev = IntegralEvaluator(integral_file)
    ev.standard_timestamp = datetime.datetime.now()
    std = IntegralEvaluator(integral_file)
    ev.standard = std
    fout = Path(tmpdir).joinpath("test_w_std")

    evaluator.save_integral_evaluator(ev, fout)

    ev_loaded = evaluator.load_integral_evaluator(fout)

    assert_integral_evaluator_equal(ev, ev_loaded)
    assert_integral_evaluator_equal(ev.standard, ev_loaded.standard)
