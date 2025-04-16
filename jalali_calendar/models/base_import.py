# -*- coding: utf-8 -*-
import datetime

import jdatetime

from odoo import _, fields, models
from odoo.http import request
from odoo.tools import (DEFAULT_SERVER_DATE_FORMAT,
                        DEFAULT_SERVER_DATETIME_FORMAT)


class Import(models.TransientModel):
    _inherit = 'base_import.import'
    _description = 'Base Import'

    def _parse_date_from_data(self, data, index, name, field_type, options):
        dt = datetime.datetime
        fmt = fields.Date.to_string if field_type == 'date' else fields.Datetime.to_string
        d_fmt = options.get('date_format')
        dt_fmt = options.get('datetime_format')
        for num, line in enumerate(data):
            if not line[index]:
                continue
            v = line[index].strip()
            if request.env.user.lang == 'fa_IR':
                try:
                    if dt_fmt and field_type == 'datetime':
                        try:
                            PERSIAN_DEFAULT_SERVER_DATETIME_FORMAT = DEFAULT_SERVER_DATETIME_FORMAT.replace('-','/')
                            line[index] = jdatetime.datetime.strptime(v, PERSIAN_DEFAULT_SERVER_DATETIME_FORMAT).togregorian().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                            continue
                        except ValueError:
                            pass
                    PERSIAN_DEFAULT_SERVER_DATE_FORMAT = DEFAULT_SERVER_DATE_FORMAT.replace('-','/')
                    line[index] = jdatetime.datetime.strptime(v, PERSIAN_DEFAULT_SERVER_DATE_FORMAT).togregorian().date().strftime(DEFAULT_SERVER_DATE_FORMAT)
                except ValueError as e:
                    raise ValueError(_("Column %s contains incorrect values. Error in line %d: %s") % (name, num + 1, e))
                except Exception as e:
                    raise ValueError(_("Error Parsing Date [%s:L%d]: %s") % (name, num + 1, e))
            else:
                try:
                    if dt_fmt and field_type == 'datetime':
                        try:
                            line[index] = fmt(dt.strptime(v, dt_fmt))
                            continue
                        except ValueError:
                            pass
                    line[index] = fmt(dt.strptime(v, d_fmt))
                except ValueError as e:
                    raise ValueError(
                        _("Column %s contains incorrect values. Error in line %d: %s") % (name, num + 1, e))
                except Exception as e:
                    raise ValueError(_("Error Parsing Date [%s:L%d]: %s") % (name, num + 1, e))