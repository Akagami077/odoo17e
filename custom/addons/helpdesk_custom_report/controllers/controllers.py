# -*- coding: utf-8 -*-
# from odoo import http


# class HelpdeskCustomReport(http.Controller):
#     @http.route('/helpdesk_custom_report/helpdesk_custom_report', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/helpdesk_custom_report/helpdesk_custom_report/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('helpdesk_custom_report.listing', {
#             'root': '/helpdesk_custom_report/helpdesk_custom_report',
#             'objects': http.request.env['helpdesk_custom_report.helpdesk_custom_report'].search([]),
#         })

#     @http.route('/helpdesk_custom_report/helpdesk_custom_report/objects/<model("helpdesk_custom_report.helpdesk_custom_report"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('helpdesk_custom_report.object', {
#             'object': obj
#         })

