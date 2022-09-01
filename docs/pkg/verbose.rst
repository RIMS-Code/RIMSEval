=========
Verbosity
=========

The package has the possibility to go into verbose mode.
To do so, change the ``rimseval.DEBUG``.
This variable is by default set to ``0``,
which means no excessive warnings.

Setting the debug level to ``1`` will show the following warnings in addition:

- Automatic mass calibration optimization did not find enough peaks and was skipped.

Setting the debug level to ``2`` will show the following warnings in addition:

- Division by zero warnings in :math:`\delta`-value calculation
- ``scipy`` optimize routine (peak fitting in mass calibration) reached maximum iterations.
