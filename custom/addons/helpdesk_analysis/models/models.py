# -*- coding: utf-8 -*-

from odoo import models, fields, api
class HelpdeskTicketSubType(models.Model):
    _name = 'helpdesk.ticket.subtype'

    name = fields.Char(string="Subtype Name", required=True)
    type = fields.Many2one('helpdesk.ticket.type', string="Type", required=True)


class HelpdeskTicketTypeInherited(models.Model):
    _inherit = 'helpdesk.ticket.type'

    subtype_ids = fields.One2many('helpdesk.ticket.subtype', 'type', string="Subtypes")

class HelpdeskTicketInherited(models.Model):
    _inherit = 'helpdesk.ticket'

    ticket_subtype_id = fields.Many2one('helpdesk.ticket.subtype', string="Subtype", domain="[('type', '=', ticket_type_id)]", required=True)
    customer_username = fields.Char(string="Username", compute="_compute_customer_info")
    customer_landmark = fields.Char(string="Landmark", compute="_compute_customer_info")
    customer_mac_address = fields.Char(string="Mac Address", compute="_compute_customer_info")
    customer_profile = fields.Char(string="Profile (Package)", compute="_compute_customer_info")
    customer_owner = fields.Char(string="Owner", compute="_compute_customer_info")
    customer_fdt = fields.Char(string="FDT", compute="_compute_customer_info")
    customer_latitude = fields.Float(string="Latitude", compute="_compute_customer_info")
    customer_longitude = fields.Float(string="Longitude", compute="_compute_customer_info")
    customer_fat = fields.Char(string="FAT", compute="_compute_customer_info")
    customer_expiration_date = fields.Date(string="Expiration Date", compute="_compute_customer_info")
    customer_created_on_date = fields.Date(string="Created On Date", compute="_compute_customer_info")
    customer_address = fields.Char(string="Customer Address", compute="_compute_customer_info")
    customer_contract_id = fields.Char(string="Customer Contract ID", compute="_compute_customer_info")

    # inherited fields
    tag_ids = fields.Many2many('helpdesk.tag', string='Tags', required=True)
    ticket_type_id = fields.Many2one('helpdesk.ticket.type', string="Type", tracking=True, required=True)

    @api.depends('partner_id')
    def _compute_customer_info(self):
        for record in self:
            record.customer_username = record.partner_id.username
            record.customer_landmark = record.partner_id.landmark
            record.customer_owner = record.partner_id.owner
            record.customer_fdt = record.partner_id.fdt
            record.customer_mac_address = record.partner_id.mac_address
            record.customer_profile = record.partner_id.profile
            record.customer_longitude = record.partner_id.partner_longitude
            record.customer_latitude = record.partner_id.partner_latitude
            record.customer_fat = record.partner_id.fat
            record.customer_expiration_date = record.partner_id.expiration_date
            record.customer_created_on_date = record.partner_id.created_on_date
            record.customer_address = record.partner_id.street2
            record.customer_contract_id = record.partner_id.sas_contract_id

    def btn_sync_sas_radius_users(self):
        """
        I linked this func with the "Update SAS Radius Users" button
        :return: reload the page
        """
        sas_radius_user_model = self.env['sas.radius.user']
        sas_radius_user_model.get_users_from_sas_radius_server()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',  # Reload the form view after syncing
        }