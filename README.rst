========================
RIMS Evaluation Software
========================


.. image:: https://github.com/RIMS-Code/RIMSEval/workflows/rimseval-tests/badge.svg?branch=main
    :target: https://github.com/RIMS-Code/RIMSEval
    :alt: Tests rimseval
.. image:: https://img.shields.io/pypi/v/rimseval?color=informational
    :target: https://pypi.org/project/rimseval/
    :alt: PyPi rimseval
.. image:: https://readthedocs.org/projects/rimseval/badge/?version=latest
    :target: https://rimseval.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status
.. image:: https://codecov.io/gh/RIMS-Code/RIMSEval/branch/main/graph/badge.svg?token=AWWOT5Y4VD
    :target: https://codecov.io/gh/RIMS-Code/RIMSEval
    :alt: Code Coverage
.. image:: https://img.shields.io/badge/License-MIT-blue.svg
    :target: https://github.com/RIMS-Code/RIMSEval/blob/main/LICENSE
    :alt: License: MIT
.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black
    :alt: Code style: black

------------
Introduction
------------

The goal of this project is to provide a python
interface to process resonance ionization mass spectrometry (RIMS) data.

A detailed user guide documenting the package can be found
`here <https://rimseval.readthedocs.io/en/latest/>`_.

--------------------
Package installation
--------------------

.. code-block:: shell-session

    pip install rimseval

If pre-releases are available and you would like to install one,
add the ``--pre`` flag to above command.
More information in the
`documentation <https://rimseval.readthedocs.io/en/latest/>`_.


.. note:: It is highly recommended that you use a virtual environment,
    since ``numpy`` is pinned to a specific version
    in order to appropriately work with ``numba``.

-----------
RIMSEvalGUI
-----------

A GUI that wraps around the ``rimseval`` package
is available on
`GitHub <https://github.com/RIMS-Code/RIMSEvalGUI>`_.
The above mentioned documentation also serves
as the documentation for this GUI.

------------
Contributing
------------

Contributions are very welcome!
Especially the documentation could need some more examples
and polishing.
Please feel free to contact me if you'd like to contribute.

The `documentation <https://rimseval.readthedocs.io/en/latest/>`_
also contains a developers guide,
if you are interested in contributing to the code base itself.
