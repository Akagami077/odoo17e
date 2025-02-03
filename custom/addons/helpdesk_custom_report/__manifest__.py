{
    'name': 'TTem',
    'version': '17.0.1.0',
    'category': 'Helpdesk',
    'summary': 'Track how long tickets spend in each Helpdesk team.',
    'author': 'Your Company',
    'website': 'https://yourcompany.com',
    'license': 'LGPL-3',
    'depends': [
        'helpdesk',  # تأكد من وجود هذا الموديل
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/helpdesk_ticket_team_history_view.xml',
        'security/helpdesk_ticket_team_history_security.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': False,  # اجعل هذا الحقل True لظهور التطبيق في قائمة التطبيقات
}
