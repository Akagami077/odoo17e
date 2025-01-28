# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class contractor_restrict(models.Model):
#     _name = 'contractor_restrict.contractor_restrict'
#     _description = 'contractor_restrict.contractor_restrict'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100

from odoo import models, api, exceptions, _

class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    def write(self, vals):
        # Check if the stage is being changed
        if 'stage_id' in vals:
            # Check if the current user belongs to the contractor group
            if self.env.user.has_group('contractor_restrict.group_helpdesk_contractor'):
                raise exceptions.UserError(
                    _("You are not allowed to change the stage of the Helpdesk ticket.")
                )
        # Allow other updates
        return super(HelpdeskTicket, self).write(vals)
