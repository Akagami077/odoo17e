# -*- coding: utf-8 -*-
{
    'name': 'Contractor Restrict',
    'version': '1.0',
    'summary': 'Restrict contractors to only view and manage tickets assigned to them',
    'description': """This module restricts contractors to only view and manage the helpdesk tickets assigned to them or created by them.""",
    'category': 'Helpdesk',
    'author': 'Your Name',
    'depends': ['helpdesk'],
    'data': [
        'security/helpdesk_security.xml',
        'security/ir.model.access.csv',
        'views/helpdesk_menu.xml',
        'views/helpdesk_views.xml',
    ],
    'installable': True,
    'application': False,
}
