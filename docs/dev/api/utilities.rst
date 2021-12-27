=================
Utility functions
=================

This folder contains further functions
that help with various tasks.
These functions are split up into individual files,
depending on their specific tasks.

.. currentmodule:: rimseval.utilities.fitting

-----------------
Fitting functions
-----------------

****************
:func:`gaussian`
****************

.. autofunction:: gaussian

**************************
:func:`residuals_gaussian`
**************************

.. autofunction:: residuals_gaussian



.. currentmodule:: rimseval.utilities.peirce

----------------------------
Peirce's rejection criterion
----------------------------

Functions to deal with Peirce's rejection criterion.
See `Wikipedia <https://en.wikipedia.org/wiki/Peirce%27s_criterion>`_
and `this PDF file <https://www.eol.ucar.edu/system/files/piercescriterion.pdf>`_
for details.

************************
:func:`peirce_criterion`
************************

.. autofunction:: peirce_criterion

***********************
:func:`reject_outliers`
***********************

.. autofunction:: reject_outliers



.. py:currentmodule:: rimseval.utilities.string_transformer

----------------------
String transformations
----------------------

Convert strings around to interface with various conventions.
For example, routines that will format isotopes using LaTeX
for labels in plots, etc., will go here.

*********************
:func:`iso_to_iniabu`
*********************

.. autofunction:: iso_to_iniabu



.. py:currentmodule:: rimseval.utilities.utils

---------
Utilities
---------

Further utility routines that do not fit anywhere else.

.. autofunction:: not_index