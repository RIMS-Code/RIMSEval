"""Methods to save/load IntegralEvaluator classes and MultiEvalator classes."""

import datetime
import json
from pathlib import Path
from typing import Union

from rimseval.evaluator import IntegralEvaluator


def load_integral_evaluator(
    din: Union[Path, str], cwd: Path = None
) -> IntegralEvaluator:
    """Load an integral evaluation class from an `.eval` file.

    Files will be loaded from an absolute path first, if not available, the routine
    will try to look for the file relative to the working directory.

    :param din: Path to the input file. Suffix `.eval` will be added if not
        present. Alternatively, the json content can be given as a string.
    :param cwd: Current working directory, will be used to look for integral files if
        given and file cannot be found in the absolute path saved in the `.eval` file.

    :return: IntegralEvaluator class with all information as stored.

    :raises TypeError: ``din`` is of bad type.
    :raises FileNotFoundError: If a file cannot be found.
    """
    if isinstance(din, Path):
        din = din.with_suffix(".eval")
        with open(din) as f:
            eval_dict = json.load(f)
    elif isinstance(din, str):
        eval_dict = json.loads(din)
    else:
        raise TypeError(f"Input must be a Path or string, not {type(din)}.")

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


def save_integral_evaluator(
    ev: IntegralEvaluator, dout: Path = None
) -> Union[None, str]:
    """Save an integral evaluation class with all information to an `.eval` file.

    The eval file will be in json format. The file contains references to the
    absolute path of each integral file, , the absolute path of each standard file,
    the set of correlations set by the user (requested by the user), and the
    timestamp of the standard.

    :return: None (if written to file) or json string (if ``dout`` is ``None``).

    :param ev: IntegralEvaluator class to save.
    :param dout: Path to the output file. Suffix `.eval` will be added if not
        present. If ``None`` is given, the json string will be returned.

    :raises TypeError: If ``ev`` is not of type ``IntegralEvaluator`` or ``dout``
        is not of type ``pathlib.Path``.
    """
    if not isinstance(ev, IntegralEvaluator):
        raise TypeError("Input must be of type IntegralEvaluator.")
    if not isinstance(dout, Path) and dout is not None:
        raise TypeError("Path must be of type pathlib.Path.")

    if dout is not None:
        dout = dout.with_suffix(".eval")

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
    if dout is None:
        return json.dumps(eval_dict, indent=4)
    else:
        with open(dout, "w") as f:
            json.dump(eval_dict, f, indent=4)
