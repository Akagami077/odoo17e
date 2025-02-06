from odoo import api, fields, models, tools


class HelpdeskTicketTeamHistory(models.Model):
    _name = 'helpdesk.ticket.team.history'
    _description = 'Helpdesk Ticket Team History'
    _order = 'in_time desc'

    # Required references
    ticket_id = fields.Integer(
        string='Ticket ID',
        required=True
    )
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

    @api.depends('ticket_id')
    def _compute_ticket_name(self):
        """Fetch the ticket's name for display."""
        for record in self:
            ticket = self.env['helpdesk.ticket'].sudo().search([('id', '=', record.ticket_id)], limit=1)
            record.ticket_name = ticket.name if ticket else ''

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
