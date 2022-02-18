============
Installation
============

----------
Executable
----------

To install an executable file of the software on your computer,
download the latest release version for your operating system from
`the GitHub repository <https://github.com/RIMS-Code/RIMSEvalGUI/releases>`_.
You do not need to have an existing python environment,
since all dependencies will be installed along.

--------------------
Anaconda / Miniconda
--------------------

If you want to install the RIMSEval GUI on Anaconda,
you should first set up a virtual environment.
To setup the environment and activate it, type:

.. code-block:: shell-session

    conda create -n rimseval python=3.9
    conda activate rimseval

Then you can install all requirements by typing:

.. code-block:: shell-session

    pip install -r requirements.txt

The RIMSEval GUI can then be started by typing:

.. code-block:: shell-session

    python RIMSEvalGUI.py

------
Python
------

To setup teh RIMSEval GUI on regular python,
make sure that you have Python 3.9 installed installed.
Then create a virtual environment.
Instructions can, e.g., found
`here <https://devrav.com/blog/create-virtual-env-python>`_.

After activating your new virtual environment,
install the requirements by typing:

.. code-block:: shell-session

    pip install -r requirements

The RIMSEval GUI can then be started by typing:

.. code-block:: shell-session

    python RIMSEvalGUI.py
