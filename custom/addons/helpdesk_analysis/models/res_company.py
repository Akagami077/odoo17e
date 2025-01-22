from odoo import models, fields, api
from odoo.exceptions import UserError

class ResCompanyHelpdeskAnalysis(models.Model):
    _inherit = 'res.company'

    url = fields.Char('URL')
    username = fields.Char('Username')
    password = fields.Char('Password')