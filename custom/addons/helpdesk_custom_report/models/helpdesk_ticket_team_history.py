from odoo import api, fields, models

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

    # Actual duration spent in this team (computed from in_time->out_time)
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

    # Ticket type reference (if used)
    ticket_type_id = fields.Many2one(
        'helpdesk.ticket.type',
        string='Ticket Type'
    )

    # NEW FIELDS: SLA comparison
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
        help="User assigned to this ticket."
    )


    @api.depends('in_time', 'out_time')
    def _compute_dur(self):
        """Compute how many hours the ticket stayed in this team (in_time->out_time)."""
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
        if 'ticket_id' in vals:
            ticket = self.env['helpdesk.ticket'].browse(vals['ticket_id'])
            vals['user_id'] = ticket.user_id.id if ticket.user_id else None
        return super(HelpdeskTicketTeamHistory, self).create(vals)

    
class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    def write(self, vals):
        result = super(HelpdeskTicket, self).write(vals)
        
        if 'user_id' in vals:
            for ticket in self:
                last_history = self.env['helpdesk.ticket.team.history'].search(
                    [('ticket_id', '=', ticket.id), ('team_id', '=', ticket.team_id.id)],
                    order='in_time desc',
                    limit=1
                )
                
                if last_history:
                    last_history.write({
                        'user_id': vals['user_id']
                    })
                else:
                    self.env['helpdesk.ticket.team.history'].create({
                        'ticket_id': ticket.id,
                        'team_id': ticket.team_id.id,
                        'in_time': fields.Datetime.now(),
                        'user_id': vals['user_id']
                    })
                

        if 'ticket_type_id' in vals:
            for ticket in self:
                last_history = self.env['helpdesk.ticket.team.history'].search(
                    [('ticket_id', '=', ticket.id), ('team_id', '=', ticket.team_id.id)],
                    order='in_time desc',
                    limit=1
                )
                
                if last_history:
                    last_history.write({
                        'ticket_type_id': vals['ticket_type_id']
                    })
                else:
                    self.env['helpdesk.ticket.team.history'].create({
                        'ticket_id': ticket.id,
                        'team_id': ticket.team_id.id,
                        'in_time': fields.Datetime.now(),
                        'ticket_type_id': vals['ticket_type_id']
                    })
        
        return result
