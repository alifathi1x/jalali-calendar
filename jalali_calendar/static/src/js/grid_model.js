/** @odoo-module **/

import { GridDataPoint } from "@web_grid/views/grid_model";
import { GridNavigationInfo } from "@web_grid/views/grid_model";
import { patch } from "@web/core/utils/patch";

import { serializeDate } from "@web/core/l10n/dates";
import { _t } from "@web/core/l10n/translation";


patch(GridNavigationInfo.prototype, {
      get periodStart() {
            if (this.range.span !== "week") {
                const tstart_date = farvardin.gregorianToSolar(this.anchor.year, this.anchor.month, this.anchor.day);
                const jstart_date = new persianDate([tstart_date[0], tstart_date[1], tstart_date[2]]).toCalendar('persian').startOf(this.range.span).toCalendar('gregorian');
                
                return this.anchor.set({year: jstart_date.year(), month:jstart_date.month(), day:jstart_date.date()});
            }
            return this.anchor.set({ weekday: this._targetWeekday }).startOf("day");
      },
      get periodEnd() {
            if (this.range.span !== "week") {
                const tstop_date = farvardin.gregorianToSolar(this.anchor.year, this.anchor.month, this.anchor.day);
                const jend_date = new persianDate([tstop_date[0], tstop_date[1], tstop_date[2]]).toCalendar('persian').endOf(this.range.span).toCalendar('gregorian');
    
                return this.anchor.set({year: jend_date.year(), month:jend_date.month(), day:jend_date.date()}).endOf("day");
            }
            return this.anchor
                .set({ weekday: this._targetWeekday })
                .plus({ weeks: 1, days: -1 })
                .endOf("day");
      }
});

patch(GridDataPoint.prototype, {
      _getDateColumnTitle(date) {
            if (this.navigationInfo.range.step in this.dateFormat) {
                return date.reconfigure({ outputCalendar: 'persian', locale: 'fa' }).toLocaleString({weekday:"long", month:"long", day:"numeric"})
            }
            return serializeDate(date);
      }

  });