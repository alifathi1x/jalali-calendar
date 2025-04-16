from odoo import _, models


class JalaliHttp(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        result = super(JalaliHttp, self).session_info()
        if result and result.get("user_context", False):
            user_context = result.get("user_context")
            user_context['calendar_type'] = self.env.user.lang == 'fa_IR' and 'jalali' or 'gregorian'
        return result
