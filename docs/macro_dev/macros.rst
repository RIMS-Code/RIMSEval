=================
Macro Development
=================

Here we describe how you can develop macros to run.
In the GUI,
the macros are run with the given interface.
In the ``CRDFileProcessor``,
you can run your own macros using the ``run_macro`` routine:
:meth:`rimseval.processor.CRDFileProcessor.run_macro`

Templates for macros and example python files can be found on
`GitHub <https://github.com/RIMS-Code/RIMSEval/tree/main/macros>`_.

An overview of useful variables can be found in
:doc:`here <../pkg/variables>`.

------------
Introduction
------------

A macro requires a specific structure.
If you need to import packages,
please follow best norms.

.. warning:: Do not import full packages into the namespace.
    This could yield to odd behavior down the line.

For example, if you want to use ``numpy`` functions,
you should import is as:

.. code-block:: python

    import numpy as np

If you want to import other routines from ``rimseval``,
use absolute imports.

Your macro can have as many subroutines as you like.
These will all be imported by the macro reader.
You must have a routine called ``calc``
that runs your calculations.
If you have more subroutines,
these need to be called from within your main calculation function.
The following template lines out the start of a macro.
If you use an editor that supports type hints,
autocompletion will work.
Information on type hints can be found
`here <https://docs.python.org/3/library/typing.html>`_.
Note the usage of absolute imports to enable type hints.

.. code-block::

    from rimseval.processor import CRDFileProcessor

    def calc(crd: CRDFileProcessor) -> None:
        """Macro template.

        :param crd: CRD file processor that will be passed to the macro.
        """
        # your code goes here

--------------
Basic examples
--------------

Below are two examples that show you how to implement, e.g.,
how to filter on full data sets and how to filter packages.

+++++++++++++++++++++++++++++++++++++
Example: Filter maximum ions per shot
+++++++++++++++++++++++++++++++++++++

Here is a re-implementation of the
:meth:`rimseval.processor.CRDFileProcessor.filter_max_ions_per_shot`
method in the form of a macro.

.. code-block:: python

    import numpy as np

    from rimseval.processor import CRDFileProcessor


    def calc(crd: CRDFileProcessor) -> None:
        """Macro to filter out all shots with more than 3 ions.

        :param crd: CRD file processor that will be passed to the macro.
        """
        # maximum ions per shot to be filtered out
        max_ions = 3

        # create a numpy mask that selects the filters we want to filter
        shots_rejected = np.where(crd.ions_per_shot > max_ions)[0]

        # pass the rejected shots array to the routine that will filter everything
        crd.apply_individual_shots_filter(shots_rejected)

As discussed above, the macro must be in the given template form.
We define here a ``shots_rejected`` array (a ``numpy.ndarray``),
which lists the shots that we want to reject.
Finally,
we pass the array of rejected shots to the in-built function
that processes the shots further and handles everything down the line.
This is the ``crd.apply_individual_shots_filter()`` routine.
More detailed documentation on this routine can be found in
:meth:`rimseval.processor.CRDFileProcessor.apply_individual_shots_filter`.

++++++++++++++++++++++++++++++++++++++++
Example: Filter maximum ions per package
++++++++++++++++++++++++++++++++++++++++

Here is a macro that re-implements the maximum number of ions per package filter.
Details on the filter can be found in
:meth:`rimseval.processor.CRDFileProcessor.filter_max_ions_per_shot`.


.. code-block:: python

    import numpy as np

    from rimseval.processor import CRDFileProcessor


    def calc(crd: CRDFileProcessor) -> None:
        """Macro to filter out all packages with more than 4 ions.

        Here we assume, that you have already created packages using the built-in function.
        Package data is therefore available.

        :param crd: CRD file processor that will be passed to the macro.
        """
        # maximum ions per pkg to be filtered out
        max_ions = 4

        # calculate total ions in all the packages
        total_ions_per_pkg = np.sum(crd.data_pkg, axis=1)

        # find packages that need deletion
        pkg_to_delete = np.where(total_ions_per_pkg > max_ions)[0]

        # now delete the packages that are not needed
        crd.data_pkg = np.delete(crd.data_pkg, pkg_to_delete, axis=0)

        # update the number of shots per package array: delete entries of deleted packages
        crd.nof_shots_pkg = np.delete(crd.nof_shots_pkg, pkg_to_delete, axis=0)

        # finally, we need to update the ``crd.data`` and ``crd.nof_shots`` entries
        crd.data = np.sum(crd.data_pkg, axis=0)
        crd.nof_shots = np.sum(crd.nof_shots_pkg)

First we calculate the sum of ions per package by summing over the ``crd.data_pkg`` array.
Note that we need to specify the axis in this case since we want to sum
over packages, not over the spectra.
Using the ``numpy.where`` function, we then locate packages that meet
the rejection criterion. The ``pkg_to_delete`` variable stores the index of the packages.
Using ``numpy.delete``, we then delete the rejectable packages from
``crd.data_pkg`` and ``crd.nof_shots_pkg``.
Finally, we need to update ``crd.data`` and ``crd.nof_shots``
such that the non-packaged data is updated as well.

.. note:: Before the macro runs, data must have been packaged using the built-in method.
