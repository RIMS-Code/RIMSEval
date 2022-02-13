=================
Development Guide
=================

This developers guide briefly goes through setting up the project.
It is not intended as a full guide for development of this project.
Most of the guidelines are copied from the developer's guide
of the ``iniabu`` project, which can be found
`here <https://iniabu.readthedocs.io/en/latest/dev/index.html>`_.

-------
Testing
-------

Full testing, linting, etc. is built-in using ``nox``.
To make it work, ensure that ``nox`` is installed by running:

.. code-block:: shell-session

    pip install nox

Then you can invoke nox by simply calling it
within the project folder via:

.. code-block:: shell-session

    nox

You can also set up your IDE to run any of the tests.
Required dependencies if you prefer not testing with ``nox``
can be found in the ``requirements-dev.txt`` file.

----------
Pre-commit
----------

Pre-commit will format code according to specs prior to committing it to GitHub.
To install the pre-commit hooks, go to the code folder and run the following command
(after installing pre-commit using pip or pipx):

$ pre-commit install

This will install the hooks that are defined in `.pre-commit-config.yaml`.

-------------
Test Coverage
-------------

Coveralls and pytest-cov is used to automatically determine the test coverage.

.. note:: If you are using PyCharm, you should set up your testing environment
    such that it contains in the `Additional Arguments` section the flag
    ``--no-cov``.
    Otherwise, coverage reporting in PyCharm will not work.

.. warning:: Code that contains the ``@njit`` or any numba JIT decorator
    is currently excluded from coverage using the ``# pragma: nocover``.
    Make sure you include useful tests for these routines nevertheless!
    However, due to existing issues, these jited methods would not show up as covered.

-------------
Documentation
-------------

This documentation is written in reText
and automatically generated using ``sphinx``.
If you would like to run it locally,
install the ``requirements-dev.txt`` packages.
From within the ``docs`` folder,
you can then generate the documentation via:

.. code-block:: shell-session

    sphinx-build -b html docs docs/_build/html/

This creates the the `html` documentation
in the :code:`docs/_build` folder.
