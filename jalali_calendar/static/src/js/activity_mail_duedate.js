/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { Activity } from "@mail/core/web/activity";
import { deserializeDateTime } from "@web/core/l10n/dates";


patch(Activity.prototype, {

      get displayDueDate() {
            if(luxon.DateTime.now().locale == 'fa-IR'){
                  return deserializeDateTime(this.props.data.date_deadline).toLocaleString(
                        luxon.DateTime.DATE_SHORT
                  );
            }else{
                  return String(this.props.data.date_deadline);
            }
            
      }
})