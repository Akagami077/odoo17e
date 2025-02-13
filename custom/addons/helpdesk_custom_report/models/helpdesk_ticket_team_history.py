from odoo import api, fields, models, tools
from datetime import datetime


class HelpdeskTicketTeamHistory(models.Model):
    _name = 'helpdesk.ticket.team.history'
    _description = 'Helpdesk Ticket Team History'
    _order = 'in_time desc'

    # Ticket ID stored as an integer (Only ID, No relation)
    ticket_id = fields.Integer(
        string='Ticket ID',
        required=True
    )

    # Ticket Title (Separated from ID)
    ticket_name = fields.Char(
        string='Ticket Title',
        compute='_compute_ticket_name',
        store=True
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

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        index=True
    )

    dur = fields.Float(
        string='Duration (Hours)',
        compute='_compute_dur',
        store=True
    )

    sla_id = fields.Many2one(
        'helpdesk.sla',
        string='SLA'
    )
    sla_time = fields.Float(
        string='SLA Time (Hours)',
        help="Number of hours set by the SLA for this Ticket Type / Team."
    )

    ticket_type_id = fields.Many2one(
        'helpdesk.ticket.type',
        string='Ticket Type'
    )

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

    user_id = fields.Many2one(
        'res.users',
        string='Assigned User',
        help="User assigned to this ticket during this period."
    )

    signee_last_message = fields.Text(
        string='Signee Last Message',
        help="The last message or comment left by the assigned user during this period."
    )

    partner_name = fields.Char(
        string='Customer Name',
        compute='_compute_partner_info',
        store=True
    )
    partner_phone = fields.Char(
        string='Phone',
        compute='_compute_partner_info',
        store=True
    )

    @api.depends('ticket_id')
    def _compute_partner_info(self):
        """
        Compute the Customer (partner) name and phone from the Helpdesk Ticket.
        """
        for record in self:
            ticket = self.env['helpdesk.ticket'].sudo().search([
                ('id', '=', record.ticket_id)
            ], limit=1)
            if ticket and ticket.partner_id:
                record.partner_name = ticket.partner_id.name or ''
                record.partner_phone = ticket.partner_id.phone or ''
            else:
                record.partner_name = ''
                record.partner_phone = ''

    @api.depends('ticket_id')
    def _compute_ticket_name(self):
        """Fetch the ticket's name based on ticket_id."""
        for record in self:
            ticket = self.env['helpdesk.ticket'].sudo().search([('id', '=', record.ticket_id)], limit=1)
            record.ticket_name = ticket.name if ticket else ''

    @api.depends('in_time', 'out_time')
    def _compute_dur(self):
        """Compute duration in hours (out_time - in_time)."""
        for record in self:
            if record.in_time and record.out_time:
                diff = record.out_time - record.in_time
                record.dur = diff.total_seconds() / 3600.0
            else:
                record.dur = 0.0

    @api.depends('dur', 'sla_time')
    def _compute_sla_exceed(self):
        """Check if the duration exceeded SLA time."""
        for record in self:
            if record.sla_time and record.dur > record.sla_time:
                record.sla_status = 'above'
                record.time_above_sla = record.dur - record.sla_time
            else:
                record.sla_status = 'within'
                record.time_above_sla = 0.0

    @api.model
    def create(self, vals):
        """Override create method to set company_id, user_id, and fetch last message."""
        ticket_id = vals.get('ticket_id')

        if ticket_id:
            ticket = self.env['helpdesk.ticket'].browse(ticket_id)
            vals['company_id'] = ticket.company_id.id if ticket.company_id else False
            vals['user_id'] = ticket.user_id.id if ticket.user_id else False

            in_time = vals.get('in_time', fields.Datetime.now())
            out_time = vals.get('out_time', fields.Datetime.now())

            messages = self.env['mail.message'].search([
                ('res_id', '=', ticket_id),
                ('model', '=', 'helpdesk.ticket'),
                ('author_id', '=', ticket.user_id.partner_id.id if ticket.user_id else False),
                ('message_type', '=', 'comment'),
                ('date', '>=', in_time),
                ('date', '<=', out_time)
            ], order='date desc', limit=1)

            if messages:
                vals['signee_last_message'] = tools.html2plaintext(messages.body).strip()

        return super(HelpdeskTicketTeamHistory, self).create(vals)


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    def write(self, vals):
        """Override write method to update history record."""
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

                if history_vals:
                    last_history.write(history_vals)

        return super(HelpdeskTicket, self).write(vals)
