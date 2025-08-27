"""Write Excel Files from the files that we have, e.g., a workup file."""

from datetime import datetime
from pathlib import Path

from iniabu.utilities import item_formatter
import xlsxwriter
from xlsxwriter.utility import xl_rowcol_to_cell

from .. import CRDFileProcessor
from ..utilities import ini


def workup_file_writer(
    crd: CRDFileProcessor, fname: Path, timestamp: bool = False
) -> None:
    """Write out an Excel workup file.

    This is for the user to write out an excel workup file, which will already be
    filled with the integrals of the given CRD file.

    :param crd: CRD file processor file to write out.
    :param fname: File name for the file to write out to.
    :param timestamp: Create a column for the time stamp? Defaults to ``False``
    """
    if crd.def_integrals is None:
        return
    else:
        int_names, _ = crd.def_integrals

    # format names
    for it, name in enumerate(int_names):
        formatted_name = item_formatter(name)
        if "-" in formatted_name:  # only format if it's an isotope!
            int_names[it] = item_formatter(name)

    # get normalizing isotope
    norm_names = []
    for name in int_names:
        try:
            ele = name.split("-")[0]
            norm_names.append(ini._get_norm_iso(ele))
        except IndexError:  # norm isotope does not exist
            norm_names.append(None)

    fname = fname.with_suffix(".xlsx").absolute()  # ensure correct format

    wb = xlsxwriter.Workbook(str(fname))
    ws = wb.add_worksheet()

    # formats
    fmt_title = wb.add_format({"bold": True, "font_size": 14})
    fmt_hdr_0 = wb.add_format({"bold": True, "italic": True, "left": True})
    fmt_hdr = wb.add_format({"bold": True, "italic": True})
    fmt_std_abus = wb.add_format({"bold": True, "color": "red"})
    fmt_counts_0 = wb.add_format({"num_format": "0", "left": True})
    fmt_counts = wb.add_format({"num_format": "0"})
    fmt_counts_unc = wb.add_format(
        {"num_format": "0", "color": "gray", "valign": "left"}
    )
    fmt_delta_0 = wb.add_format({"num_format": "0", "left": True})
    fmt_delta = wb.add_format({"num_format": "0"})
    fmt_delta_unc = wb.add_format(
        {"num_format": "0", "color": "gray", "valign": "left"}
    )
    fmt_timestamp = wb.add_format({"num_format": "YYYY-MM-DD HH:MM:SS"})

    # cell widths for data
    wdth_counts = 8
    wdth_delta = 12
    wdth_delta_unc = 6

    # rows to define
    abu_row = 4
    num_eqn_rows = 999

    # special headers and user definitions
    general_headers = ["Remarks", "File Name", "# Shots"]
    general_headers_widths = [20, 20, 10]
    fname_col = 1
    shots_col = 2

    if timestamp:
        general_headers.append("Timestamp")
        general_headers_widths.append(18)

    # write the title
    ws.write(0, 0, f"Workup {datetime.today().date()}", fmt_title)

    # write data header and abundances
    hdr_row = abu_row + 1  # row to start header of the data in

    int_col = len(general_headers)  # start of integral column
    delta_col = int_col + 2 * len(int_names)  # start of delta column

    for col, hdr in enumerate(general_headers):
        ws.write(hdr_row, col, hdr, fmt_hdr)
        ws.set_column(col, col, general_headers_widths[col])

    for col, name in enumerate(int_names):
        # write abundances
        try:
            abu_col = ini.iso[name].abu_rel
            ws.write(abu_row, 2 * col + int_col, abu_col, fmt_std_abus)
        except IndexError:
            pass
        # write integral header
        name = iso_format_excel(name)

        fmt_hdr_use = fmt_hdr_0 if col == 0 else fmt_hdr

        ws.write(hdr_row, 2 * col + int_col, name, fmt_hdr_use)
        ws.write(hdr_row, 2 * col + 1 + int_col, "±1σ", fmt_hdr)

    # integral column width
    ws.set_column(int_col, int_col + 2 * len(int_names) - 1, wdth_counts)

    col = delta_col
    for it, name in enumerate(int_names):
        norm_iso_name = norm_names[it]
        fmt_hdr_use = fmt_hdr_0 if col == delta_col else fmt_hdr
        if (
            norm_iso_name is not None and norm_iso_name in int_names
        ):  # norm isotope valid
            ws.write(
                hdr_row,
                col,
                f"δ({iso_format_excel(name)}/{iso_format_excel(norm_iso_name)})",
                fmt_hdr_use,
            )
            ws.write(hdr_row, col + 1, "±1σ", fmt_hdr)

            # set width
            ws.set_column(col, col, wdth_delta)
            ws.set_column(col + 1, col + 1, wdth_delta_unc)

            col += 2

    # WRITE DATA
    data_row = hdr_row + 1

    # file name
    ws.write(data_row, fname_col, crd.fname.name)

    # write the number of shots
    ws.write(data_row, shots_col, crd.nof_shots, fmt_counts)

    for row in range(data_row + 1, num_eqn_rows + data_row):
        ws.write_blank(row, shots_col, None, fmt_counts)

    # write the timestamp if requested
    if timestamp:
        ws.write(data_row, shots_col + 1, crd.timestamp, fmt_timestamp)

    for row in range(data_row + 1, num_eqn_rows + data_row):
        ws.write_blank(row, shots_col + 1, None, fmt_timestamp)

    # write integrals
    for col, dat in enumerate(crd.integrals):
        fmt_counts_use = fmt_counts_0 if col == 0 else fmt_counts
        ws.write(data_row, 2 * col + int_col, dat[0], fmt_counts_use)
        ws.write(data_row, 2 * col + int_col + 1, dat[1], fmt_counts_unc)

    for row in range(data_row + 1, num_eqn_rows + data_row):  # boarder for integrals
        for col, _ in enumerate(crd.integrals):
            fmt_counts_use = fmt_counts_0 if col == 0 else fmt_counts
            ws.write_blank(row, 2 * col + int_col, None, fmt_counts_use)
            ws.write_blank(row, 2 * col + int_col + 1, None, fmt_counts_unc)

    # write delta equations
    col = delta_col
    for it, _ in enumerate(int_names):
        norm_iso_name = norm_names[it]
        if (
            norm_iso_name is not None and norm_iso_name in int_names
        ):  # norm isotope valid
            for eq_row in range(num_eqn_rows):
                # get cell values, nominators and denominators
                nom_iso = xl_rowcol_to_cell(data_row + eq_row, 2 * it + int_col)
                nom_iso_unc = xl_rowcol_to_cell(data_row + eq_row, 2 * it + int_col + 1)
                den_iso = xl_rowcol_to_cell(
                    data_row + eq_row,
                    2 * int_names.index(norm_iso_name) + int_col,
                    col_abs=True,
                )
                den_iso_unc = xl_rowcol_to_cell(
                    data_row + eq_row,
                    2 * int_names.index(norm_iso_name) + int_col + 1,
                    col_abs=True,
                )
                # get standard abundances cell names
                nom_std = xl_rowcol_to_cell(abu_row, 2 * it + int_col, row_abs=True)
                den_std = xl_rowcol_to_cell(
                    abu_row,
                    2 * int_names.index(norm_iso_name) + int_col,
                    row_abs=True,
                    col_abs=True,
                )

                # decide if we write a boarder or not
                fmt_delta_use = fmt_delta_0 if col == delta_col else fmt_delta

                # write the values for the delta formula
                ws.write(
                    data_row + eq_row,
                    col,
                    f'=IF({nom_iso}<>"",'
                    f'(({nom_iso}/{den_iso})/({nom_std}/{den_std})-1)*1000, "")',
                    fmt_delta_use,
                )
                # equation for uncertainty
                ws.write(
                    data_row + eq_row,
                    col + 1,
                    f'=IF({nom_iso}<>"",'
                    f"1000*SQRT("
                    f"(({nom_iso_unc}/{den_iso})/({nom_std}/{den_std}))^2+"
                    f"(({nom_iso}*{den_iso_unc}/{den_iso}^2)/({nom_std}/{den_std}))^2"
                    f'), "")',
                    fmt_delta_unc,
                )

            # increment column
            col += 2

    # close the workbook
    wb.close()


def iso_format_excel(iso: str) -> str:
    """Format isotope name from `iniabu` to format as written to Excel.

    :param iso: Isotope, formatted according to `iniabu`, e.g., "Si-28"
    :return: Excel write-out format.
    """
    iso_split = iso.split("-")
    if len(iso_split) != 2:
        return iso
    else:
        return f"{iso_split[1]}{iso_split[0]}"
