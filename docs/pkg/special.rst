=======
Special
=======

The ``rimseval`` package has some special functions incorporated,
which allow you to perform various analysis on your data
and your RIMS setup.

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

    from typing import Path

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

    from typing import Path

    from rimseval import CRDFileProcessor
    from rimseval.guis import dt_ions

    my_file = Path("path/to/my_file.crd")
    crd = CRDFileProcessor(crd)
    crd.spectrum_full()

    dt_ions(crd, max_ns=100)
