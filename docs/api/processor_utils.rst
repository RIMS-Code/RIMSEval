.. currentmodule:: rimseval.processor_utils

===================
Processor Utilities
===================

Utility functions for the CRD file processor :class:`CRDFileProcessor`.
Many of the mathematically heavy routines
are outsourced here for JITing with
`numba <https://numba.pydata.org/>`_.

-----------------------
:func:`create_packages`
-----------------------

.. autofunction:: create_packages

----------------------------
:func:`dead_time_correction`
----------------------------

.. autofunction:: dead_time_correction

----------------------------
:func:`gaussian_fit_get_max`
----------------------------

.. autofunction:: gaussian_fit_get_max

-------------------------
:func:`integrals_summing`
-------------------------

.. autofunction:: integrals_summing

------------------------
:func:`mass_calibration`
------------------------

.. autofunction:: mass_calibration

-------------------
:func:`mass_to_tof`
-------------------

.. autofunction:: mass_to_tof

---------------------------
:func:`multi_range_indexes`
---------------------------

.. autofunction:: multi_range_indexes

-------------------------------
:func:`sort_data_into_spectrum`
-------------------------------

.. autofunction:: sort_data_into_spectrum

-------------------
:func:`tof_to_mass`
-------------------

.. autofunction:: tof_to_mass
