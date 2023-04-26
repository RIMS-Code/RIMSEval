"""Resonance Ionization Mass Spectrometry (RIMS) Data Evaluation for CRD Files."""

from . import data_io
from . import guis
from . import interfacer
from . import utilities
from .evaluator import IntegralEvaluator
from .multi_eval import MultiEvaluator
from .multi_proc import MultiFileProcessor
from .processor import CRDFileProcessor

VERBOSITY = 0

__all__ = [
    "VERBOSITY",
    "CRDFileProcessor",
    "data_io",
    "guis",
    "interfacer",
    "IntegralEvaluator",
    "MultiEvaluator",
    "MultiFileProcessor",
    "utilities",
]

# Package information
__version__ = "2.0.1"

__title__ = "rimseval"
__description__ = (
    "Evaluate resonance ionization mass spectrometry measurements, correct, and "
    "filter. Contains a reader for crd files (Chicago Raw Data) but can also convert "
    "FastComTec lst files to crd."
)

__uri__ = "https://rimseval.readthedocs.io"
__author__ = "Reto Trappitsch"

__license__ = "MIT"
__copyright__ = "Copyright (c) 2023, Reto Trappitsch"
