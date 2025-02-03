# -*- coding: utf-8 -*-
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
        عند إنشاء تذكرة جديدة، إذا كان `team_id` محددًا، نقوم بإنشاء سجل في الهيستوري.
        أيضًا، نقوم بجلب `sla_time` من الـ SLA المرتبط.
        """
        tickets = super().create(vals_list)
        for ticket, vals in zip(tickets, vals_list):
            team_id = vals.get('team_id')
            if team_id:
                # البحث عن SLA المناسب
                sla_record = ticket._find_sla(team_id, ticket.ticket_type_id.id)
                sla_id = sla_record.id if sla_record else False
                sla_time = sla_record.time if sla_record else 0.0

                self.env['helpdesk.ticket.team.history'].create({
                    'ticket_id': ticket.id,
                    'team_id': team_id,
                    'in_time': fields.Datetime.now(),
                    'ticket_type_id': ticket.ticket_type_id.id,
                    'sla_id': sla_id,
                    'sla_time': sla_time,  # تخزين قيمة SLA Time
                    # We rely on the create override in the history model to set company_id
                })
        return tickets

    def write(self, vals):
        """
        عند تحديث تذكرة:
        - إذا تغير `team_id`، يتم إغلاق السجل السابق وإنشاء سجل جديد.
        - إذا تغير `sla_time` أو `time`، يتم تحديثه فقط في آخر سجل في الهيستوري لنفس `ticket_id` و`team_id`.
        - إذا تم إغلاق التذكرة، يتم تحديث `out_time`.
        """
        for ticket in self:
            old_team_id = ticket.team_id.id

            last_line = self.env['helpdesk.ticket.team.history'].search([
                ('ticket_id', '=', ticket.id),
                ('team_id', '=', old_team_id),
            ], order='in_time desc', limit=1)

            result = super(HelpdeskTicket, ticket).write(vals)

            # Update SLA time in the last history if sla_time changed
            if 'sla_time' in vals and last_line:
                last_line.write({'sla_time': vals['sla_time']})

            # If the 'time' field changed, recalc the SLA time
            if 'time' in vals:
                sla_record = ticket._find_sla(ticket.team_id.id, ticket.ticket_type_id.id)
                if sla_record and last_line:
                    last_line.write({'sla_time': sla_record.time})

            # If team changed, close the old line and create a new one
            new_team_id = ticket.team_id.id
            if 'team_id' in vals and new_team_id != old_team_id:
                if last_line:
                    last_line.out_time = fields.Datetime.now()

                sla_record = ticket._find_sla(new_team_id, ticket.ticket_type_id.id)
                sla_id = sla_record.id if sla_record else False
                sla_time = sla_record.time if sla_record else 0.0

                self.env['helpdesk.ticket.team.history'].create({
                    'ticket_id': ticket.id,
                    'team_id': new_team_id,
                    'in_time': fields.Datetime.now(),
                    'ticket_type_id': ticket.ticket_type_id.id,
                    'sla_id': sla_id,
                    'sla_time': sla_time,
                })

            # If stage changed to a folded stage => close out_time
            if 'stage_id' in vals and ticket.stage_id.fold:
                if last_line and not last_line.out_time:
                    last_line.out_time = fields.Datetime.now()

            # If ticket has a close_date => close out_time
            if 'close_date' in vals and vals['close_date']:
                if last_line and not last_line.out_time:
                    last_line.out_time = fields.Datetime.now()

        return result

    def _find_sla(self, team_id, ticket_type_id):
        """
        البحث عن SLA المناسب بناءً على `team_id` و `ticket_type_id`.
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
