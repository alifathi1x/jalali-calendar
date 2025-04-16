/** @odoo-module **/

import { GanttRenderer } from "@web_gantt/gantt_renderer";
import { patch } from "@web/core/utils/patch";

import { _t } from "@web/core/l10n/translation";
import { formatDateTime, serializeDate, serializeDateTime } from "@web/core/l10n/dates";

import {
    dateAddFixedOffset,
    getCellColor,
    getColorIndex,
    useGanttConnectorDraggable,
    useGanttDraggable,
    useGanttResizable,
    useGanttUndraggable,
    useMultiHover,
} from "@web_gantt/gantt_helpers";



const { DateTime } = luxon;


patch(GanttRenderer.prototype, {
  computeColumns() {
    this.columns = [];
    this.subColumns = [];
    this.dateGridColumns = [];

    var { scale, startDate, stopDate } = this.model.metaData;
    const { cellPart, cellTime, interval, time } = scale;
    const now = DateTime.local();
    let cellIndex = 1;
    let colOffset = 1;
    let date;

    const tstart_date = farvardin.gregorianToSolar(startDate.year, startDate.month, startDate.day);
    const tstop_date = farvardin.gregorianToSolar(stopDate.year, stopDate.month, stopDate.day);

    if(scale.id == "month"){
        console.log("object");

        const diff = now.startOf("month").diff(startDate, 'months').toObject();
        
        const gfocus = now.minus(diff)
        const jfocus = farvardin.gregorianToSolar(gfocus.year, gfocus.month, gfocus.day)

        const jstart_date = new persianDate([jfocus[0], jfocus[1], jfocus[2]]).toCalendar('persian').startOf('month').startOf('day').toCalendar('gregorian');
        const jend_date = new persianDate([jfocus[0], jfocus[1], jfocus[2]]).toCalendar('persian').endOf('month').endOf('day').toCalendar('gregorian');

        startDate = startDate.set({year: jstart_date.year(), month:jstart_date.month(), day:jstart_date.date()});
        stopDate = stopDate.set({year: jend_date.year(), month:jend_date.month(), day:jend_date.date()});


    }
    if(scale.id == "year"){



        const jstart_date = new persianDate([tstart_date[0] +1, tstart_date[1], tstart_date[2]]).toCalendar('persian').startOf('year').toCalendar('gregorian');
        const jend_date = new persianDate([tstart_date[0] +1, tstart_date[1], tstart_date[2]]).toCalendar('persian').endOf('year').toCalendar('gregorian');

        startDate = startDate.set({year: jstart_date.year(), month:jstart_date.month()+1});
        stopDate = stopDate.set({year: jend_date.year(), month:jend_date.month()});
    }

    for (date = startDate; date <= stopDate; date = date.plus({ [interval]: 1 })) {
        const start = date;
        const stop = date.endOf(interval);
        const index = cellIndex++;
        const columnId = `__column__${index}`;
        const column = {
            id: columnId,
            grid: { column: [colOffset, cellPart] },
            start,
            stop,
        };
        const isToday =
            (["week", "month"].includes(scale.id) && date.hasSame(now, "day")) ||
            (scale.id === "year" && date.hasSame(now, "month")) ||
            (scale.id === "day" && date.hasSame(now, "hour"));

        if (isToday) {
            column.isToday = true;
        }

        this.columns.push(column);

        for (let i = 0; i < cellPart; i++) {
            const subCellStart = dateAddFixedOffset(start, { [time]: i * cellTime });
            const subCellStop = dateAddFixedOffset(start, {
                [time]: (i + 1) * cellTime,
                seconds: -1,
            });
            this.subColumns.push({ start: subCellStart, stop: subCellStop, isToday, columnId });
            this.dateGridColumns.push(subCellStart);
        }

        colOffset += cellPart;
    }

    this.dateGridColumns.push(date);
  },
  getFormattedFocusDate() {
    const { focusDate, scale } = this.model.metaData;
    const { format, id: scaleId } = scale;
    switch (scaleId) {
        case "day":
        case "month":
            return focusDate.reconfigure({ outputCalendar: 'persian', locale: 'fa' }).toLocaleString({ month: 'long',  year: 'numeric'})
        case "year":
            return focusDate.reconfigure({ outputCalendar: 'persian', locale: 'fa' }).toLocaleString({ year: 'numeric'});
        case "week": {
            const { startDate, stopDate } = this.model.metaData;
            const start = formatDateTime(startDate, { format });
            const stop = formatDateTime(stopDate, { format });
            return `${startDate.reconfigure({ outputCalendar: 'persian', locale: 'fa' }).toLocaleString({ year: 'numeric', month: "long", day: "numeric"})} - ${stopDate.reconfigure({ outputCalendar: 'persian', locale: 'fa' }).toLocaleString({ year: 'numeric', month: "long", day: "numeric"})}`;
        }
        default:
            throw new Error(`Unknown scale id "${scaleId}".`);
    }
  }

  });