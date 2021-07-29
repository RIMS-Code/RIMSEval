"""Interfacing functions to talk to settings, calibrations, GUIs, etc."""

import json
from pathlib import Path
from typing import Any

import numpy as np

from rimseval.processor import CRDFileProcessor
from rimseval.compatibility.lion_eval import LIONEvalCal


def read_lion_eval_calfile(crd: CRDFileProcessor, fname: Path = None) -> None:
    """Read a LIONEval calibration file and set it to instance of crd.

    LIONEval is the first, Python2.7 version of the data evaluation software. This
    routine takes an old calibration file if requested by the user and sets the
    mass calibration, integrals, and background correction information if present.

    :param crd: Instance of the CRDFileProcessor, since we need to set properties
    :param fname: Filename to mass calibration file. If `None`, try the same file name
        as for the CRD file, but with `.cal` as an extension.
    """
    if fname is None:
        fname = crd.fname.with_suffix(".cal")

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


def load_cal_file(crd: CRDFileProcessor, fname: Path = None) -> None:
    """Load a calibration file from a specific path / name.

    :param crd: CRD Processor class to load into
    :param fname: Filename and path. If `None`, try file with same name as CRD file but
        `.json` suffix.
    """
    if fname is None:
        fname = crd.fname.with_suffix(".json")

    with fname.open("r") as fin:
        json_object = json.load(fin)

    def entry_loader(key: str, json_obj: Any) -> Any:
        """Returns the value of a json_object dictionary if existent, otherwise None."""
        if key in json_obj.keys():
            return json_obj[key]
        else:
            return None

    # mass cal
    crd.def_mcal = np.array(entry_loader("mcal", json_object))

    # integrals
    names = entry_loader("integral_names", json_object)
    integrals = np.array(entry_loader("integrals", json_object))

    if names is not None and integrals is not None:
        crd.def_integrals = names, integrals


def save_cal_file(crd: CRDFileProcessor, fname: Path = None) -> None:
    """Save a calibration file to a specific path / name.

    Note: The new calibration files are `.json` files and not `.cal` files.

    :param crd: CRD class instance to read all the data from.
    :param fname: Filename to save to to. If None, will save in folder / name of
        original crd file name, but with '.cal' ending.
    """
    if fname is None:
        fname = crd.fname.with_suffix(".json")

    cal_to_write = {}

    # mass cal
    if crd.def_mcal is not None:
        cal_to_write["mcal"] = crd.def_mcal.tolist()

    # integrals
    if crd.def_integrals is not None:
        names, integrals = crd.def_integrals
        cal_to_write["integral_names"] = names
        cal_to_write["integrals"] = integrals.tolist()

    json_object = json.dumps(cal_to_write, indent=4)

    with fname.open("w") as fout:
        fname.write_text(json_object)
