from odoo import models, api
import jdatetime

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def convert_jalali(self, field):
        if self.env.user.lang == 'fa_IR':
            if field == 'date_order':
                return jdatetime.date.fromgregorian(date=self.date_order)
            elif field == 'validity_date':
                return jdatetime.date.fromgregorian(date=self.validity_date)
        else:
            if field == 'date_order':
                return self.date_order
            elif field == 'validity_date':
                return self.validity_date


