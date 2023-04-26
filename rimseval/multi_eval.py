"""Evaluate multiple integral files with standards, etc."""

from pathlib import Path
from typing import Union

import pandas as pd

from rimseval.evaluator import IntegralEvaluator


class MultiEvaluator:
    """Evaluate multiple integral files with standards.

    Provides routines to handle a full data evaluation for a project. This includes:
    - All functions of the ``IntegralEvaluator`` class for multiple classes.
    - Read and write of the ``MultiEvaluator`` class to `.meval` file.
    - Export of data to csv, Excel, and LaTeX tables.
    """

    def __init__(self, meval_file: Path = None) -> None:
        """Initialize the MultiEvaluator class.

        :param meval_file: Path to a MultiEvaluator save file.
        """
        self._integral_evaluators = []
        self._meval_save = meval_file

    @property
    def num_of_files(self):
        """Return the number of IntegralEvaluators stored in the MultiEvaluator."""
        return len(self._integral_evaluators)

    def add_integral_evaluator(self, integral_evaluator: IntegralEvaluator) -> None:
        """Add an IntegralEvaluator to the MultiEvaluator.

        :param integral_evaluator: IntegralEvaluator to add.
        """
        pass

    def export(self, export_file: Path = None) -> Union[pd.DataFrame, None]:
        """Export the MultiEvaluator to a file.

        Valid export files are `csv` for comma separated export, `xlsx` for Excel
        export, and `tex` to export a LaTeX table.

        :param export_file: Path to the export file. If ``None``, a pandas DataFrame
            is returned.

        :raises ValueError: If the export file type is not supported.
        """
        if export_file is not None:
            if export_file.suffix not in [".csv", ".xlsx", ".tex"]:
                raise ValueError(
                    "Export file type not supported. Only csv, xlsx, and tex "
                    "are supported file types."
                )
        pass

    def load(self, meval_file: Path) -> None:
        """Load a MultiEvaluator from a save file.

        :param meval_file: Path to a MultiEvaluator save file.
        """
        pass

    def remove_integral_evaluator(self, name: str) -> None:
        """Remove an IntegralEvaluator from the MultiEvaluator.

        :param name: Name of the IntegralEvaluator to remove.
        """
        pass

    def save(self, meval_file: Path = None) -> None:
        """Save the MultiEvaluator to a save file.

        :param meval_file: Path to a MultiEvaluator save file.
        """
        pass
