# -*- coding: utf-8 -*-
"""
This module contains custom export controllers for the Jalali Calendar.
It overrides the default CSV and Excel export functionality to handle Jalali eightdates.
"""

import datetime
import io
from typing import List, Any

import jdatetime
from odoo.addons.web.controllers.export import CSVExport, ExcelExport
from odoo.http import request
from odoo.tools import (
    DEFAULT_SERVER_DATE_FORMAT,
    DEFAULT_SERVER_DATETIME_FORMAT,
    pycompat,
)


class CSVExportInherit(CSVExport):
    def from_data(self, fields: List[str], rows: List[List[Any]]) -> bytes:
        if request.env.user.lang == 'fa_IR':
            return self._export_jalali_csv(fields, rows)
        return super().from_data(fields, rows)

    def _export_jalali_csv(self, fields: List[str], rows: List[List[Any]]) -> bytes:
        fp = io.BytesIO()
        writer = pycompat.csv_writer(fp, quoting=1)
        writer.writerow(fields)

        for data in rows:
            row = [self._format_cell(d) for d in data]
            writer.writerow(row)

        return fp.getvalue()

    @staticmethod
    def _format_cell(value: Any) -> str:
        if isinstance(value, str) and value.startswith(('=', '-', '+')):
            return f"'{value}"
        if isinstance(value, datetime.datetime):
            return jdatetime.datetime.fromgregorian(datetime=value).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        if isinstance(value, datetime.date):
            return jdatetime.datetime.fromgregorian(date=value).strftime(DEFAULT_SERVER_DATE_FORMAT)
        return pycompat.to_text(value)


class ExcelExportInherit(ExcelExport):
    def from_group_data(self, fields: List[str], groups: Any) -> Any:
        if request.env.user.lang == 'fa_IR':
            self._convert_dates_to_jalali(groups)
        return super().from_group_data(fields, groups)

    def from_data(self, fields: List[str], rows: List[List[Any]]) -> Any:
        if request.env.user.lang == 'fa_IR':
            rows = [self._convert_row_to_jalali(row) for row in rows]
        return super().from_data(fields, rows)

    @staticmethod
    def _convert_dates_to_jalali(groups: Any) -> None:
        for group in groups.children.values():
            for data in group.data:
                for i, value in enumerate(data):
                    data[i] = ExcelExportInherit._convert_to_jalali(value)

    @staticmethod
    def _convert_row_to_jalali(row: List[Any]) -> List[Any]:
        return [ExcelExportInherit._convert_to_jalali(value) for value in row]

    @staticmethod
    def _convert_to_jalali(value: Any) -> Any:
        if isinstance(value, datetime.datetime):
            return jdatetime.datetime.fromgregorian(datetime=value).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        if isinstance(value, datetime.date):
            return jdatetime.datetime.fromgregorian(date=value).strftime(DEFAULT_SERVER_DATE_FORMAT)
        return value