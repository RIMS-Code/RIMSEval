"""Run Pierce's criterion to reject data.

Implementation after Ross (2003) using calculation method for table from Wikipedia.
Note that the table that Ross (2003) presents is for `R`, which is the square root
of what `x**2` means in Gould (1855). Also, the first value of Ross (2003) for
three observations, one doubtful value seems to off by a bit. The rest of the
table agrees well.
"""

from typing import Tuple

import numpy as np
from scipy import special


def peirce_criterion(n_tot: int, n: int, m: int = 1) -> float:
    """Peirce's criterion

    Returns the threshold error deviation for outlier identification
    using Peirce's criterion based on Gould's methodology.
    This routine is heavily copied from Wikipedia

    :param n_tot: Total number of observations.
    :param n: Number of outliers to be removed.
    :param m: Number of model unknowns, defaults to 1.

    :return: Error threshold `R` (Ross, 2003) / Square root of `x**2` (Gould, 1955)
    """
    # Check number of observations:
    if n_tot > 1:
        # Calculate Q (Nth root of Gould's equation B):
        q_cap = (n ** (n / n_tot) * (n_tot - n) ** ((n_tot - n) / n_tot)) / n_tot

        # Initialize R values (as floats)
        r_new = 1.0
        r_old = 0.0
        #
        # Start iteration to converge on R:
        while abs(r_new - r_old) > (n_tot * 2.0e-16):
            # Calculate Lamda
            # (1/(N-n)th root of Gould's equation A'):
            ldiv = r_new ** n
            if ldiv == 0:
                ldiv = 1.0e-6
            lambda_g = ((q_cap ** n_tot) / (ldiv)) ** (1.0 / (n_tot - n))
            # Calculate x-squared (Gould's equation C):
            x2 = 1.0 + (n_tot - m - n) / n * (1.0 - lambda_g ** 2.0)
            # If x2 goes negative, return 0:
            if x2 < 0:
                x2 = 0.0
                r_old = r_new
            else:
                # Use x-squared to update R (Gould's equation D):
                r_old = r_new
                r_new = np.exp((x2 - 1) / 2.0) * special.erfc(
                    np.sqrt(x2) / np.sqrt(2.0)
                )
    else:
        x2 = 0.0
    return np.sqrt(x2)


def reject_outliers(
    data: np.ndarray, m: int = 1
) -> Tuple[float, float, np.ndarray, np.ndarray]:
    """Applies Peirce's criterion to reject outliers.

    Algorithm implmeneted as given by Ross (2003).

    :param data: All data points.
    :param m: Number of model unknowns, defaults to 1.

    :return: New average and standard deviation, Array with the outliers.
    """
    data = np.array(data)  # just making sure it's a numpy array
    data_in = data.copy()

    # first drop all nan and inf
    drop_index = np.where(np.isnan(data) | np.isinf(data))
    data = np.delete(data, drop_index)

    avg = np.average(data)
    std = np.std(data)
    n_tot = len(data)

    outliers = []
    diffs = np.abs(data - avg)

    for it in range(len(data)):  # check for every data point if it should be rejected
        max_diff = diffs.max()
        max_ind = diffs.argmax()

        rejection_limit = peirce_criterion(n_tot, it + 1, m)
        if max_diff > rejection_limit * std:
            outliers.append(data[max_ind])
            # delete max from diffs and data
            data = np.delete(data, max_ind)
            diffs = np.delete(diffs, max_ind)
        else:
            break  # we are done rejecting

    avg_new = float(np.average(data))
    std_new = float(np.std(data))

    # determine indexes of outliers in original array
    outliers = np.array(outliers)
    outliers_ind = np.zeros_like(outliers)
    for it, outl in enumerate(outliers):
        outliers_ind[it] = np.where(data_in == outl)[0][0]  # only first occurence
    outliers_ind = np.sort(outliers_ind)

    return avg_new, std_new, outliers, outliers_ind
