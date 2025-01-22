# -*- coding: utf-8 -*-
# from odoo import http


# class HelpdeskAnalysis(http.Controller):
#     @http.route('/helpdesk_analysis/helpdesk_analysis', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/helpdesk_analysis/helpdesk_analysis/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('helpdesk_analysis.listing', {
#             'root': '/helpdesk_analysis/helpdesk_analysis',
#             'objects': http.request.env['helpdesk_analysis.helpdesk_analysis'].search([]),
#         })

#     @http.route('/helpdesk_analysis/helpdesk_analysis/objects/<model("helpdesk_analysis.helpdesk_analysis"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('helpdesk_analysis.object', {
#             'object': obj
#         })

