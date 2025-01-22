from odoo import api, fields, models

class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    ticket_type_id = fields.Many2one(
        'helpdesk.ticket.type',
        string='Ticket Type'
    )

    @api.model_create_multi
    def create(self, vals_list):
        """
        On ticket creation, if team_id is set, we create a history record.
        We also find the SLA and copy its 'time' field to 'sla_time'.
        """
        tickets = super().create(vals_list)
        for ticket, vals in zip(tickets, vals_list):
            team_id = vals.get('team_id')
            if team_id:
                # Find SLA
                sla_record = ticket._find_sla(team_id, ticket.ticket_type_id.id)
                sla_id = sla_record.id if sla_record else False
                sla_time = sla_record.time if sla_record else 0.0

                self.env['helpdesk.ticket.team.history'].create({
                    'ticket_id': ticket.id,
                    'team_id': team_id,
                    'in_time': fields.Datetime.now(),
                    'ticket_type_id': ticket.ticket_type_id.id,
                    'sla_id': sla_id,
                    'sla_time': sla_time,  # store the SLA time
                })
        return tickets

    def write(self, vals):
        """
        Overriding write to:
         - Close out_time on old team, create new record if team changes.
         - Copy SLA and SLA time to the new record.
         - If ticket closes, out_time is set.
        """
        for ticket in self:
            old_team_id = ticket.team_id.id

            # Find the last open line for the old team
            last_line = self.env['helpdesk.ticket.team.history'].search([
                ('ticket_id', '=', ticket.id),
                ('team_id', '=', old_team_id),
                ('out_time', '=', False),
            ], limit=1, order='in_time desc')

            result = super(HelpdeskTicket, ticket).write(vals)

            # 1) If the team changed
            new_team_id = ticket.team_id.id
            if 'team_id' in vals and new_team_id != old_team_id:
                if last_line:
                    last_line.out_time = fields.Datetime.now()

                # Find SLA
                sla_record = ticket._find_sla(new_team_id, ticket.ticket_type_id.id)
                sla_id = sla_record.id if sla_record else False
                sla_time = sla_record.time if sla_record else 0.0

                self.env['helpdesk.ticket.team.history'].create({
                    'ticket_id': ticket.id,
                    'team_id': new_team_id,
                    'in_time': fields.Datetime.now(),
                    'ticket_type_id': ticket.ticket_type_id.id,
                    'sla_id': sla_id,
                    'sla_time': sla_time,  # store the SLA time
                })

            # 2) If ticket is closed (stage folded or close_date), set out_time
            if 'stage_id' in vals and ticket.stage_id.fold:
                if last_line and not last_line.out_time:
                    last_line.out_time = fields.Datetime.now()

            if 'close_date' in vals and vals['close_date']:
                if last_line and not last_line.out_time:
                    last_line.out_time = fields.Datetime.now()

        return True

    def _find_sla(self, team_id, ticket_type_id):
        """
        Example: Finds an SLA that matches (team + ticket_type).
        'ticket_type_ids' is many2many, so we use 'in'.
        """
        domain = [('team_id', '=', team_id)]
        if ticket_type_id:
            domain.append(('ticket_type_ids', 'in', ticket_type_id))

        sla = self.env['helpdesk.sla'].search(domain, limit=1)
        return sla
