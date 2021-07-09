"""Initialization of the rimseval package."""

from . import data_io
from . import processor

# Package information
__version__ = "0.0.0"

__title__ = "rimseval"
__description__ = (
    "Evaluate resonance ionization mass spectrometry measurements, correct, and "
    "filter. Contains a reader for crd files (Chicago Raw Data) but can also convert "
    "FastComTec lst files to crd."
)

# Todo
__uri__ = "Todo Docs Link"
__author__ = "Reto Trappitsch"

__license__ = "MIT"
__copyright__ = "Copyright (c) 2020, Reto Trappitsch"
