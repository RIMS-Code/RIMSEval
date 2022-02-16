========================
General Usage of the API
========================

.. note:: Here, the general usage of the API is described.
    Information on filtering data can be found
    :doc:`here <filters>`.

------------------
Convert LST to CRD
------------------

To convert a list file to a CRD file,
use the ``LST2CRD`` class.
Details can be found here: :meth:`rimseval.processor.data_io.lst_to_crd.LST2CRD class`.
If your list file is at ``path/to/file.lst``,
you can convert it to a CRD file as following:

.. code-block:: python

     from pathlib import Path
     from rimseval.data_io import LST2CRD
     file = Path("path/to/file.lst")
     lst = LST2CRD(file_name=file, channel_data=1, tag_data=None)
     lst.read_list_file()
     lst.write_crd()

You will get a `crd` file with the same name
and in the same folder.

.. note::
    Depending on the TDC, the channel number that you need to pass for the
    ``channel_data`` or ``tag_data`` variable are not equal to the channel numbers
    written on front of your TDC.
    For some TDCs, the manufacturer uses different numbers in the software than on the labels.
    The following tables shows models that are implemented in the software,
    for which the channels that you need to set and the stop numbers (labels on the TDC)
    are different.
    Please consult your TDC manual!

    .. list-table:: MCS8A
        :widths: 25 25
        :header-rows: 1

        * - Channel Number
          - TDC Identifier / Label
        * - 9
          - STOP 1
        * - 10
          - STOP 2
        * - 11
          - STOP 3
        * - 12
          - STOP 4
        * - 13
          - STOP 5
        * - 14
          - STOP 6
        * - 15
          - STOP 7

-------------------
Work with CRD files
-------------------

This chapter gradually builds on itself
to give you an overview of the package functionality.

+++++++++++++++
Load a CRD file
+++++++++++++++

Let us assume you have a file named ``my_file.crd``.
Creating a ``Path`` of this file using ``pathlib``,
we can then open it as following:

.. code-block:: python

    from pathlib import Path
    from rimseval import CRDFileProcessor

    my_file = Path("my_file.crd")
    crd = CRDFileProcessor(my_file)
    crd.spectrum_full()

The last command in this sequence processes the spectrum
such that the time of flight array of data is populated.
This command can also be used to reset a dataset at any point.

++++++++++++++++
Mass calibration
++++++++++++++++

To perform a mass calibration,
you need to know at least two time of flights (in microseconds)
and their corresponding mass values.
Group these into a ``numpy.ndarray``,
in which each line contains first the time of flight
and then the associated mass values.

.. code-block:: python

    mass_cal_parameters = np.array([[1, 10], [2, 20]])
    crd.def_mcal = mass_cal_parameters

.. note:: If more than two values are defined,
    a linear optimization is run to determine the best mass calibration.

In above example, the time of flights are ``1`` and ``2``
with associated masses ``10`` and ``20``, respectively.
After setting the parameters,
the mass calibration can be executed as:

.. code-block:: python

    crd.mass_calibrataion()

.. note:: This calibration can also be performed using a ``matplotlib`` GUI.
    For details, see :doc:`here <guis>`.

++++++++++++++++++++
Dead time correction
++++++++++++++++++++

To correct your mass spectrum for dead time effects,
you need to know the number of bins :math:`d` of your TDC
that are dead after an ion hits.
Assuming :math:`d=7`, you can then correct your spectrum
for dead time effects as following:

.. code-block:: python

    crd.dead_time_correction(7)

.. note:: This is only an example of a data evaluation tool.
    More information on all the tools can be found
    :doc:`here <filters>`.

+++++++++++++++++++++++++
Integrals and Backgrounds
+++++++++++++++++++++++++

To set integrals,
you need to prepare a name for each integral (e.g., the isotope name)
and the mass range over which you want to integrate.
Assuming you have two peaks, e.g., :sup:`235`\U and :sup:`238`\U,
you could define the integrals as following:

.. code-block:: python

    integral_names = ["235U", "238U"]
    integral_ranges = np.array([[234.8, 235.2], [237.8, 238.2]])
    crd.def_integrals = integral_names, integral_ranges

.. warning:: Each integral name should only be used once!

In a similar fashion,
you can define backgrounds for a peak.
For example, if you want to define a :math:`0.2`\amu background
for your :sup:`235`\U peak on the left and right of it,
you could set the backgrounds as following:

.. code-block:: python

    bg_names = ["235U", "235U"]
    bg_ranges = np.array([[234.6, 234.8], [235.2, 235.4]])
    crd.def_backgrounds = bg_names, bg_ranges

.. warning:: The backgrounds you define must have the same name as the peaks they are defined for.
    Multiple definitions per background can exist.

To apply the integrals,
simply run:

.. code-block:: python

    crd.integrals_calc(bg_corr=True)

Background correction can be turned on and off by setting the ``bg_corr`` variable
to either ``True`` or ``False``, respectively.
Details on integral background corrections and the math behind it
can be found :doc:`here <../bg/integrals>`.

.. note:: Integral and background definitions can also be performed using a ``matplotlib`` GUI.
    For details, see :doc:`here <guis>`.

+++++++
Results
+++++++

If everything worked as planned,
you can access your processed mass spectrum via multiple variables.
An overview of the available variables can be found
:doc:`here <variables>`.
