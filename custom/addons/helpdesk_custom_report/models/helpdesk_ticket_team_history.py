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
                    ('date', '>=', in_time),
                    ('date', '<=', out_time)
                ], order='date desc', limit=1)
                if messages:
                    vals['signee_last_message'] = tools.html2plaintext(messages.body).strip()

        return super(HelpdeskTicketTeamHistory, self).create(vals)

    def write(self, vals):
        """
        Override write method to update the `signee_last_message` when the period or user changes.
        """
        for record in self:
            if 'in_time' in vals or 'out_time' in vals or 'user_id' in vals:
                in_time = vals.get('in_time', record.in_time)
                out_time = vals.get('out_time', record.out_time or fields.Datetime.now())
                user_id = vals.get('user_id', record.user_id.id)

                # Fetch the last message from the updated signee in this period
                messages = self.env['mail.message'].search([
                    ('res_id', '=', record.ticket_id.id),
                    ('model', '=', 'helpdesk.ticket'),
                    ('author_id', '=', self.env['res.users'].browse(user_id).partner_id.id),
                    ('date', '>=', in_time),
                    ('date', '<=', out_time)
                ], order='date desc', limit=1)

                if messages:
                    vals['signee_last_message'] = tools.html2plaintext(messages.body).strip()

        return super(HelpdeskTicketTeamHistory, self).write(vals)
