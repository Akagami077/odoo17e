from odoo import models, fields, api
from odoo.exceptions import UserError

class ResPartnerHelpdeskAnalysis(models.Model):
    _inherit = 'res.partner'

    username = fields.Char(string="Username")
    landmark = fields.Char(string="Landmark")
    mac_address = fields.Char(string="Mac Address")
    profile = fields.Char(string="Profile (Package)")
    owner = fields.Char(string="Owner")
    fdt = fields.Char(string="FDT")
    fat = fields.Char(string="FAT")
    expiration_date = fields.Date(string="Expiration Date")
    created_on_date = fields.Date(string="Created On Date")
    sas_contract_id = fields.Char(string="Contract ID")

    def update_partner_data_from_sas_radius(self):
        sas_radius = self.env['sas.radius.user']
        sas_radius_user = sas_radius.search([('partner', '=', self.id)], limit=1)
        if sas_radius_user:
            sas_radius_user.update_user_data()
        else:
            raise UserError("This partner isn't a SAS Radius user!")