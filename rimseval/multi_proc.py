"""Process multiple CRD files, open them, handle individually, enable batch runs."""

from pathlib import Path
from typing import List

import numpy as np
from PyQt6 import QtCore

import rimseval
from rimseval.multi_template import MultiTemplate
from rimseval.processor import CRDFileProcessor


class MultiFileProcessor(QtCore.QObject, MultiTemplate):
    """Class to process multiple CRD files at ones.

    Example:
        >>> file_names = [Path("file1.crd"), Path("file2.crd"), Path("file3.crd")]
        >>> mfp = MultiFileProcessor(file_names)
        >>> mfp.num_of_files
        3
        >>> mfp.peak_fwhm = 0.02  # set full with half max for all files
    """

    signal_processed = QtCore.pyqtSignal(str)  # emits the filename that was processed

    def __init__(self, file_paths: List[Path]):
        """Initialize the multiple file processor.

        :param file_paths: List of pathes to the CRD files.
        """
        super().__init__(file_paths=file_paths)

    # PROPERTIES #

    @property
    def peak_fwhm(self) -> float:
        """Get / Set FWHM of each peak.

        The getter returns the average, the setter sets the same for all.

        :return: Average peak FWHM in us.
        """
        fwhm = np.zeros(len(self.files))
        for it, file in enumerate(self.files):
            fwhm[it] = file.peak_fwhm
        return np.average(fwhm)

    @peak_fwhm.setter
    def peak_fwhm(self, value: float):
        for file in self.files:
            file.peak_fwhm = value

    # METHODS #

    def apply_to_all(self, id: int, opt_mcal: bool = False, bg_corr: bool = False):
        """Take the configuration for the ID file and apply it to all files.

        :param id: Index where the main CRD file is in the list
        :param opt_mcal: Optimize mass calibration if True (default: False)
        :param bg_corr: Perform background correction?
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
        crd_main.integrals_calc_delta()
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
                if backgrounds is not None:
                    file.def_backgrounds = backgrounds
                if integrals is not None:
                    file.def_integrals = integrals
                if applied_filters is not None:
                    file.applied_filters = applied_filters

                # run the evaluation
                file.calculate_applied_filters()

                # integrals
                file.integrals_calc(bg_corr=bg_corr)
                file.integrals_calc_delta()

                # save calibration
                rimseval.interfacer.save_cal_file(file)

                # emit signal
                self.signal_processed.emit(str(file.fname.name))

    def load_calibrations(self, secondary_cal: Path = None) -> None:
        """Load calibration files for all CRDs.

        This routine checks first if a calibration file with the same name exists.
        If so, it will be loaded. If no primary calibration is present and a secondary
        calibration filename is given, the program will try to load that one if it
        exists. Otherwise, no calibration will be loaded.

        :param secondary_cal: File for secondary calibration. Will only be used if it
            exists.
        """
        for crd in self.files:
            self.load_calibration_single(crd, secondary_cal=secondary_cal)

    @staticmethod
    def load_calibration_single(
        crd: CRDFileProcessor, secondary_cal: Path = None
    ) -> None:
        """Load a single calibration for a CRD file.

        Loads the primary calibration (i.e., the one with the same name but .json
        qualifier) if it exists. Otherwise, if a secondary calibration is given,
        it will try to load that one. If that file does not exist either, nothing
        will be done.

        :param crd: CRD file to load the calibration for.
        :param secondary_cal: Optional, calibration to fall back on if no primary
            calibration is available.
        """
        if (calfile := crd.fname.with_suffix(".json")).is_file():
            pass
        elif secondary_cal is not None and (calfile := secondary_cal).is_file():
            pass
        else:
            return

        rimseval.interfacer.load_cal_file(crd, calfile)

    def open_additional_files(
        self, fnames: List[Path], read_files=True, secondary_cal=None
    ) -> None:
        """Open additional files to the ones already opened.

        Files will be appended to the list, no sorting.

        :param fnames: List of filenames for the additional files to be opened.
        :param read_files: Read the files after opening?
        :param secondary_cal: Secondary calibration file for loading calibrations.
        """
        start_index = len(self._files)
        super().open_additional_files(fnames)

        for it in range(start_index, len(self._files)):
            fl = self._files[it]
            if read_files:
                fl.spectrum_full()
            self.load_calibration_single(fl, secondary_cal=secondary_cal)

    def read_files(self) -> None:
        """Run spectrum_full on all CRD files."""
        for file in self.files:
            file.spectrum_full()
