"""Methods to save/load IntegralEvaluator classes and MultiEvalator classes."""

import json
from pathlib import Path

from rimseval.evaluator import IntegralEvaluator


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
