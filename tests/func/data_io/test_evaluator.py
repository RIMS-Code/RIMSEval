"""Tests for saving/loading evaluator classes."""

from pathlib import Path
import pytest
import numpy as np

from rimseval.data_io import evaluator
from rimseval.evaluator import IntegralEvaluator


def test_save_load_integral_evaluator_no_standard(tmpdir, integral_file):
    """Save an integral evaluator file without a standard."""
    ev = IntegralEvaluator(integral_file)
    fout = Path(tmpdir).joinpath("test_no_std")

    evaluator.save_integral_evaluator(ev, fout)
    assert fout.with_suffix(".eval").exists()


def test_save_load_integral_evaluator(tmpdir, integral_file):
    """Save and load an integral evaluator with a standard."""
    ev = IntegralEvaluator(integral_file)
    std = IntegralEvaluator(integral_file)
    ev.standard = std
    fout = Path(tmpdir).joinpath("test_w_std")

    evaluator.save_integral_evaluator(ev, fout)
    assert fout.with_suffix(".eval").exists()
