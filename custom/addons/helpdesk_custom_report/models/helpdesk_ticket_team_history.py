from odoo import api, fields, models, tools
from datetime import datetime


class HelpdeskTicketTeamHistory(models.Model):
    _name = 'helpdesk.ticket.team.history'
    _description = 'Helpdesk Ticket Team History'
    _order = 'in_time desc'

    # Required references
    ticket_id = fields.Many2one(
        'helpdesk.ticket',
        string='Ticket',
        required=True
    )
    team_id = fields.Many2one(
        'helpdesk.team',
        string='Team',
        required=True
    )
    in_time = fields.Datetime(
        string='In Time',
        required=True
    )
    out_time = fields.Datetime(
        string='Out Time'
    )

    # Computed field for duration
    dur = fields.Float(
        string='Duration (Hours)',
        compute='_compute_dur',
        store=True
    )

    # SLA references
    sla_id = fields.Many2one(
        'helpdesk.sla',
        string='SLA'
    )
    sla_time = fields.Float(
        string='SLA Time (Hours)',
        help="Number of hours set by the SLA for this Ticket Type / Team."
    )

    # Ticket type reference
    ticket_type_id = fields.Many2one(
        'helpdesk.ticket.type',
        string='Ticket Type'
    )

    # SLA comparison fields
    sla_status = fields.Selection(
        [('within', 'Within SLA'), ('above', 'Above SLA')],
        string='SLA Status',
        compute='_compute_sla_exceed',
        store=True
    )
    time_above_sla = fields.Float(
        string='Time Above SLA',
        compute='_compute_sla_exceed',
        store=True,
        help="Duration (in hours) exceeding the SLA time, if any."
    )

    # User assigned to the ticket
    user_id = fields.Many2one(
        'res.users',
        string='Assigned User',
        help="User assigned to this ticket during this period."
    )

    # New field to record the signee's last message
    signee_last_message = fields.Text(
        string='Signee Last Message',
        help="The last message or comment left by the assigned user during this period."
    )

    @api.depends('in_time', 'out_time')
    def _compute_dur(self):
        """Compute how many hours the ticket stayed in this team (in_time -> out_time)."""
        for record in self:
            if record.in_time and record.out_time:
                diff = record.out_time - record.in_time
                record.dur = diff.total_seconds() / 3600.0
            else:
                record.dur = 0.0

    @api.depends('dur', 'sla_time')
    def _compute_sla_exceed(self):
        """
        Check if the actual duration (dur) is above or within the SLA time (sla_time).
        - If dur > sla_time => sla_status = 'above', time_above_sla = dur - sla_time
        - Otherwise => sla_status = 'within', time_above_sla = 0.0
        """
        for record in self:
            if record.sla_time and record.dur > record.sla_time:
                record.sla_status = 'above'
                record.time_above_sla = record.dur - record.sla_time
            else:
                record.sla_status = 'within'
                record.time_above_sla = 0.0

    @api.model
    def create(self, vals):
        """
        Override create method to set the `user_id` and initialize the signee's last message if provided.
        """
        if 'ticket_id' in vals:
            ticket = self.env['helpdesk.ticket'].browse(vals['ticket_id'])
            vals['user_id'] = ticket.user_id.id if ticket.user_id else None

            # Automatically fetch the signee's last message during this period
            if 'in_time' in vals:
                in_time = vals['in_time']
                out_time = vals.get('out_time', fields.Datetime.now())
                messages = self.env['mail.message'].search([
                    ('res_id', '=', ticket.id),
                    ('model', '=', 'helpdesk.ticket'),
                    ('author_id', '=', ticket.user_id.partner_id.id),
                    ('message_type', '=', 'comment'),  # فقط الرسائل المكتوبة
                    ('date', '>=', in_time),
                    ('date', '<=', out_time)
                ], order='date desc', limit=1)

                if messages:
                    vals['signee_last_message'] = tools.html2plaintext(messages.body).strip()

        return super(HelpdeskTicketTeamHistory, self).create(vals)

class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    def write(self, vals):
        """
        Override write method to:
        - Update `user_id`, `ticket_type_id`, and `signee_last_message` in the latest history record.
        - Update `sla_id` and `sla_time` in the latest history record when `team_id` or `ticket_type_id` changes.
        """
        for ticket in self:
            last_history = self.env['helpdesk.ticket.team.history'].search(
                [('ticket_id', '=', ticket.id), ('team_id', '=', ticket.team_id.id)],
                order='in_time desc',
                limit=1
            )

            if last_history:
                history_vals = {}

                if 'user_id' in vals:
                    history_vals['user_id'] = vals['user_id']

                if 'ticket_type_id' in vals:
                    history_vals['ticket_type_id'] = vals['ticket_type_id']

                in_time = last_history.in_time
                out_time = last_history.out_time or fields.Datetime.now()

                messages = self.env['mail.message'].search([
                    ('res_id', '=', ticket.id),
                    ('model', '=', 'helpdesk.ticket'),
                    ('message_type', '=', 'comment'),
                    ('date', '>=', in_time),
                    ('date', '<=', out_time)
                ], order='date desc', limit=1)


                if messages:
                    history_vals['signee_last_message'] = tools.html2plaintext(messages.body).strip()

                team_changed = 'team_id' in vals
                type_changed = 'ticket_type_id' in vals

                if team_changed or type_changed:
                    new_team_id = vals.get('team_id', ticket.team_id.id)
                    new_type_id = vals.get('ticket_type_id', ticket.ticket_type_id.id)

                    sla_record = self._find_sla(new_team_id, new_type_id)
                    sla_id = sla_record.id if sla_record else False
                    sla_time = sla_record.time if sla_record else 0.0

                    history_vals.update({
                        'sla_id': sla_id,
                        'sla_time': sla_time,
                    })

                last_history.write(history_vals)

        return super(HelpdeskTicket, self).write(vals)

    def _find_sla(self, team_id, ticket_type_id):
        """
        العثور على SLA المناسب بناءً على الفريق ونوع التذكرة.
        """
        domain = [('team_id', '=', team_id)]
        if ticket_type_id:
            domain.append(('ticket_type_ids', 'in', ticket_type_id))

        sla = self.env['helpdesk.sla'].search(domain, limit=1)
        return sla


class HelpdeskSLA(models.Model):
    _inherit = 'helpdesk.sla'

    def write(self, vals):
        """
        Override write to update `sla_time` in `helpdesk.ticket.team.history`
        when the SLA's `time` field is updated.
        """
        result = super().write(vals)

        if 'time' in vals:
            for sla in self:
                tickets = self.env['helpdesk.ticket'].search([('team_id', '=', sla.team_id.id)])

                for ticket in tickets:
                    last_history = self.env['helpdesk.ticket.team.history'].search([
                        ('ticket_id', '=', ticket.id),
                        ('team_id', '=', sla.team_id.id),
                        ('sla_id', '=', sla.id),
                    ], order='in_time desc', limit=1)

                    if last_history:
                        last_history.write({'sla_time': vals['time']})

        return result