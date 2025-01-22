# -*- coding: utf-8 -*-
{
    'name': "helpdesk_analysis",

    'summary': "Helpdesk Analysis addon that add some fields to helpdesk",

    'description': """
        Change Helpdesk addon to have more features for analysis purposes
    """,

    'author': "Digizilla",
    'website': "https://digizilla.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'contacts', 'base_geolocalize', 'helpdesk'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/helpdesk_ticket_subtype.xml',
        'views/res_partner.xml',
        'views/res_company.xml',
        'data/cron.xml',
        'views/partner_sas_user_views.xml',  # your new XML
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}

