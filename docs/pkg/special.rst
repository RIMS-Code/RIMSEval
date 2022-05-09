=======
Special
=======

The ``rimseval`` package has some special functions incorporated,
which allow you to perform various analysis on your data
and your RIMS setup.

------------------------
Excel Workup file writer
------------------------

Sometimes,
it is useful to further process multiple evaluated spectra
in an Excel file.
You can use the
:meth:`rimseval.data_io.excel_writer.workup_file_writer`
to create a workbook to continue working on your data.
This workbook will contain integrals,
:math:`\delta`-values.

Here is an example usage for a file
that would contain zirconium data.
Note that :math:`\delta`-values would usually
be normalized to the most abundant :sup:`90`\Zr,
however, we would like to normalize here
to :sup:`94`\Zr.
This is accomplished by setting the according
normalization isotope of ``iniabu``.

The following code assumes that ``crd`` is
an instance of ``CRDFileProcessor``
and that a mass calibration has been performed
and integrals have been set for zirconium isotopes.

.. code-block:: python

    from pathlib import Path

    from rimseval.data_io import excel_writer
    from rimseval.utilities import ini

    # set Zr normalization isotope to Zr-94
    ini.norm_isos = {"Zr": "Zr-94"}

    # Write the excel file
    my_output_file = Path("workup_file.xlsx")
    excel_writer.workup_file_writer(crd, my_output_file)

-------------------
Hist. ions per shot
-------------------

For appropriate dead time correction
we assume that all counts are Poisson distributed.
This means that the histogram of number of ions per shot
should follow the following distribution:

.. math::

    f(k) = \exp(-\mu) \frac{\mu^{k}}{k!}

Here, :math:`k` is the number of ions per shot,
:math:`f(k)` is the frequency of ions in bin :math:`k`,
and :math:`\mu` is the number of ions divided by the number of shots.

There is a GUI function implemented
that allows you to directly plot a histogram of ions per shot
and compare it to the theoretical assumption.
The following code shows you how to do this:

.. code-block:: python

    from pathlib import Path

    from rimseval import CRDFileProcessor
    from rimseval.guis import hist_nof_shots

    my_file = Path("path/to/my_file.crd")
    crd = CRDFileProcessor(crd)
    crd.spectrum_full()

    nof_ions_per_shot(crd)

This will open a  ``matplotlib`` window and display the histogram.

----------------------
Hist. time differences
----------------------

To debug your system,
i.e., to determine if the detector is ringing,
it can be useful to determine the time difference between all ions
in individual shots that have more than one ion arriving.

For every shot with more than one ion,
we determine the time difference between these shots
and create a histogram of all of these time differences.
For a shot with :math:`n` ions arriving,
there will be :math:`\frac{(n-1)n}{2}` time differences determined.

.. warning:: This is different from the previous ``LIONEval`` software,
    where time differences were only determined between subsequent ions.
    Here, all ion time differences are taken into account now.

To calculate and display this plot,
some example code is given below.
Note that ``max_ns=100`` will set
the upper limit of the x-axis to 100ns.
This number is of course user-defined and can be omitted.

.. code-block:: python

    from pathlib import Path

    from rimseval import CRDFileProcessor
    from rimseval.guis import dt_ions

    my_file = Path("path/to/my_file.crd")
    crd = CRDFileProcessor(crd)
    crd.spectrum_full()

    dt_ions(crd, max_ns=100)


---------------------
Integrals per package
---------------------

If you have split your spectrum into packages
and have defined integrals,
this routine allows you to show a figure
of all integrals per package
versus the number of the package.
This is especially interesting to find bursts in your measurements,
i.e., when measuring with the desorption laser.

The following example shows how the plot is generated:

.. code-block:: python

    from pathlib import Path

    from rimseval import CRDFileProcessor
    from rimseval.guis import integrals_packages

    my_file = Path("path/to/my_file.crd")
    crd = CRDFileProcessor(crd)
    crd.spectrum_full()

    integrals_packages(crd)
