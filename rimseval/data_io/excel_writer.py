"""Write Excel Files from the files that we have, e.g., a workup file."""

from datetime import datetime
from pathlib import Path

from iniabu.utilities import item_formatter
import xlsxwriter

from .. import CRDFileProcessor
from ..utilities import ini


def workup_file_writer(crd: CRDFileProcessor, fname: Path) -> None:
    """Write out an Excel workup file.

    This is for the user to write out an excel workup file, which will already be
    filled with the integrals of the given CRD file.

    :param crd: CRD file processor file to write out.
    :param fname: File name for the file to write out to.
    """
    if crd.def_integrals is None:
        return
    else:
        int_names, _ = crd.def_integrals

    # format names
    for it, name in enumerate(int_names):
        int_names[it] = item_formatter(name)

    fname = fname.with_suffix(".xlsx").absolute()  # ensure correct format

    wb = xlsxwriter.Workbook(str(fname))
    ws = wb.add_worksheet()

    # formats
    fmt_title = wb.add_format({"bold": True, "font_size": 14})
    fmt_bold = wb.add_format({"bold": True})
    fmt_italic = wb.add_format({"italic": True})
    fmt_bold_italic = wb.add_format({"bold": True, "italic": True})
    fmt_std_abus = wb.add_format({"bold": True, "color": "red"})

    # write the title
    ws.write(0, 0, f"Workup {datetime.today().date()}", fmt_title)

    # write data header
    hdr_row = 3  # row to start header of the data in
    general_headers = ["Remarks", "File Name", "# Shots"]

    int_col = len(general_headers)  # start of integral column
    delta_col = int_col + 2 * len(int_names)  # start of delta column

    for col, hdr in enumerate(general_headers):
        ws.write(hdr_row, col, general_headers[col], fmt_bold_italic)
    for col, name in enumerate(int_names):
        ws.write(hdr_row, 2 * col + int_col, name, fmt_bold_italic)
        ws.write(hdr_row, 2 * col + 1 + int_col, f"σ{name})", fmt_bold_italic)

    # close the workbook
    wb.close()


def iso_format_excel(iso: str) -> str:
    """Format isotope name from `iniabu` to format as written to Excel.

    :param iso: Isotope, formatted according to `iniabu`, e.g., "Si-28"
    :return: Excel write-out format.
    """
    iso_split = iso.split("-")
    return f"{iso_split[1]}{iso_split[0]}"
