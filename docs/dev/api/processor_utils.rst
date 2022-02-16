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
:func:`integrals_bg_corr`
-------------------------

.. autofunction:: integrals_bg_corr

-------------------------
:func:`integrals_summing`
-------------------------

.. autofunction:: integrals_summing

-------------------------------------
:func:`mask_filter_max_ions_per_time`
-------------------------------------

.. autofunction:: mask_filter_max_ions_per_time

-------------------------------------------
:func:`mask_filter_max_ions_per_tof_window`
-------------------------------------------

.. autofunction:: mask_filter_max_ions_per_tof_window

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

-----------------------------------------------
:func:`remove_shots_from_filtered_packages_ind`
-----------------------------------------------

.. autofunction:: remove_shots_from_filtered_packages_ind

----------------------------------
:func:`remove_shots_from_packages`
----------------------------------

.. autofunction:: remove_shots_from_packages

-------------------------------
:func:`sort_data_into_spectrum`
-------------------------------

.. autofunction:: sort_data_into_spectrum

-------------------
:func:`tof_to_mass`
-------------------

.. autofunction:: tof_to_mass
