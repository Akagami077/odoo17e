from odoo import models, fields, api

class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    has_access = fields.Boolean('Has Access to edit?', compute='_compute_has_access')

    @api.depends('partner_id')
    def _compute_has_access(self):
        is_creator = (self.env.user == self.create_uid)
        is_creator_false = (self.create_uid.id == False)
        is_helpdesk_manager = self.env.user.has_group('helpdesk.group_helpdesk_manager')
        is_user_with_access = self.env.user.has_group('ticket_access.group_helpdesk_has_access')
        self.has_access = is_creator or is_helpdesk_manager or is_user_with_access or is_creator_false


    @api.onchange('team_id')
    def set_stage_to_new(self):
        if self.stage_id.id != 12:
            self.stage_id = 1
