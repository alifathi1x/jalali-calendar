/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { DateTimeField } from "@web/views/fields/datetime/datetime_field";
import {
    areDatesEqual,
    deserializeDate,
    deserializeDateTime,
    formatDate,
    formatDateTime,
    today,
} from "@web/core/l10n/dates";
patch(DateTimeField.prototype, {
    getFormattedValue(valueIndex) {
        const value = this.values[valueIndex];
        const resultDate = value
            ? this.field.type === "date"
                ? formatDate(value)
                : formatDateTime(value)
            : "";
        if (!value || !resultDate) {
            return resultDate;
        }
        const dateOptions = { year: "numeric", month: "2-digit", day: "2-digit" };
        const formattedDate = value.reconfigure().toLocaleString(dateOptions);
        if (resultDate.split(" ")[1]) {
            return `${formattedDate} ${resultDate.split(" ")[1]}`;
        } else {
            return formattedDate;
        }
    }
});