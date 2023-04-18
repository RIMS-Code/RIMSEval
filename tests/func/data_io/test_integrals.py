"""Functional tests for the data_io integrals module."""

from pathlib import Path

import pytest
import numpy as np

from rimseval.data_io import integrals


def test_export(crdproc_int):
    """Export of integrals with default filename."""
    integrals.export(crdproc_int)
    fname = Path(crdproc_int.fname)
    fname = fname.with_name(fname.stem + "_int").with_suffix(".csv").absolute()
    assert fname.is_file()


def test_export_fname(crdproc_int, tmpdir):
    """Export of integrals with given filename."""
    fname = Path(tmpdir.strpath).joinpath("test")
    integrals.export(crdproc_int, fname)
    assert fname.with_suffix(".csv").is_file()


def test_export_valueerror(crdproc_int):
    """Export of integrals with CRDProcessor class with no integrals."""
    crdproc_int.integrals = None
    with pytest.raises(ValueError):
        integrals.export(crdproc_int)


def test_load(crdproc_int, tmpdir):
    """Assure that export and load end up with the same data."""
    fname = Path(tmpdir.strpath).joinpath("test.csv")
    integrals.export(crdproc_int, fname)
    name_ld, timestamp_ld, peaks_ld, int_ld = integrals.load(fname)

    assert name_ld == crdproc_int.name
    assert timestamp_ld == crdproc_int.timestamp
    assert peaks_ld == crdproc_int.def_integrals[0]
    np.testing.assert_allclose(int_ld, crdproc_int.integrals)
