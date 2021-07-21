"""Interfacing functions to talk to settings, calibrations, GUIs, etc."""

from pathlib import Path

import numpy as np

from rimseval.processor import CRDFileProcessor
from rimseval.compatibility.lion_eval import LIONEvalCal


def read_lion_eval_calfile(fname: Path, crd: CRDFileProcessor) -> None:
    """Read a LIONEval calibration file and set it to instance of crd.

    LIONEval is the first, Python2.7 version of the data evaluation software. This
    routine takes an old calibration file if requested by the user and sets the
    mass calibration, integrals, and background correction information if present.

    :param fname: Filename to mass calibration file.
    :param crd: Instance of the CRDFileProcessor, since we need to set properties
    """
    cal = LIONEvalCal(fname)

    crd.def_mcal = cal.mass_cal
    if cal.integrals:
        names = []
        areas = np.empty((len(cal.integrals), 2))
        for it, line in enumerate(cal.integrals):
            names.append(line[0])
            areas[it][0] = line[1] - line[2]
            areas[it][1] = line[1] + line[3]
        crd.def_integrals = (names, areas)
    # fixme: add background correction stuff once implemented
