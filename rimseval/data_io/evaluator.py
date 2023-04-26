"""Methods to save/load IntegralEvaluator classes and MultiEvalator classes."""

import datetime
import json
from pathlib import Path

from rimseval.evaluator import IntegralEvaluator


def load_integral_evaluator(fname_in: Path, cwd: Path = None) -> IntegralEvaluator:
    """Load an integral evaluation class from an `.eval` file.

    Files will be loaded from an absolute path first, if not available, the routine
    will try to look for the file relative to the working directory.

    :param fname_in: Path to the input file. Suffix `.eval` will be added if not
        present.
    :param cwd: Current working directory, will be used to look for integral files if
        given and file cannot be found in the absolute path saved in the `.eval` file.

    :return: IntegralEvaluator class with all information as stored.

    :raises FileNotFoundError: If a file cannot be found.
    """
    fname_in = fname_in.with_suffix(".eval")

    with open(fname_in) as f:
        eval_dict = json.load(f)

    # create the evaluator
    ev = IntegralEvaluator()
    sample_fnames = [Path(p) for p in eval_dict["sample_files"]]

    for fl in sample_fnames:
        if not fl.exists() and cwd is not None:
            fl = cwd.joinpath(fl.name)
        elif not fl.exists():
            raise FileNotFoundError(f"Could not find file {fl}")

        if not fl.exists():
            raise FileNotFoundError(f"Could not find file {fl}")

        ev.add_integral(fl)

    ev.correlation_set = set(eval_dict["correlations"])

    # add the standard if present
    if eval_dict["standard_files"] is not None:
        std = IntegralEvaluator()
        std_fnames = [Path(p) for p in eval_dict["standard_files"]]
        for fl in std_fnames:
            if not fl.exists():
                fl = Path.cwd().joinpath(fl)

            if not fl.exists():
                raise FileNotFoundError(f"Could not find file {fl}")
            std.add_integral(fl)
        ev.standard = std
        if (tmstmp := eval_dict["standard_timestamp"]) is not None:
            ev.standard_timestamp = datetime.datetime.fromisoformat(tmstmp)

    return ev


def save_integral_evaluator(ev: IntegralEvaluator, fname_out: Path) -> None:
    """Save an integral evaluation class with all information to an `.eval` file.

    The eval file will be in json format. The file contains references to the
    absolute path of each integral file, , the absolute path of each standard file,
    the set of correlations set by the user (requested by the user), and the
    timestamp of the standard.

    :param ev: IntegralEvaluator class to save.
    :param fname_out: Path to the output file. Suffix `.eval` will be added if not
        present.

    :raises TypeError: If the path is not of type ``pathlib.Path``.
    """
    if not isinstance(fname_out, Path):
        raise TypeError("Path must be of type pathlib.Path.")

    fname_out = fname_out.with_suffix(".eval")

    # create the dictionary
    eval_dict = {
        "sample_files": [str(p) for p in ev.file_names],
        "correlations": list(ev.correlation_set),
    }
    if ev.standard is None:
        eval_dict["standard_files"] = None
    else:
        eval_dict["standard_files"] = [str(p) for p in ev.standard.file_names]

    if ev.standard_timestamp is None:
        eval_dict["standard_timestamp"] = None
    else:
        eval_dict["standard_timestamp"] = ev.standard_timestamp.isoformat()

    # save the dictionary
    with open(fname_out, "w") as f:
        json.dump(eval_dict, f, indent=4)
