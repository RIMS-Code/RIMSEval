"""Process multiple CRD files, open them, handle individually, enable batch runs."""

import gc
from pathlib import Path
from typing import List, Union

from PyQt6 import QtCore
import numpy as np

import rimseval.interfacer
from rimseval.processor import CRDFileProcessor


class MultiFileProcessor(QtCore.QObject):
    """Class to process multiple CRD files at ones.

    Example:
        >>> file_names = [Path("file1.crd"), Path("file2.crd"), Path("file3.crd")]
        >>> mfp = MultiFileProcessor(file_names)
        >>> mfp.num_of_files
        3
        >>> mfp.peak_fwhm = 0.02  # set full with half max for all files
    """

    signal_processed = QtCore.pyqtSignal(str)  # emits the filename that was processed

    def __init__(self, crd_files: List[Path]):
        """Initialize the multiple file processor.

        :param crd_files: List of pathes to the CRD files.
        """
        super().__init__()
        self._num_of_files = len(crd_files)
        self.crd_files = crd_files

        self._files = None

    # PROPERTIES #

    @property
    def files(self) -> List[CRDFileProcessor]:
        """Return a list of files.

        If the files are not opened, it will open and read them.
        """
        if self._files is None:
            self.open_files()
        return self._files

    @property
    def num_of_files(self) -> int:
        """Get the number of files that are in the multiprocessor."""
        return self._num_of_files

    @property
    def peak_fwhm(self) -> float:
        """Get / Set FWHM of each peak.

        The getter returns the average, the setter sets the same for all.

        :return: Average peak FWHM in us.
        """
        if self._files is None:
            self.open_files()
        fwhm = np.zeros(len(self._files))
        for it, file in enumerate(self._files):
            fwhm[it] = file.peak_fwhm
        return np.average(fwhm)

    @peak_fwhm.setter
    def peak_fwhm(self, value: float):
        if self._files is None:
            self.open_files()
        for file in self._files:
            file.peak_fwhm = value

    # METHODS #

    def apply_to_all(self, id: int, opt_mcal: bool = False, bg_corr: bool = False):
        """Take the configuration for the ID file and apply it to all files.

        :param id: Index where the main CRD file is in the list
        :param opt_mcal: Optimize mass calibration if True (default: False)
        :param bc_corr: Perform background correction?
        """
        crd_main = self.files[id]

        mcal = crd_main.def_mcal
        integrals = crd_main.def_integrals
        backgrounds = crd_main.def_backgrounds
        applied_filters = crd_main.applied_filters

        # run file itself first:
        if crd_main.tof is None:
            crd_main.spectrum_full()
        if crd_main.mass is None:
            crd_main.mass_calibration()
        crd_main.calculate_applied_filters()
        if bg_corr and backgrounds is not None:
            bg_corr = True
        else:
            bg_corr = False
        crd_main.integrals_calc(bg_corr=bg_corr)
        self.signal_processed.emit(str(crd_main.fname.name))
        rimseval.interfacer.save_cal_file(crd_main)

        for it, file in enumerate(self.files):
            if it != id:  # skip already done file
                file.spectrum_full()
                if mcal is not None:
                    file.def_mcal = mcal
                    file.mass_calibration()
                    if opt_mcal:
                        file.optimize_mcal()
                if integrals is not None:
                    file.def_integrals = integrals
                if backgrounds is not None:
                    file.def_backgrounds = backgrounds
                if applied_filters is not None:
                    file.applied_filters = applied_filters

                # run the evaluation
                file.calculate_applied_filters()

                # integrals
                file.integrals_calc(bg_corr=bg_corr)

                # save calibration
                rimseval.interfacer.save_cal_file(file)

                # emit signal
                self.signal_processed.emit(str(file.fname.name))

    def close_files(self) -> None:
        """Destroys the files and frees the memory."""
        del self._files
        gc.collect()  # garbage collector
        self._files = None

    def open_files(self) -> None:
        """Open the files and store them in the list."""
        files = [CRDFileProcessor(fname) for fname in self.crd_files]
        self._files = files

    def read_files(self) -> None:
        """Run spectrum_full on all CRD files."""
        for file in self.files:
            file.spectrum_full()
