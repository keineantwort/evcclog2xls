import logging

from log import init_logger
import os
from datetime import datetime
from dataclasses import dataclass

import xlsxwriter

log = init_logger(log_level=logging.DEBUG)

format_table_cell = None
format_table_header = None


@dataclass
class ExcelTableHeader:
    position: int
    label: str
    width: int


def create_format(workbook):
    global format_table_header
    format_table_header = workbook.add_format({'bold': True, 'font_size': 13, 'bottom': 1})
    global format_table_cell
    format_table_cell = workbook.add_format({'font_size': 12})
    format_table_cell.set_text_wrap()
    format_table_cell.set_align('left')
    format_table_cell.set_align('top')

    workbook.set_size(2000, 1500)


def add_table_header(worksheet, header_list, row=0, col=0):
    all_header = list(h2.label for h2 in sorted(header_list, key=lambda h: h.position))

    worksheet.write_row(row, col, all_header, format_table_header)

    for header in header_list:
        worksheet.set_column(col + header.position, col + header.position, header.width)

    worksheet.freeze_panes(row + 1, col)


def add_worksheet(workbook, worksheet_name, header_list):
    worksheet = workbook.add_worksheet(worksheet_name)

    add_table_header(worksheet, header_list)

    worksheet.autofilter(0, 0, 0, len(header_list) - 1)
    worksheet.set_zoom(150)

    return worksheet
