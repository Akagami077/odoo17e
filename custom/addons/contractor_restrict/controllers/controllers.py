# -*- coding: utf-8 -*-
# from odoo import http


# class ContractorRestrict(http.Controller):
#     @http.route('/contractor_restrict/contractor_restrict', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/contractor_restrict/contractor_restrict/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('contractor_restrict.listing', {
#             'root': '/contractor_restrict/contractor_restrict',
#             'objects': http.request.env['contractor_restrict.contractor_restrict'].search([]),
#         })

#     @http.route('/contractor_restrict/contractor_restrict/objects/<model("contractor_restrict.contractor_restrict"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('contractor_restrict.object', {
#             'object': obj
#         })

