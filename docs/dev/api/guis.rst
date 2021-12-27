####
GUIs
####

These GUIs are part of the API package
in order to bring some functionality to the user
when working on the command line.
Here,
we solely use ``matloplib`` and Qt frontends.
This is **not** the description of the main GUI,
which can be found in :doc:`../../gui/gui`.



.. currentmodule:: rimseval.guis.mcal

---------------------
Mass Calibration GUIs
---------------------

Define the mass calibration by clicking on a plot.
Uses ``Qt5Agg`` for ``matplotlib``.

****************************
:class:`MplCanvasRightClick`
****************************

Handle right-click on ``matplotlib`` canvas.

.. autoclass:: MplCanvasRightClick
    :members:
    :undoc-members:

******************************
:class:`CreateMassCalibration`
******************************

.. autoclass:: CreateMassCalibration
    :members:
    :undoc-members:

***************************
:func:`create_mass_cal_app`
***************************

.. autofunction:: create_mass_cal_app

************************
:func:`find_closest_iso`
************************

.. autofunction:: find_closest_iso