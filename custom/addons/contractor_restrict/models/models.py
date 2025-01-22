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

