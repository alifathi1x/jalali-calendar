# -*- coding: utf-8 -*-
import collections
from functools import partial

import babel.dates
import jdatetime
from babel.dates import format_date
from dateutil.relativedelta import relativedelta
from odoo import _, api, fields, models
from odoo.tools.misc import format_date

from ..globals import jdate_utils


class date_range(object):
    def __init__(self, start, stop):
        assert start <= stop
        self.start = start
        self.end = stop

    def iter(self, step):
        v = self.start
        step = STEP_BY[step]
        while v <= self.end:
            yield v
            v += step

STEP_BY = {
    'day': relativedelta(days=1),
    'week': relativedelta(weeks=1),
    'month': relativedelta(months=1),
    'year': relativedelta(years=1),
}

            
FORMAT = {
    'day': u"EEE\nMMM\u00A0dd",
    'week': u'w',
    'month': u'MMMM\u00A0yyyy',
}
SKELETONS = {
    'day': u"MMMEEEdd",
    'month': u'yyyyMMMM',
}

class Base(models.AbstractModel):
    _inherit = 'base'
    
    def _get_date_formatter(self, step, field, locale):
        """ Returns a callable taking a single positional date argument and
        formatting it for the step and locale provided.
        """

        # Week number calculation does not have a dedicated format in `FORMAT['week']`. So its method is a little more
        # complex. More over, `babel` lib does not return correct number. See below.
        if step == 'week':

            def _week_format(date):
                if field.type == 'date':
                    weeknumber = babel.dates.format_date(date, format=FORMAT[step], locale=locale)
                elif field.type == 'datetime':
                    # For some reason, babel returns the '2018-12-31' as "Week 53" instead of "Week 1"
                    # Check https://github.com/python-babel/babel/issues/619 and change this when Odoo will use a fixed Babel version
                    weeknumber = date.strftime('%V')  # ISO 8601 week as a decimal number with Monday as the first day of the week.
                return _("Week %(weeknumber)s\n%(week_start)s - %(week_end)s") % {
                    'weeknumber': weeknumber,
                    'week_start': format_date(self.env, date, locale, "MMM\u00A0dd"),
                    'week_end': format_date(self.env, date + self._grid_step_by(step) - relativedelta(days=1), locale, "MMM\u00A0dd")
                }
            return _week_format

        if hasattr(babel.dates, 'format_skeleton'):
            def _format(d, _fmt=babel.dates.format_skeleton, _sk=SKELETONS[step], _l=locale):
                if self.env.user.lang == 'fa_IR' and field.type == 'date' and step=="day":
                    jdate = jdatetime.date.fromgregorian(date=d)
                    result = jdate_utils.get_weekday_name(jdate, locale)+ ' ' + jdate_utils.get_month_name(jdate, locale)+' '+jdate_utils.e2p(str(jdate.day)) 
                else:
                    result = _fmt(datetime=d, skeleton=_sk, locale=_l)
                # approximate distribution over two lines, for better
                # precision should be done by rendering with an actual
                # proportional font, for even better precision should be done
                # using the fonts the browser asks for, here we just use
                # non-whitespace length which is really gross. Also may need
                # word-splitting in non-latin scripts.
                #
                # also ideally should not split the lines at all under a
                # certain width
                cl = lambda l: sum(len(s) for s in l)
                line1 = result.split(u' ')
                halfway = cl(line1) / 2.
                line2 = collections.deque(maxlen=int(halfway) + 1)
                while cl(line1) > halfway:
                    line2.appendleft(line1.pop())

                middle = line2.popleft()
                if cl(line1) < cl(line2):
                    line1.append(middle)
                else:
                    line2.appendleft(middle)
                return u"%s\n%s" % (
                    u'\u00A0'.join(line1),
                    u'\u00A0'.join(line2),
                )
            return _format
        else:
            return partial(babel.dates.format_date,
                           format=FORMAT[step],
                           locale=locale)
            
    def _grid_range_of(self, span, step, anchor, field):
        """
            For `datetime` field, this method will return a range object containing the list of column date
            bounds. Those datetime are timezoned in UTC. The closing date should not be included in column
            domain.

            :param span: name of the grid range (total period displayed)
            :param step: name of the time unit used as step for grid column
            :param anchor: the `date` or `datetime` in the period to display
            :param field: `odoo.field` used as grouping criteria
        """
        if self.env.user.lang == 'fa_IR' and field.type == 'date' and span=="month":
            jg = jdatetime.GregorianToJalali(anchor.year, anchor.month,anchor.day)
            jd = jdatetime.date(jg.jyear, jg.jmonth,1)
            start = jd.togregorian()
            end = start+jdatetime.timedelta(jdate_utils.get_month(jd)[1].day-1)
            return date_range(start, end)
        else:
            return super()._grid_range_of(span, step, anchor, field)
