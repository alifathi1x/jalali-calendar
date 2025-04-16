# -*- coding: utf-8 -*-
import collections
import datetime

import babel.dates
import dateutil
import jdatetime
import itertools
import pytz
from odoo.tools import (
    clean_context, config, CountingStream, date_utils, discardattr,
    DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, frozendict,
    get_lang, LastOrderedSet, lazy_classproperty, OrderedSet, ormcache,
    partition, populate, Query, ReversedIterable, split_every, unique, SQL,
)
import odoo
from odoo import _, api, models
from odoo.osv import expression
from odoo.tools import (DEFAULT_SERVER_DATE_FORMAT,
                        DEFAULT_SERVER_DATETIME_FORMAT, date_utils)
from odoo.tools.misc import get_lang

from ..globals import jdate_utils

# read_group stuff
READ_GROUP_TIME_GRANULARITY = {
    'hour': dateutil.relativedelta.relativedelta(hours=1),
    'day': dateutil.relativedelta.relativedelta(days=1),
    'week': datetime.timedelta(days=7),
    'month': dateutil.relativedelta.relativedelta(months=1),
    'quarter': dateutil.relativedelta.relativedelta(months=3),
    'year': dateutil.relativedelta.relativedelta(years=1)
}


class JalaliBase(models.AbstractModel):
    _inherit = 'base'

    @api.model
    def _read_group_fill_temporal(self, data, groupby, annoted_aggregates,
                                  fill_from=False, fill_to=False, min_groups=False):
        """Helper method for filling date/datetime 'holes' in a result set.

        We are in a use case where data are grouped by a date field (typically
        months but it could be any other interval) and displayed in a chart.

        Assume we group records by month, and we only have data for June,
        September and December. By default, plotting the result gives something
        like::

                                                ___
                                      ___      |   |
                                     |   | ___ |   |
                                     |___||___||___|
                                      Jun  Sep  Dec

        The problem is that December data immediately follow September data,
        which is misleading for the user. Adding explicit zeroes for missing
        data gives something like::

                                                           ___
                             ___                          |   |
                            |   |           ___           |   |
                            |___| ___  ___ |___| ___  ___ |___|
                             Jun  Jul  Aug  Sep  Oct  Nov  Dec

        To customize this output, the context key "fill_temporal" can be used
        under its dictionary format, which has 3 attributes : fill_from,
        fill_to, min_groups (see params of this function)

        Fill between bounds:
        Using either `fill_from` and/or `fill_to` attributes, we can further
        specify that at least a certain date range should be returned as
        contiguous groups. Any group outside those bounds will not be removed,
        but the filling will only occur between the specified bounds. When not
        specified, existing groups will be used as bounds, if applicable.
        By specifying such bounds, we can get empty groups before/after any
        group with data.

        If we want to fill groups only between August (fill_from)
        and October (fill_to)::

                                                     ___
                                 ___                |   |
                                |   |      ___      |   |
                                |___| ___ |___| ___ |___|
                                 Jun  Aug  Sep  Oct  Dec

        We still get June and December. To filter them out, we should match
        `fill_from` and `fill_to` with the domain e.g. ``['&',
        ('date_field', '>=', 'YYYY-08-01'), ('date_field', '<', 'YYYY-11-01')]``::

                                         ___
                                    ___ |___| ___
                                    Aug  Sep  Oct

        Minimal filling amount:
        Using `min_groups`, we can specify that we want at least that amount of
        contiguous groups. This amount is guaranteed to be provided from
        `fill_from` if specified, or from the lowest existing group otherwise.
        This amount is not restricted by `fill_to`. If there is an existing
        group before `fill_from`, `fill_from` is still used as the starting
        group for min_groups, because the filling does not apply on that
        existing group. If neither `fill_from` nor `fill_to` is specified, and
        there is no existing group, no group will be returned.

        If we set min_groups = 4::

                                         ___
                                    ___ |___| ___ ___
                                    Aug  Sep  Oct Nov

        :param list data: the data containing groups
        :param list groupby: list of fields being grouped on
        :param list annoted_aggregates: dict of "<key_name>:<aggregate specification>"
        :param str fill_from: (inclusive) string representation of a
            date/datetime, start bound of the fill_temporal range
            formats: date -> %Y-%m-%d, datetime -> %Y-%m-%d %H:%M:%S
        :param str fill_to: (inclusive) string representation of a
            date/datetime, end bound of the fill_temporal range
            formats: date -> %Y-%m-%d, datetime -> %Y-%m-%d %H:%M:%S
        :param int min_groups: minimal amount of required groups for the
            fill_temporal range (should be >= 1)
        :rtype: list
        :return: list
        """
        # TODO: remove min_groups
        if self.env.user.lang == 'fa_IR':
            first_group = groupby[0]
            field_name = first_group.split(':')[0].split(".")[0]
            field = self._fields[field_name]
            if field.type not in ('date', 'datetime') and not (field.type == 'properties' and ':' in first_group):
                return data

            granularity = first_group.split(':')[1] if ':' in first_group else 'month'
            days_offset = 0
            if granularity == 'week':
                # _read_group_process_groupby week groups are dependent on the
                # locale, so filled groups should be too to avoid overlaps.
                # TODO CHECK jalali calendar
                first_week_day = int(get_lang(self.env).week_start) - 1
                days_offset = first_week_day and 7 - first_week_day
            interval = READ_GROUP_TIME_GRANULARITY[granularity]
            tz = False
            if field.type == 'datetime' and self._context.get('tz') in pytz.all_timezones_set:
                tz = pytz.timezone(self._context['tz'])

            # TODO: refactor remaing lines here

            # existing non null datetimes
            existing = [d[first_group] for d in data if d[first_group]] or [None]
            # assumption: existing data is sorted by field 'groupby_name'
            existing_from, existing_to = existing[0], existing[-1]
            if fill_from:
                fill_from = odoo.fields.Datetime.to_datetime(fill_from) if isinstance(fill_from, datetime.datetime) else odoo.fields.Date.to_date(fill_from)
                fill_from = date_utils.start_of(fill_from, granularity) - datetime.timedelta(days=days_offset)
                if tz:
                    fill_from = tz.localize(fill_from)
            elif existing_from:
                fill_from = existing_from
            if fill_to:
                fill_to = odoo.fields.Datetime.to_datetime(fill_to) if isinstance(fill_to, datetime.datetime) else odoo.fields.Date.to_date(fill_to)
                fill_to = date_utils.start_of(fill_to, granularity) - datetime.timedelta(days=days_offset)
                if tz:
                    fill_to = tz.localize(fill_to)
            elif existing_to:
                fill_to = existing_to

            if not fill_to and fill_from:
                fill_to = fill_from
            if not fill_from and fill_to:
                fill_from = fill_to
            if not fill_from and not fill_to:
                return data

            if min_groups > 0:
                fill_to = max(fill_to, fill_from + (min_groups - 1) * interval)

            if fill_to < fill_from:
                return data

            # required_dates = date_utils.date_range(fill_from, fill_to, interval)
            # TODO Jalali calendar
            # if field.type == 'datetime':
            required_dates = jdate_utils.get_date_range(jdatetime.datetime.fromgregorian(

                            date=fill_from), jdatetime.datetime.fromgregorian(date=fill_to), interval)

            required_dates = [dt.togregorian() for dt in required_dates]
            # else:
            #     required_dates = jdate_utils.get_date_range(jdatetime.date.fromgregorian(

            #                     date=fill_from), jdatetime.date.fromgregorian(date=fill_to), interval)

            #     required_dates = [dt.togregorian() for dt in required_dates]


            if existing[0] is None:
                existing = list(required_dates)
            else:
                # TODO CHECK jalali calendar
                # can't compare datetime.datetime to datetime.date
                existing = [datetime.datetime.combine(dt_list, datetime.datetime.min.time()) for dt_list in existing]
                existing = sorted(set().union(existing, required_dates))

            empty_item = {
                name: self._read_group_empty_value(spec)
                for name, spec in annoted_aggregates.items()
            }
            for group in groupby[1:]:
                empty_item[group] = self._read_group_empty_value(group)

            grouped_data = collections.defaultdict(list)
            for d in data:
                grouped_data[d[first_group]].append(d)

            result = []
            for dt in existing:
                result.extend(grouped_data[dt] or [dict(empty_item, **{first_group: dt})])

            if False in grouped_data:
                result.extend(grouped_data[False])

            return result
        else:
            return super()._read_group_fill_temporal(data, groupby, annoted_aggregates, fill_from, fill_to, min_groups)

    @api.model
    def _read_group_process_groupby(self, gb, query):
        """
            Helper method to collect important information about groupbys: raw
            field name, type, time information, qualified name, ...
        """
        if self.env.user.lang == 'fa_IR':
            split = gb.split(':')
            field = self._fields.get(split[0])
            if not field:
                raise ValueError("Invalid field %r on model %r" % (split[0], self._name))
            field_type = field.type
            gb_function = split[1] if len(split) == 2 else None
            temporal = field_type in ('date', 'datetime')
            tz_convert = field_type == 'datetime' and self._context.get('tz') in pytz.all_timezones
            qualified_field = self._inherits_join_calc(self._table, split[0], query)
            if temporal:
                display_formats = {
                    # Careful with week/year formats:
                    #  - yyyy (lower) must always be used, *except* for week+year formats
                    #  - YYYY (upper) must always be used for week+year format
                    #         e.g. 2006-01-01 is W52 2005 in some locales (de_DE),
                    #                         and W1 2006 for others
                    #
                    # Mixing both formats, e.g. 'MMM YYYY' would yield wrong results,
                    # such as 2006-01-01 being formatted as "January 2005" in some locales.
                    # Cfr: http://babel.pocoo.org/en/latest/dates.html#date-fields
                    'hour': 'hh:00 dd MMM',
                    'day': 'dd MMM yyyy',  # yyyy = normal year
                    'week': "'W'w YYYY",  # w YYYY = ISO week-year
                    'month': 'MMMM yyyy',
                    'quarter': 'QQQ yyyy',
                    'year': 'yyyy',
                }
                time_intervals = {
                    'hour': dateutil.relativedelta.relativedelta(hours=1),
                    'day': dateutil.relativedelta.relativedelta(days=1),
                    'week': datetime.timedelta(days=7),
                    'month': dateutil.relativedelta.relativedelta(months=1),
                    'quarter': dateutil.relativedelta.relativedelta(months=3),
                    'year': dateutil.relativedelta.relativedelta(years=1)
                }
                if tz_convert:
                    qualified_field = "timezone('%s', timezone('UTC', %s))" % (
                        self._context.get('tz', 'UTC'), qualified_field)
                qualified_field_org = "date_trunc('%s', %s::timestamp)" % (gb_function or 'month', qualified_field)
                if gb_function == 'month' or not gb_function:
                    qualified_field = "substring(g2j(%s), 0, 8) || '-01'" % (qualified_field)
                elif gb_function == 'day':
                    qualified_field = "g2j(%s)" % (qualified_field)
                elif gb_function == 'week':
                    qualified_field =\
                        "case" \
                        " when extract(dow from %s) = 0 then g2j(%s - interval '1 day')" \
                        " when extract(dow from %s) = 1 then g2j(%s - interval '2 day')" \
                        " when extract(dow from %s) = 2 then g2j(%s - interval '3 day')" \
                        " when extract(dow from %s) = 3 then g2j(%s - interval '4 day')" \
                        " when extract(dow from %s) = 4 then g2j(%s - interval '5 day')" \
                        " when extract(dow from %s) = 5 then g2j(%s - interval '6 day')" \
                        " when extract(dow from %s) = 6 then g2j(%s)"\
                        " end" % (qualified_field, qualified_field, qualified_field, qualified_field, qualified_field, qualified_field, qualified_field,
                                  qualified_field, qualified_field, qualified_field, qualified_field, qualified_field, qualified_field, qualified_field)
                elif gb_function == 'quarter':
                    qualified_field =\
                        "case" \
                        " when substring(g2j(%s), 6, 2) < '04' then substring(g2j(%s), 0, 5) || '-01-01'" \
                        " when substring(g2j(%s), 6, 2) < '07' then substring(g2j(%s), 0, 5) || '-04-01'" \
                        " when substring(g2j(%s), 6, 2) < '10' then substring(g2j(%s), 0, 5) || '-07-01'" \
                        " when substring(g2j(%s), 6, 2) < '13' then substring(g2j(%s), 0, 5) || '-10-01'" \
                        " end" % (qualified_field, qualified_field, qualified_field, qualified_field,
                                  qualified_field, qualified_field, qualified_field, qualified_field)
                elif gb_function == 'year':
                    qualified_field = "substring(g2j(%s), 0, 5) || '-01-01'" % (qualified_field)

                if field_type == 'datetime':
                    qualified_field += " || ' 00:00:00'"
                    
                if gb_function == 'month' and field_type == 'datetime':
                    qualified_field = qualified_field_org
            if field_type == 'boolean':
                qualified_field = "coalesce(%s,false)" % qualified_field
            return {
                'field': split[0],
                'groupby': gb,
                'type': field_type,
                'display_format': display_formats[gb_function or 'month'] if temporal else None,
                'interval': time_intervals[gb_function or 'month'] if temporal else None,
                'granularity': gb_function or 'month' if temporal else None,
                'tz_convert': tz_convert,
                'qualified_field': qualified_field,
            }
        else:
            return super()._read_group_process_groupby(gb, query)

    @api.model
    def _read_group_prepare_data(self, key, value, groupby_dict):
        """
            Helper method to sanitize the data received by read_group. The None
            values are converted to False, and the date/datetime are formatted,
            and corrected according to the timezones.
        """
        if self.env.user.lang == 'fa_IR':
            value = False if value is None else value
            gb = groupby_dict.get(key)
            if gb and gb['type'] in ('date', 'datetime') and value:
                if isinstance(value, str):
                    dt_format = DEFAULT_SERVER_DATETIME_FORMAT if gb['type'] == 'datetime' else DEFAULT_SERVER_DATE_FORMAT
                    value = jdatetime.datetime.togregorian(jdatetime.datetime.strptime(value, dt_format))
                if gb['tz_convert']:
                    value = pytz.timezone(self._context['tz']).localize(value)
            return value
        else:
            return super()._read_group_prepare_data(key, value, groupby_dict)

    def _read_group_format_result(self, rows_dict, lazy_groupby):
        """
            Helper method to format the data contained in the dictionary data by
            adding the domain corresponding to its values, the groupbys in the
            context and by properly formatting the date/datetime values.

        :param data: a single group
        :param annotated_groupbys: expanded grouping metainformation
        :param groupby: original grouping metainformation
        :param domain: original domain for read_group
        """
        # return super()._read_group_format_result(rows_dict, lazy_groupby)
        if self.env.user.lang == 'fa_IR':
            for group in lazy_groupby:
                field_name = group.split(':')[0].split('.')[0]
                field = self._fields[field_name]

                if field.type in ('date', 'datetime'):
                    locale = get_lang(self.env).code
                    fmt = DEFAULT_SERVER_DATETIME_FORMAT if field.type == 'datetime' else DEFAULT_SERVER_DATE_FORMAT
                    granularity = group.split(':')[1] if ':' in group else 'month'
                    interval = READ_GROUP_TIME_GRANULARITY[granularity]

                elif field.type == "properties":
                    self._read_group_format_result_properties(rows_dict, group)
                    continue

                for row in rows_dict:
                    value = row[group]

                    if field.type in ('many2one', 'many2many') and isinstance(value, models.BaseModel):
                        row[group] = (value.id, value.sudo().display_name) if value else False
                        value = value.id

                    if not value and field.type == 'many2many':
                        other_values = [other_row[group][0] if isinstance(other_row[group], tuple)
                                        else other_row[group].id if isinstance(other_row[group], models.BaseModel)
                                        else other_row[group] for other_row in rows_dict if other_row[group]]
                        additional_domain = [(field_name, 'not in', other_values)]
                    else:
                        additional_domain = [(field_name, '=', value)]

                    if field.type in ('date', 'datetime'):
                        if value and isinstance(value, (datetime.date, datetime.datetime)):
                            range_start = value
                            range_end = value + interval
                            if field.type == 'datetime':
                                j_range_start = jdatetime.datetime.fromgregorian(date=range_start)

                                if interval == dateutil.relativedelta.relativedelta(days=1):
                                    j_range_start, j_range_end = jdate_utils.get_day(j_range_start)
                                elif interval == datetime.timedelta(7):
                                    j_range_start, j_range_end = jdate_utils.get_week(j_range_start)
                                elif interval == dateutil.relativedelta.relativedelta(months=1):
                                    j_range_start, j_range_end = jdate_utils.get_month(j_range_start)
                                elif interval == dateutil.relativedelta.relativedelta(months=3):
                                    j_range_start, j_range_end = jdate_utils.get_quarter(j_range_start)
                                elif interval == dateutil.relativedelta.relativedelta(years=1):
                                    j_range_start, j_range_end = jdate_utils.get_year(j_range_start)
                                j_range_end += jdatetime.timedelta(seconds=1)  # because of using "<" operator in the domain
                                label = ''

                                

                                tzinfo = None
                                if self._context.get('tz') in pytz.all_timezones_set:
                                    tzinfo = pytz.timezone(self._context['tz'])
                                    range_start = tzinfo.localize(range_start).astimezone(pytz.utc)
                                    # take into account possible hour change between start and end
                                    range_end = tzinfo.localize(range_end).astimezone(pytz.utc)
                                    # range_start = pytz.timezone(self._context.get('tz', 'UTC')).localize(
                                    #     jdatetime.datetime.togregorian(j_range_start))
                                    # range_end = pytz.timezone(self._context.get('tz', 'UTC')).localize(
                                    #     jdatetime.datetime.togregorian(j_range_end))
                                # TODO CHECK jalali calendar
                                if granularity == "hour":
                                    label = str(j_range_start.year) + ' ' + \
                                            jdate_utils.get_month_name(j_range_start, locale) + ' ' + str(j_range_start.day)
                                if granularity == "day":
                                    label = str(j_range_start.year) + ' ' + \
                                            jdate_utils.get_month_name(j_range_start, locale) + ' ' + str(j_range_start.day)
                                if granularity == "week":
                                    label = ('W' if locale == 'en_US' else 'ه‌') + \
                                            str(j_range_start.weeknumber()) + ' ' + str(j_range_start.year)
                                if granularity == "month":
                                    label = jdate_utils.get_month_name(j_range_start, locale) + ' ' + str(j_range_start.year)
                                if granularity == "quarter":
                                    label = jdate_utils.get_quarter_name(j_range_start, locale) + ' ' + str(j_range_start.year)
                                if granularity == "year":
                                    label = str(j_range_end.year)
                            else:
                                j_range_start = jdatetime.date.fromgregorian(date=range_start)

                                if interval == dateutil.relativedelta.relativedelta(days=1):
                                    j_range_start, j_range_end = jdate_utils.get_day(j_range_start)
                                elif interval == datetime.timedelta(7):
                                    j_range_start, j_range_end = jdate_utils.get_week(j_range_start)
                                elif interval == dateutil.relativedelta.relativedelta(months=1):
                                    j_range_start, j_range_end = jdate_utils.get_month(j_range_start)
                                elif interval == dateutil.relativedelta.relativedelta(months=3):
                                    j_range_start, j_range_end = jdate_utils.get_quarter(j_range_start)
                                elif interval == dateutil.relativedelta.relativedelta(years=1):
                                    j_range_start, j_range_end = jdate_utils.get_year(j_range_start)
                                j_range_end += jdatetime.timedelta(seconds=1)  # because of using "<" operator in the domain
                                label = ''
                                # TODO CHECK jalali calendar
                                # j_range_start = jdatetime.date.fromgregorian(date=range_start)
                                # label = str(j_range_start.year) + ' ' + \
                                # jdate_utils.get_month_name(j_range_start, locale) + ' ' + str(j_range_start.day)
                                if granularity == "hour":
                                    label = str(j_range_start.year) + ' ' + \
                                            jdate_utils.get_month_name(j_range_start, locale) + ' ' + str(j_range_start.day)
                                if granularity == "day":
                                    label = str(j_range_start.year) + ' ' + \
                                            jdate_utils.get_month_name(j_range_start, locale) + ' ' + str(j_range_start.day)
                                # TODO week groupby
                                if granularity == "week":
                                    label = ('W' if locale == 'en_US' else 'ه‌') + \
                                            str(j_range_start.weeknumber()) + ' ' + str(j_range_start.year)
                                if granularity == "month":
                                    label = jdate_utils.get_month_name(j_range_start, locale) + ' ' + str(j_range_start.year)
                                if granularity == "quarter":
                                    label = jdate_utils.get_quarter_name(j_range_start, locale) + ' ' + str(j_range_start.year)
                                if granularity == "year":
                                    label = str(j_range_start.year)

                            if self._context.get('tz') in pytz.all_timezones_set:
                                range_start = pytz.timezone(self._context.get('tz', 'UTC')).localize(
                                    jdatetime.datetime.togregorian(j_range_start))
                                range_end = pytz.timezone(self._context.get('tz', 'UTC')).localize(
                                    jdatetime.datetime.togregorian(j_range_end))
                            range_start = range_start.strftime(fmt)
                            range_end = range_end.strftime(fmt)
                            row[group] = label  # TODO should put raw data
                            row.setdefault('__range', {})[group] = {'from': range_start, 'to': range_end}
                            additional_domain = [
                                '&',
                                    (field_name, '>=', range_start),
                                    (field_name, '<', range_end),
                            ]
                        elif not value:
                            # Set the __range of the group containing records with an unset
                            # date/datetime field value to False.
                            row.setdefault('__range', {})[group] = False

                    row['__domain'] = expression.AND([row['__domain'], additional_domain])
        else:
            return super()._read_group_format_result(rows_dict, lazy_groupby)


    @api.model
    def _read_group(self, domain, groupby=(), aggregates=(), having=(), offset=0, limit=None, order=None):
        """ Get fields aggregations specified by ``aggregates`` grouped by the given ``groupby``
        fields where record are filtered by the ``domain``.

        :param list domain: :ref:`A search domain <reference/orm/domains>`. Use an empty
                list to match all records.
        :param list groupby: list of groupby descriptions by which the records will be grouped.
                A groupby description is either a field (then it will be grouped by that field)
                or a string `'field:granularity'`. Right now, the only supported granularities
                are `'day'`, `'week'`, `'month'`, `'quarter'` or `'year'`, and they only make sense for
                date/datetime fields.
        :param list aggregates: list of aggregates specification.
                Each element is `'field:agg'` (aggregate field with aggregation function `'agg'`).
                The possible aggregation functions are the ones provided by
                `PostgreSQL <https://www.postgresql.org/docs/current/static/functions-aggregate.html>`_,
                `'count_distinct'` with the expected meaning and `'recordset'` to act like `'array_agg'`
                converted into a recordset.
        :param list having: A domain where the valid "fields" are the aggregates.
        :param int offset: optional number of groups to skip
        :param int limit: optional max number of groups to return
        :param str order: optional ``order by`` specification, for
                overriding the natural sort ordering of the groups,
                see also :meth:`~.search`.
        :return: list of tuple containing in the order the groups values and aggregates values (flatten):
                `[(groupby_1_value, ... , aggregate_1_value_aggregate, ...), ...]`.
                If group is related field, the value of it will be a recordset (with a correct prefetch set).

        :rtype: list
        :raise AccessError: if user is not allowed to access requested information
        """
        self.check_access_rights('read')

        if expression.is_false(self, domain):
            if not groupby:
                # when there is no group, postgresql always return a row
                return [tuple(
                    self._read_group_empty_value(spec)
                    for spec in itertools.chain(groupby, aggregates)
                )]
            return []

        query = self._search(domain)

        fnames_to_flush = OrderedSet()

        groupby_terms: dict[str, SQL] = {}
        for spec in groupby:
            groupby_terms[spec], fnames_used = self._read_group_groupby(spec, query)
            fnames_to_flush.update(fnames_used)

        select_terms: list[SQL] = []
        for spec in aggregates:
            sql_expr, fnames_used = self._read_group_select(spec, query)
            select_terms.append(sql_expr)
            fnames_to_flush.update(fnames_used)

        sql_having, fnames_used = self._read_group_having(having, query)
        fnames_to_flush.update(fnames_used)

        sql_order, sql_extra_groupby, fnames_used = self._read_group_orderby(order, groupby_terms, query)
        fnames_to_flush.update(fnames_used)

        groupby_terms = list(groupby_terms.values())

        query_parts = [
            SQL("SELECT %s", SQL(", ").join(groupby_terms + select_terms)),
            SQL("FROM %s", query.from_clause),
        ]
        if query.where_clause:
            query_parts.append(SQL("WHERE %s", query.where_clause))
        if groupby_terms:
            if sql_extra_groupby:
                groupby_terms.append(sql_extra_groupby)
            query_parts.append(SQL("GROUP BY %s", SQL(", ").join(groupby_terms)))
        if sql_having:
            query_parts.append(SQL("HAVING %s", sql_having))
        if sql_order:
            query_parts.append(SQL("ORDER BY %s", sql_order))
        if limit:
            query_parts.append(SQL("LIMIT %s", limit))
        if offset:
            query_parts.append(SQL("OFFSET %s", offset))

        self._flush_search(domain, fnames_to_flush)
        if fnames_to_flush:
            self._read_group_check_field_access_rights(fnames_to_flush)

        self.env.cr.execute(SQL("\n").join(query_parts))
        # row_values: [(a1, b1, c1), (a2, b2, c2), ...]
        row_values = self.env.cr.fetchall()

        if not row_values:
            return row_values
        
                
        if row_values and order and len(order.split(':')[0].split(",")) == 1:
            if ":month" in order:
                new_jalali = [
                    SQL("SELECT %s", SQL(", ").join([SQL('SUBSTRING(g2j({0}), 1, 7) AS month'.format(".".join([query.table, order.split(':')[0]])))] + select_terms)),
                    SQL("FROM %s", query.from_clause),
                ]
                new_jalali.append(SQL("WHERE %s", query.where_clause))
                if groupby_terms:
                    if sql_extra_groupby:
                        groupby_terms.append(sql_extra_groupby)
                new_jalali.append(SQL("GROUP BY month"))
                if sql_having:
                    new_jalali.append(SQL("HAVING %s", sql_having))
                if sql_order:
                    new_jalali.append(SQL("ORDER BY month"))
                if limit:
                    new_jalali.append(SQL("LIMIT %s", limit))
                if offset:
                    new_jalali.append(SQL("OFFSET %s", offset))

                self.env.cr.execute(SQL("\n").join(new_jalali))
                jalali_values = self.env.cr.fetchall()
                jalali_formated = []
                for i in jalali_values:
                    if i[0] != None:
                        jalali_formated.append((jdatetime.datetime(int(i[0].split('-')[0]), int(i[0].split('-')[1]),1).togregorian(), *i[1:]))
                    else:
                        jalali_formated.append((i))
                row_values = jalali_formated

        if row_values and order and len(order.split(':')[0].split(",")) == 1:
            if ":year" in order:
                new_jalali = [
                    SQL("SELECT %s", SQL(", ").join([SQL('SUBSTRING(g2j({0}), 1, 4) AS month'.format(".".join([query.table, order.split(':')[0]])))] + select_terms)),
                    SQL("FROM %s", query.from_clause),
                ]
                new_jalali.append(SQL("WHERE %s", query.where_clause))
                if groupby_terms:
                    if sql_extra_groupby:
                        groupby_terms.append(sql_extra_groupby)
                new_jalali.append(SQL("GROUP BY month"))
                if sql_having:
                    new_jalali.append(SQL("HAVING %s", sql_having))
                if sql_order:
                    new_jalali.append(SQL("ORDER BY month"))
                if limit:
                    new_jalali.append(SQL("LIMIT %s", limit))
                if offset:
                    new_jalali.append(SQL("OFFSET %s", offset))

                self.env.cr.execute(SQL("\n").join(new_jalali))
                jalali_values = self.env.cr.fetchall()
                jalali_formated = []
                for i in jalali_values:
                    if i[0] != None:
                        jalali_formated.append((jdatetime.datetime(int(i[0]), 1, 1).togregorian(), *i[1:]))
                    else:
                        jalali_formated.append((i))
                row_values = jalali_formated

        if row_values and order and len(order.split(':')[0].split(",")) == 1:
            if ":quarter" in order:
                new_jalali = [
                    SQL("SELECT %s", SQL(", ").join([SQL('SUBSTRING(g2j({0}), 1, 4) AS year'.format(".".join([query.table, order.split(':')[0]]))), SQL('get_quarter(SUBSTRING(g2j({0}), 1, 7)) AS quarter'.format(".".join([query.table, order.split(':')[0]])))] + select_terms)),
                    SQL("FROM %s", query.from_clause),
                ]
                new_jalali.append(SQL("WHERE %s", query.where_clause))
                if groupby_terms:
                    if sql_extra_groupby:
                        groupby_terms.append(sql_extra_groupby)
                new_jalali.append(SQL("GROUP BY year, quarter"))
                if sql_having:
                    new_jalali.append(SQL("HAVING %s", sql_having))
                if sql_order:
                    new_jalali.append(SQL("ORDER BY year, quarter"))
                if limit:
                    new_jalali.append(SQL("LIMIT %s", limit))
                if offset:
                    new_jalali.append(SQL("OFFSET %s", offset))

                self.env.cr.execute(SQL("\n").join(new_jalali))
                jalali_values = self.env.cr.fetchall()
                jalali_formated = []
                for i in jalali_values:
                    if i[0] != None:
                        if i[1] == 1:
                            jalali_formated.append((jdatetime.datetime(int(i[0]), 1, 1).togregorian(), *i[2:]))
                        elif i[1] == 2:
                            jalali_formated.append((jdatetime.datetime(int(i[0]), 4, 1).togregorian(), *i[2:]))
                        elif i[1] == 3:
                            jalali_formated.append((jdatetime.datetime(int(i[0]), 7, 1).togregorian(), *i[2:]))
                        elif i[1] == 4:
                            jalali_formated.append((jdatetime.datetime(int(i[0]), 10, 1).togregorian(), *i[2:]))
                        else:
                            jalali_formated.append(None, *i[2:])
                    else:
                        jalali_formated.append((i[:1] + i[2:]))
                row_values = jalali_formated

        # post-process values column by column
        column_iterator = zip(*row_values)

        # column_result: [(a1, a2, ...), (b1, b2, ...), (c1, c2, ...)]
        column_result = []
        for spec in groupby:
            try:
                column = self._read_group_postprocess_groupby(spec, next(column_iterator))
                column_result.append(column)
            except StopIteration:
                break
        for spec in aggregates:
            try:
                column = self._read_group_postprocess_aggregate(spec, next(column_iterator))
                column_result.append(column)
            except StopIteration:
                break
        assert next(column_iterator, None) is None

        # return [(a1, b1, c1), (a2, b2, c2), ...]
        return list(zip(*column_result))