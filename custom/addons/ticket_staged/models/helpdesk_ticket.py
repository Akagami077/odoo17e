from odoo import models, fields, api

class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    @api.onchange('stage_id')
    def set_team_to_customer_care_on_solved(self):
        # الصباح
        if self.company_id.id == 1:
            current_team_id = 6 #operation
            next_team_id = 1 #customer care
            stage_id = 12
        # نخبة العراق
        elif self.company_id.id == 3:
            current_team_id = 21 #operation
            next_team_id = 3 #customer care
            stage_id = 18
        else:
            current_team_id = 0
            next_team_id = 0
            stage_id = 0

        if self.team_id.id == current_team_id:
            if self.stage_id and self.stage_id.id == stage_id:
                self.team_id = next_team_id

    @api.onchange('stage_id')
    def set_team_to_operations_on_solved(self):
        # الصباح
        if self.company_id.id == 1:
            current_team_id = 5  # contractor
            next_team_id = 6  # opertaion
            current_stage_id = 12
            next_stage_id = 14
        # نخبة العراق
        elif self.company_id.id == 3:
            current_team_id = 24 # contractor
            next_team_id = 21  # operation
            current_stage_id = 20
            next_stage_id = 19
        else:
            current_team_id = 0
            next_team_id = 0
            current_stage_id = 0
            next_stage_id = 0

        if self.team_id.id == current_team_id:
            if self.stage_id and self.stage_id.id == current_stage_id:
                self.team_id = next_team_id
                self.stage_id = next_stage_id

