# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


import jdatetime

from odoo.addons.hr_payroll.models import hr_payslip
from odoo.tools.misc import (DATE_LENGTH, babel, babel_locale_parse, datetime,
                             format_date, get_lang, odoo, posix_to_ldml)

from ..globals import jdate_utils


def jalali_format_date(env, value, lang_code=False, date_format=False):
    if env.user.lang == 'fa_IR':
        if not value:
            return ''
        if isinstance(value, str):
            if len(value) < DATE_LENGTH:
                return ''
            if len(value) > DATE_LENGTH:
                # a datetime, convert to correct timezone
                value = odoo.fields.Datetime.from_string(value)
                value = odoo.fields.Datetime.context_timestamp(env['res.lang'], value)
            else:
                value = odoo.fields.Datetime.from_string(value)
        elif isinstance(value, datetime.datetime) and not value.tzinfo:
            # a datetime, convert to correct timezone
            value = odoo.fields.Datetime.context_timestamp(env['res.lang'], value)

        lang = get_lang(env, lang_code)
        locale = babel_locale_parse(lang.code)
        if not date_format:
            date_format = posix_to_ldml(lang.date_format, locale=locale)
            
        range_start = value
        # possible_intervals: day, week, month, quarter, year
        j_range_start = jdatetime.datetime.fromgregorian(date=range_start)
        j_range_start, j_range_end = jdate_utils.get_month(j_range_start)
        
        if date_format == 'dd MMM yyyy':
            return str(j_range_start.year) + ' ' + \
                jdate_utils.get_month_name(j_range_start, locale) + ' ' + str(j_range_start.day)
        elif date_format == "'W'w YYYY":
            return ('W' if locale == 'en_US' else 'ه‌') + \
                str(j_range_start.weeknumber()) + ' ' + str(j_range_start.year)
        elif date_format in ('MMMM yyyy', 'MMMM y'):
            return jdate_utils.get_month_name(j_range_start, locale) + ' ' + str(j_range_start.year)
        elif date_format == 'QQQ yyyy':
            return jdate_utils.get_quarter_name(j_range_start, locale) + ' ' + str(j_range_start.year)
        elif date_format in ('yyyy','y'):
            return str(j_range_start.year)
        return babel.dates.format_date(value, format=date_format, locale=locale)
    format_date(env, value, lang_code, date_format)

hr_payslip.format_date = jalali_format_date