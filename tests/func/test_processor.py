"""Function test for processor."""

from pathlib import Path

import numpy as np

from rimseval.processor import CRDFileProcessor
import rimseval.processor_utils as pu


def test_data_dimension_after_dead_time_correction(crd_file):
    """Ensure ToF and data have the same dimensions - BF 2021-07-23."""
    _, _, _, fname = crd_file
    crd = CRDFileProcessor(Path(fname))
    crd.spectrum_full()
    crd.dead_time_correction(3)

    assert crd.tof.ndim == crd.data.ndim


def test_mass_calibration_2pts(crd_file):
    """Perform mass calibration with two points."""
    _, _, _, fname = crd_file
    params = (13, 42)
    tms = (42.0, 95.0)

    mass_cal = np.zeros((len(tms), 2))
    for it, tm in enumerate(tms):
        mass_cal[it][0] = tm
        mass_cal[it][1] = pu.calculate_mass_square(tm, params[0], params[1])

    # set variables
    crd = CRDFileProcessor(Path(fname))
    crd.spectrum_full()

    crd.def_mcal = mass_cal
    mass_exp = pu.calculate_mass_square(crd.tof, params[0], params[1])

    crd.mass_calibration()
    mass_rec = crd.mass
    print(tms)
    np.testing.assert_almost_equal(mass_rec, mass_exp)
    assert crd.mass.ndim == crd.tof.ndim
