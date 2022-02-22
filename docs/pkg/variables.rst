=========
Variables
=========

Here we describe the most important variables that are available for the user.
These variables can be retrieved by calling them,
however, are also of intereste for macro developers.

Throughout this chapter, we will use ``crd`` as an instance of the
``CRDFileProcessor``, see also
:meth:`rimseval.processor.CRDFileProcessor`.

-------
General
-------

- ``crd.crd``: The CRDReader instance of the opened file.
- ``crd.fname``: File name of the opened CRD file.

-------------
Spectrum Data
-------------

- ``crd.data``: The mass spectrum data for an opened file.
    This data must be a ``numpy.ndarray`` with the same length as
    ``crd.tof`` and ``crd.mass``.
- ``crd.mass``: The mass axis of a given spectrum as a ``numpy.ndarray``.
    This array is only available after mass calibration and must be
    of the same length as ``crd.data`` and ``crd.tof``.
- ``crd.nof_shots``: An integer that contains the number of used shots in the spectrum.
    This variable is updated when shots are rejected.
- ``crd.tof``: Time of flight data of the spectrum.
    This data is only available
    after opening after ``crd.full_spectrum()`` was run.
    It is a ``numpy.ndarray`` and must be of the same length as ``crd.data``
    and ``crd.mass``.

------------
Package Data
------------

- ``crd.data_pkg``: A data array for each individual package.
    For a data length :math:`n` and :math:`p` packages,
    this ``numpy.ndarray`` is of size :math:`n \times p`.
- ``crd.nof_shots_pkg``: The number of shots in the package.
    The data are given as a ``numpy.ndarray`` of integers.
    It describes the number of shots in each individual package.

---------
Integrals
---------

- ``crd.integrals``: Sum of counts for each defined integral.
    For each defined integral, this array will contain
    the sum of counts in the defined area and its uncertainty.
    :math:`m` defined peaks, it will therefore be of size :math:`m \times 2`.
    The second entry of each integral is the uncertainty of the counts.
- ``crd.integrals_pkg``: Integral data for packages.
    For a total of :math:`p` packages and :math:`m` defined integrals,
    this ``numpy.ndarray`` will be of size :math:`p \times m \times 2`.
    As for the integrals, the sum of counts for each peak and its uncertainty
    are given.

----------------
Single Shot Data
----------------

In order to avoid storing the whole spectrum for every shot,
the data is ordered in two arrays with one helper array.

- ``crd.all_tofs``: Recorded time of arrival bins in the TDC.
    This ``numpy.ndarray`` contains all recorded time of flights
    in order of arrival. It is therefore of the same length as
    the total number of recorded ions.
    The time of flights are not stored in microseconds,
    but the TDC bin of arrival is stored as an integer.
- ``crd.ions_per_shot``: Number of ions recorded per shot.
    This ``numpy.ndarray`` is of length ``self.nof_shots``
    and records for the number of ions that arrived in each shot as an integer.
    The sum of this array is the total number of ions that are in the spectrum.
- ``crd.ions_to_tof_map``: Mapper array to find arrival bins for each shot.
    This 2D ``numpy.ndarray`` contains one entry per shot and
    is therefore of the same length as ``crd.ions_per_shot``.
    Each entry describes in which range of ``crd.all_tofs`` the arrival bins are stored.
    For example, if you want to retrieve the arrival bins of the ions of the 10th shot
    of your data set, you could acquire them by calling:

    .. code-block:: python

        tof_range = crd.ions_per_shot[9]  # the first shot is index 0
        arrival_bins = crd.all_tofs[tof_range[0]:tof_range[1]]
