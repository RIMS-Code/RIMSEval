===============================
Filters & Data Evaluation Tools
===============================

Here,
we describe the individual filters
that can be applied to the data.
Note that these are not just filters in the strict sense,
but also further data evaluation tools, e.g., deadtime correction.
References to the individual API classes are given as well.

--------------------
Dead time correction
--------------------

API Documentation:
:meth:`rimseval.processor.CRDFileProcessor.dead_time_correction`

This method applies a dead time correction to the whole spectrum.
If packages were set, the dead time correction is performed
on each package individually as well.
The method takes the number of dead bins after the original bin.

The dead time correction is calculated as described in
`Stephan et al. (1994) <https://doi.org/10.1116/1.579255>`_.
In brief, be :math:`N(i)` the total ion count in channel :math:`i` and
:math:`n_s` and total number of shots. We can then calculate
a value :math:`N'(i)` as:

.. math:: N'(i) = n_{s} - \sum_{i-k}^{i} N(i)

Here, :math:`k` is the number of dead channels after an ion strikes the detector.
For every channel and using the quantity :math:`N'(i)`, we can then calculate
the corrected number of counts :math:`N_{\mathrm{corr}}(i)` as:

.. math:: N_{\mathrm{corr}}(i) = -n_{s} \cdot \log \left( 1 - \frac{N(i)}{N'(i)} \right)

.. note:: The dead time correction should be run after all other filters
    have been applied to the spectrum!

------------------------
Maximum ions per package
------------------------

API Documentation:
:meth:`rimseval.processor.CRDFileProcessor.filter_max_ions_per_pkg`

This filter acts on packages.
It takes one argument,
namely the maximum number of ions that are allowed to be in a package.
Any package with more ions
will be removed from the evaluation process.
This filter automatically updates the variable
that holds the number of shots that are being evaluated.
Furthermore, it also updates the mass spectrum data,
which is subsequently used, e.g.,
to calculate integrals.

.. note:: If you run this filter multiple times,
    you must make sure that you are lowering
    the maximum number of allowed ions.
    Otherwise,
    please reset the data set before running a again.

**See also:**

- :meth:`rimseval.processor.CRDFileProcessor.packages`
- :meth:`rimseval.processor.CRDFileProcessor.spectrum_full`


---------------------
Maximum ions per shot
---------------------


API Documentation:
:meth:`rimseval.processor.CRDFileProcessor.filter_max_ions_per_shot`

This filter acts on individual.
It takes one argument,
namely the maximum number of ions that are allowed to be in a shot.
Any shot with more ions
will be removed from the evaluation process.
This filter automatically updates the variable
that holds the number of shots that are being evaluated.
Furthermore, it also updates the mass spectrum data,
which is subsequently used, e.g.,package
to calculate integrals.

.. note:: If you run this filter multiple times,
    you must make sure that you are lowering
    the maximum number of allowed ions.
    Otherwise,
    please reset the data set before running a again.

If packages are defined,
this filter will remove the shots from the existing packages as well.
This means that you can end up with packages that contain less shots
than what you defined when you created them!

.. note:: If you filter for maximum ions in packages and maximum ions per shot,
    the preferred way of achieving this is to filter the packages first.
    Otherwise, packages will be created with shots that are not in order of each other.
    While in practice, this will most likely not change your setup by a lot,
    in theory the preferred way should be "more correct".

**See also:**

- :meth:`rimseval.processor.CRDFileProcessor.spectrum_full`



----------------------------------------------------
Package countrate filter based on Peirce's criterion
----------------------------------------------------

This method filters packages based on Peirce's criterion,
assuming that they should all contain the same number of counts.
The user has to decide if such an assumptions makes sense or not.

More details on Peirce's criterion can be found on
`Wikipedia <https://en.wikipedia.org/wiki/Peirce's_criterion>`_.
The algorithm implemented here is after
`Ross (2013) <http://www.eol.ucar.edu/system/files/piercescriterion.pdf>`_.

.. warning:: Running this filter more than once might lead to weird results!

**See also:**

- :meth:`rimseval.processor.CRDFileProcessor.packages`
- :meth:`rimseval.processor.CRDFileProcessor.spectrum_full`

---------------------------------------------------------------
Package :math:`\delta`-value filter based on Peirce's criterion
---------------------------------------------------------------

**ToDo: Describe once the routine actually works properly!**
