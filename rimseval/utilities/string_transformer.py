"""Transform strings from one format into another.

Hopefully the routines in here will be temporary and can be trashed soon.
"""


def iso_to_iniabu(iso: str) -> str:
    """Transform an isotope name to current iniabu default.

    :param iso: Isotope name as a string, e.g., 46Ti or Ti46.
    """
    zz_first = True  # e.g., 46Ti
    try:
        int(iso[0])
    except ValueError:
        iso = iso[::-1]
        zz_first = False

    ind = 0
    zz = None
    while ind < len(iso):
        try:
            int(iso[ind])
        except ValueError:
            zz = iso[:ind]
            break
        ind += 1

    ret_str = (
        f"{iso[ind:].capitalize()}-{zz}"
        if zz_first
        else f"{iso[ind:][::-1].capitalize()}-{zz[::-1]}"
    )

    return ret_str
