from odoo import models, fields, api, exceptions, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

import datetime
import jdatetime
import num2fawords

class JalaliResUser(models.Model):
    _inherit = "res.users"

    def get_jalali_date(self, g_date):
        if isinstance(g_date, str):
            g_date_obj = datetime.datetime.strptime(g_date, DEFAULT_SERVER_DATE_FORMAT)
        else:
            g_date_obj = g_date

        j_date_obj = jdatetime.date.fromgregorian(date=g_date_obj)
        j_date = jdatetime.date.strftime(j_date_obj, DEFAULT_SERVER_DATE_FORMAT)

        return j_date

    def get_jalali_datetime(self, g_datetime):
        if isinstance(g_datetime, str):
            g_datetime_obj = datetime.datetime.strptime(g_datetime, DEFAULT_SERVER_DATETIME_FORMAT)
        else:
            g_datetime_obj = g_datetime

        j_datetime_obj = jdatetime.datetime.fromgregorian(date=g_datetime_obj)
        j_datetime = jdatetime.datetime.strftime(j_datetime_obj, DEFAULT_SERVER_DATETIME_FORMAT)

        return j_datetime

    def get_farsi_words(self, number):
        return num2fawords.words(number)
