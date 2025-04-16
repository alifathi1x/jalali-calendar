from odoo import models, fields, api, exceptions, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import jdatetime

from ..globals import jdate_utils

MONTH_SELECTION = [
    ('1', _('January_1')),
    ('2', _('February_2')),
    ('3', _('March_3')),
    ('4', _('April_4')),
    ('5', _('May_5')),
    ('6', _('June_6')),
    ('7', _('July_7')),
    ('8', _('August_8')),
    ('9', _('September_9')),
    ('10', _('October_10')),
    ('11', _('November_11')),
    ('12', _('December_12')),
]

class JalaliResCompany(models.Model):
    _inherit = "res.company"

    def _get_tax_closing_period_boundaries(self, date):
        self.ensure_one()
        period_months = self._get_tax_periodicity_months_delay()
        ########## overrided ##########
        """
        period_number = (date.month//period_months) + (1 if date.month % period_months != 0 else 0)
        end_date = date_utils.end_of(datetime.date(date.year, period_number * period_months, 1), 'month')
        start_date = end_date + relativedelta(day=1, months=-period_months + 1)
        return start_date, end_date
        """
        jdate = jdatetime.datetime.fromgregorian(date=date).date()
        jboy = jdatetime.date(jdate.year, 1, 1)

        jstart = jboy
        jperiods = []
        for _ in range(12//period_months):
            jend = jstart.replace(month=jstart.month + period_months) if jstart.month + \
                period_months <= 12 else jboy.replace(year=jboy.year + 1)
            jend -= jdatetime.timedelta(days=1)
            jperiods.append((jstart, jend))

            jstart = jend + jdatetime.timedelta(days=1)

        jdate = jdatetime.datetime.fromgregorian(date=date)
        for jperiod in jperiods:
            start_date, end_date = jdatetime.date.togregorian(jperiod[0]), jdatetime.date.togregorian(jperiod[1])
            if start_date <= date <= end_date:
                return start_date, end_date
        ########## ######### ##########

    def _get_tax_closing_move_description(self, periodicity, period_start, period_end, fiscal_position):
        ########## overrided ##########
        """
        if periodicity == 'year':
            return _("Tax return for %s", period_start.year)
        elif periodicity == 'trimester':
            return _("Tax return for %s", format_date(self.env, period_start, date_format='qqq'))
        elif periodicity == 'monthly':
            return _("Tax return for %s", format_date(self.env, period_start, date_format='LLLL'))
        else:
            return _("Tax return from %s to %s") % (format_date(self.env, period_start), format_date(self.env, period_end))
        """
        jperiod_start = jdatetime.datetime.fromgregorian(date=period_start).date()
        jperiod_end = jdatetime.datetime.fromgregorian(date=period_end).date()
        locale = self._context.get('lang') or 'en_US'

        if periodicity == 'year':
            return _("Tax return for %s", jperiod_start.year)
        elif periodicity == 'trimester':
            return _("Tax return for %s", jdate_utils.get_quarter_name(jperiod_start, locale))
        elif periodicity == 'monthly':
            return _("Tax return for %s", jdate_utils.get_month_name(jperiod_start, locale))
        else:
            return _("Tax return from %s to %s") % (jperiod_start.strftime(DEFAULT_SERVER_DATE_FORMAT), jperiod_end.strftime(DEFAULT_SERVER_DATE_FORMAT))
        ########## ######### ##########
