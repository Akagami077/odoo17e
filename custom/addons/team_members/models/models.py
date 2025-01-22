# -*- coding: utf-8 -*-

from odoo import models, fields, api


class helpdesk_team(models.Model):
    _inherit = 'helpdesk.team'
    # member_ids = fields.Many2many('res.users', string='Team Members', domain=lambda self: [
    #     ('groups_id', 'in', [(self.env.ref('helpdesk.group_helpdesk_user').id), (self.env.ref('team_members.group_helpdesk_team_tickets').id)])],
    #                               default=lambda self: self.env.user, required=True)


    team_members = fields.Many2many('res.partner', string="Team Members")

