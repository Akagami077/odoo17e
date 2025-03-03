/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { GanttRenderer } from "@web_gantt/gantt_renderer";
import { AppointmentBookingGanttPopover } from "@appointment/views/gantt/gantt_popover";
const { DateTime } = luxon;

export class AppointmentBookingGanttRenderer extends GanttRenderer {
    static components = {
        ...GanttRenderer.components,
        Popover: AppointmentBookingGanttPopover,
    }
    static headerTemplate = "appointment.AppointmentBookingGanttRenderer.Header";

    /**
     * @override
     */
    setup() {
        super.setup();
        this.orm = useService("orm");
    }

    /**
     * @override
     * If multiple columns have been selected, remove the default duration from the context so that
     * the stop matches the end of the selection instead of being redefined to match the appointment duration.
     */
    onCreate(rowId, columnStart, columnStop) {
        const { start, stop } = this.getColumnStartStop(columnStart, columnStop);
        const context = this.model.getDialogContext({rowId, start, stop, withDefault: true});
        if (columnStart != columnStop){
            delete context['default_duration'];
        }
        this.props.create(context);
    }

    /**
     * @override
     */
    enrichPill(pill) {
        const enrichedPill = super.enrichPill(pill);
        const { record } = pill;
        const now = DateTime.now()
        // see o-colors-complete for array of colors to index into
        let color = false;
        if (!record.appointment_attended && now.diff(record.start, ['minutes']).minutes > 15){
            color = 1  // red
        } else if (record.appointment_attended) {
            color = 10  // green
        } else {
            color = 8  // blue
        }
        if (color) {
            enrichedPill.className += ` o_gantt_color_${color}`;
        }
        return enrichedPill;
    }

    /**
     * Display 'Add Leaves' action button if grouping by appointment resources.
     */
    get showAddLeaveButton() {
        return !!(this.model.metaData.groupedBy && this.model.metaData.groupedBy[0] === 'appointment_resource_id');
    }

    async onClickAddLeave() {
        this.env.services.action.doAction({
            name: _t("Add Closing Day(s)"),
            type: "ir.actions.act_window",
            res_model: "appointment.manage.leaves",
            view_mode: "form",
            views: [[false, "form"]],
            target: "new",
            context: {},
        }, {
            onClose: () => this.model.fetchData(),
        });
    }

    /**
     * @override
     * Async copy of the overriden method
     */
    async onPillClicked(ev, pill) {
        if (this.popover.isOpen) {
            return;
        }
        const popoverTarget = ev.target.closest(".o_gantt_pill_wrapper");
        this.popover.open(popoverTarget, await this.getPopoverProps(pill));
    }
    /**
     * @override
     */
    async getPopoverProps(pill) {
        const popoverProps = super.getPopoverProps(pill);
        const { record } = pill;
        const attendedState = record.appointment_attended;
        const partner_ids = record.partner_ids || [];
        let contact_partner_id = false;
        if (record.partner_ids) {
            contact_partner_id = record.partner_id
            ? partner_ids.find(partner_id => partner_id != record.partner_id[0])
            : partner_ids.length ? partner_ids[0] : false;
        }
        const popoverValues = contact_partner_id
            ? await this.orm.read(
                'res.partner',
                [contact_partner_id], ['name', 'email', 'phone']
            )
            : [{
                id: false,
                name: '',
                email: '',
                phone: '',
            }];
        Object.assign(popoverProps, {
            markAsAttendedCallback: () => {
                this.orm.call(
                    'calendar.event',
                    'write',
                    [record.id, {
                        appointment_attended: !attendedState,
                    }],
                ).then(() => this.model.fetchData());
            },
            attendedState,
            title: popoverValues[0].name || this.getDisplayName(pill),
            context: {
                ...popoverProps.context,
                gantt_pill_contact_name: popoverValues[0].name,
                gantt_pill_contact_email: popoverValues[0].email,
                gantt_pill_contact_phone: popoverValues[0].phone,
            }
        });
        return popoverProps;
    }
}
