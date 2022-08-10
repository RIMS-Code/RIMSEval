"""Interfacing functions to talk to settings, calibrations, GUIs, etc."""

import json
from pathlib import Path
from typing import Any

import numpy as np

from rimseval.compatibility.lion_eval import LIONEvalCal
from rimseval.processor import CRDFileProcessor


def read_lion_eval_calfile(crd: CRDFileProcessor, fname: Path = None) -> None:
    """Read a LIONEval calibration file and set it to instance of crd.

    LIONEval is the first, Python2.7 version of the data evaluation software. This
    routine takes an old calibration file if requested by the user and sets the
    mass calibration, integrals, and background correction information if present.

    :param crd: Instance of the CRDFileProcessor, since we need to set properties
    :param fname: Filename to mass calibration file. If `None`, try the same file name
        as for the CRD file, but with `.cal` as an extension.

    :raises OSError: Calibration file does not exist.
    """
    if fname is None:
        fname = crd.fname.with_suffix(".cal")

    if not fname.exists():
        raise OSError(f"The requested calibration file {fname} does not exist.")

    cal = LIONEvalCal(fname)

    if cal.mass_cal is not None:
        crd.def_mcal = cal.mass_cal

    names_int = None
    if cal.integrals:
        names_int = []
        areas_int = np.zeros((len(cal.integrals), 2))
        for it, line in enumerate(cal.integrals):
            names_int.append(line[0])
            areas_int[it][0] = line[1] - line[2]
            areas_int[it][1] = line[1] + line[3]
        crd.def_integrals = (names_int, areas_int)

    if cal.bg_corr and cal.integrals:  # w/o integrals, don't load bgs!
        names_bg = []
        areas_bg = []
        for line in cal.bg_corr:
            name = line[0]
            if name in names_int:  # must be the case for new program
                names_bg.append(name)
                areas_bg.append([line[2], line[3]])
                names_bg.append(name)
                areas_bg.append([line[4], line[5]])

        areas_bg = np.array(areas_bg)
        crd.def_backgrounds = (names_bg, areas_bg)

    if cal.applied_filters is not None:
        crd.applied_filters = cal.applied_filters


def load_cal_file(crd: CRDFileProcessor, fname: Path = None) -> None:
    """Load a calibration file from a specific path / name.

    :param crd: CRD Processor class to load into
    :param fname: Filename and path. If `None`, try file with same name as CRD file but
        `.json` suffix.

    :raises IOError: Calibration file does not exist.
    :raises IOError: JSON file cannot be decoded. JSON error message is returned too.
    """
    if fname is None:
        fname = crd.fname.with_suffix(".json")

    if not fname.exists():
        raise OSError(f"The requested calibration file {fname} does not exist.")

    with fname.open("r", encoding="utf-8") as fin:
        try:
            json_object = json.load(fin)
        except json.decoder.JSONDecodeError as orig_err:
            raise OSError(
                f"Cannot open the calibration file {fname.name}. JSON decode error."
            ) from orig_err

    def entry_loader(key: str, json_obj: Any) -> Any:
        """Return the value of a json_object dictionary if existent, otherwise None."""
        if key in json_obj.keys():
            return json_obj[key]
        else:
            return None

    # mass cal
    mcal = entry_loader("mcal", json_object)
    if mcal is not None:
        crd.def_mcal = np.array(mcal)

    # integrals
    names_int = entry_loader("integral_names", json_object)
    integrals = np.array(entry_loader("integrals", json_object))

    if names_int is not None and integrals is not None:
        crd.def_integrals = names_int, integrals

    # backgrounds
    names_bgs = entry_loader("background_names", json_object)
    backgrounds = np.array(entry_loader("backgrounds", json_object))

    if names_bgs is not None and backgrounds is not None:
        crd.def_backgrounds = names_bgs, backgrounds

    # applied filters
    applied_filters = entry_loader("applied_filters", json_object)
    if applied_filters is not None:
        crd.applied_filters = applied_filters


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
        names_int, integrals = crd.def_integrals
        cal_to_write["integral_names"] = names_int
        cal_to_write["integrals"] = integrals.tolist()

    # backgrounds
    if crd.def_backgrounds is not None:
        names_bg, backgrounds = crd.def_backgrounds
        cal_to_write["background_names"] = names_bg
        cal_to_write["backgrounds"] = backgrounds.tolist()

    # filters
    if crd.applied_filters != {}:
        cal_to_write["applied_filters"] = crd.applied_filters

    json_object = json.dumps(cal_to_write, indent=4)

    fname.write_text(json_object, encoding="utf-8")
