from . import models
# -*- coding: utf-8 -*-

import inspect
from datetime import date, datetime

import jdatetime

from odoo import fields
from odoo.addons.base.models.ir_actions_report import IrActionsReport
from odoo.tools.safe_eval import time

from . import (base, base_import, ir_http, ir_sequence, misc, models,
               res_company, res_users, sale_order)

from ..globals import jdate_utils

def my_render_template(self, template, values=None):
    """Allow to render a QWeb template python-side. This function returns the 'ir.ui.view'
    render but embellish it with some variables/methods used in reports.
    :param values: additional methods/variables used in the rendering
    :returns: html representation of the template
    :rtype: bytes
    """
    if values is None:
        values = {}

    # Browse the user instead of using the sudo self.env.user
    user = self.env['res.users'].browse(self.env.uid)
    view_obj = self.env['ir.ui.view'].with_context(inherit_branding=False)
    values.update(
        time=time,
        context_timestamp=lambda t: fields.Datetime.context_timestamp(self.with_context(tz=user.tz), t),
        user=user,
        res_company=self.env.company,
        web_base_url=self.env['ir.config_parameter'].sudo().get_param('web.base.url', default=''),
    )
    res = view_obj._render_template(template, values).encode()
    try:
        if self.env.user.lang == 'fa_IR':
            str_res = res.decode()
            for doc in values['docs']:
                for i in inspect.getmembers(doc):
                    if i[0].startswith('_'):
                        continue
                    elif isinstance(i[1],(date,datetime,)):
                        str_res= str_res.replace(i[1].strftime('%Y/%m/%d'),jdate_utils.e2p(jdatetime.date.fromgregorian(date=i[1]).strftime('%Y/%m/%d')))
                        str_res= str_res.replace(i[1].strftime('%Y-%m-%d'),jdate_utils.e2p(jdatetime.date.fromgregorian(date=i[1]).strftime('%Y-%m-%d')))
                    continue
            res = str_res.encode()
    except:
        pass
    return res


IrActionsReport._render_template = my_render_template
