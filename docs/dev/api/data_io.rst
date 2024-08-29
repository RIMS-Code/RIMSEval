###########################
Data Input and Output (I/O)
###########################

The routines in this folder
deal with data input and output.
Transformers for converting list files
to `CRD` files can also be found here.
Also export functions are found here.



.. currentmodule:: rimseval.data_io.crd_reader

------------------
:class:`CRDReader`
------------------

.. autoclass:: CRDReader
    :members:
    :undoc-members:



.. currentmodule:: rimseval.data_io.crd_utils

------------------
CRD File Utilities
------------------

Header definitions, enums, and JIT compiled functions
for processing `CRD` files.

***********
Definitions
***********

.. property:: CURRENT_DEFAULTS
    :annotation: Current default CRD header information.

.. property:: HEADER_START
    :annotation: Defaults sizes for the header values to read in.

******************
:class:`CRDHeader`
******************

.. autoclass:: CRDHeader
    :members:
    :undoc-members:


**************************
:func:`shot_to_tof_mapper`
**************************

.. autofunction:: shot_to_tof_mapper



.. currentmodule:: rimseval.data_io.lst_to_crd

---------------------------
LST to CRD File Transformer
---------------------------

.. autoclass:: LST2CRD
    :members:
    :undoc-members:



.. currentmodule:: rimseval.data_io.lst_utils

------------------
LST File Utilities
------------------

JIT compiled functions
for processing `LST` files.

************************
:func:`ascii_to_ndarray`
************************

.. autofunction:: ascii_to_ndarray

****************************
:func:`get_sweep_time_ascii`
****************************

.. autofunction:: get_sweep_time_ascii

********************************
:func:`transfer_lst_to_crd_data`
********************************

.. autofunction:: transfer_lst_to_crd_data



.. py:currentmodule:: rimseval.data_io.excel_writer

------------
Excel Writer
------------

**************************
:func:`workup_file_writer`
**************************

.. autofunction:: workup_file_writer



.. py:currentmodule:: rimseval.data_io.integrals

------------------------
Integral export / import
------------------------

**************
:func:`export`
**************

.. autofunction:: export

************
:func:`load`
************

.. autofunction:: load



.. py:currentmodule:: rimseval.data_io.export

----------------
Export functions
----------------

********************
:func:`tof_spectrum`
********************

.. autofunction:: tof_spectrum

*********************
:func:`mass_spectrum`
*********************

.. autofunction:: mass_spectrum
