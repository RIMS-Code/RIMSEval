============
Delta Values
============

For all integrals, :math:`\delta`-values can be calculated automatically
as described in the :doc:`usage documentation <../pkg/usage>`.
Delta values are always calculated (1) with respect to the major isotope
and (2) using the NIST database of the
`iniabu <https://github.com/galactic-forensics/iniabu>`_ package.
If no value can be calculated, i.e.,
because the isotope is unknown to ``iniabu`` or because
the natural abundance of the specified isotope is unknown,
``np.nan`` will be returned as the :math:`\delta`-value.

.. note:: All :math:`\delta`-values are reported in per mil (‰).

--------------------------------
Calculation :math:`\delta`-value
--------------------------------

Be :math:`i` and :math:`j` the number of counts
in the nominator and denominator isotopes, respectively, and
:math:`r` the NIST isotopic ratio of the same isotopes.
The :math:`\delta`-value can then be calculated as:

.. math::

    \delta = \left( \frac{i/j}{r} - 1 \right) \times 1000 \qquad (‰)

-------------
Uncertainties
-------------

Be :math:`\sigma_i` and :math:`\sigma_j` the uncertainties of values
:math:`i` and :math:`j`, respectively.
The uncertainty of the :math:`\delta`-value :math:`\sigma_{\delta}`
can be calculated as:

.. math::

    \sigma_{\delta} = \frac{1000}{r} \left[
        \left(\frac{\sigma_i}{j}\right)^2 +
        \left(\frac{i\sigma_j}{j^2}\right)^2 \right]^{1/2}
        \qquad (‰)
