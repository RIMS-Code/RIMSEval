"""Handle import and export of integrals."""

import datetime
from pathlib import Path
from typing import List, Tuple

import numpy as np

from rimseval.processor import CRDFileProcessor


def export(crd: CRDFileProcessor, fname: Path = None) -> None:
    """Export integrals to csv file.

    If no file name is given, the file name of the CRD file is used, '_int' is added,
    and '.csv' is used as the extension.

    Header lines start with a #, all data lines are comma separated and labels for
    rows and columns are given within the data.

    :param crd: CRD file.
    :param fname: File name to export to (optional): csv file.

    :raises ValueError: CRD file has no integrals.
    """

    if crd.integrals is None:
        raise ValueError("CRD file has no integrals.")

    if fname is None:
        fname = (
            crd.fname.with_name(crd.fname.stem + "_int").with_suffix(".csv").absolute()
        )
    else:
        if not fname.suffix == ".csv":
            fname = fname.with_suffix(".csv").absolute()

    peak_names = crd.def_integrals[0]

    with open(fname, "w") as f:
        f.write(f"# CRD File: {crd.name}\n")
        f.write(f"# Timestamp: {crd.timestamp}\n")
        f.write("Peak,Integral,Error\n")
        for it, peak in enumerate(peak_names):
            f.write(f"{peak},{crd.integrals[it][0]},{crd.integrals[it][1]}\n")


def load(fname: Path) -> Tuple[str, datetime.datetime, List, np.ndarray]:
    """Load an integral csv file.

    :param fname: File name to load from.

    :return: Integral data.
        1. CRD file name (equiv to ``crd.name``)
        2. Timestamp (equiv to ``crd.timestamp``)
        3. Peak names (equiv to ``crd.def_integrals[0]``)
        4. Integrals (equiv to ``crd.integrals``)
    """
    with open(fname) as f:
        lines = f.readlines()

    crd_name = None
    timestamp = None

    for it, line in enumerate(lines):
        if line[0] == "#":  # header
            if line.startswith("# CRD File:"):
                crd_name = line.split(":")[1].strip()
            if line.startswith("# Timestamp:"):
                tmp = line.split(":")[1:]
                timestamp = datetime.datetime.strptime(
                    ":".join(tmp).strip(), "%Y-%m-%d %H:%M:%S"
                )

    peak_names = []
    integrals = []
    for line in lines[3:]:
        peak_names.append(line.split(",")[0])
        integrals.append([float(line.split(",")[1]), float(line.split(",")[2])])

    return crd_name, timestamp, peak_names, np.array(integrals)
