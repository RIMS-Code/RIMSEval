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



.. currentmodule:: rimseval.guis.integrals

----------------------
Integrals & Background
----------------------

Classes to define integrals and backgrounds.
These are both very similar in nature, therefore,
one superclass is created and individual
routines subclass this one further.


**************************
:class:`DefineAnyTemplate`
**************************

.. autoclass:: DefineAnyTemplate
    :members:
    :undoc-members:

**************************
:class:`DefineBackgrounds`
**************************

.. autoclass:: DefineBackgrounds
    :members:
    :undoc-members:

************************
:class:`DefineIntegrals`
************************

.. autoclass:: DefineIntegrals
    :members:
    :undoc-members:

******************************
:func:`define_backgrounds_app`
******************************

.. autofunction:: define_backgrounds_app

****************************
:func:`define_integrals_app`
****************************

.. autofunction:: define_integrals_app

*********************
:func:`tableau_color`
*********************

.. autofunction:: tableau_color



.. currentmodule:: rimseval.guis.mpl_canvas

-------------------------
Matplotlib Canvas Classes
-------------------------

These classes create spectra plotters and handling
for theses specific tasks.
Uses the matplotlib ``Qt5Agg`` backend.

*********************
:class:`PlotSpectrum`
*********************

Plots the spectrum and serves it as a matplotlib figure.
It adds toolbar and canvas (see below)
plus makes two layouts available,
a bottom layout and a right layout.
This allows the addition to QWidgets into this layouts later on.

The plot widget adds one button in the bottom layout
to toggle logarithmic axes for the vertical / signal axis.

.. autoclass:: PlotSpectrum
    :members:
    :undoc-members:

****************************
:class:`MplCanvasRightClick`
****************************

Handle right-click on ``matplotlib`` canvas.
Releases to signals: one on right mouse button press
and one on right mouse button release.
These signals send the x and y position where
the mouse event took place.

.. autoclass:: MplCanvasRightClick
    :members:
    :undoc-members:

*******************************
:class:`MyMplNavigationToolbar`
*******************************

Re-implementation of the matplotlib navigation toolbar.
After zooming in,
the zoom function is automatically deactivated.

.. autoclass:: MyMplNavigationToolbar
    :members:
    :undoc-members: