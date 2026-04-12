{
    'name': 'NCST Budget Management',
    'version': '1.0',
    'summary': 'Custom budget allocation and control workflow',
    'author': 'Fatima Hasan - NCST',
    'description': """
NCST Budget Management
======================
Custom module for:
- General budget management
- Department budget allocation
- Budget reservation control
- Budget tracking and monitoring
""",
    'category': 'Accounting',
    'author': 'NCST',
    'website': '',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'hr',
        'account',
    ],
    'data': [
        'data/budget_sequence.xml',
        'data/budget_cron.xml',
        'security/budget_security.xml',
        'security/ir.model.access.csv',
        'views/general_budget_views.xml',
        'views/department_budget_views.xml',
        'views/budget_reservation_views.xml',
        'views/hr_department_budget_views.xml',
        'views/budget_department_reject_wizard_views.xml',
        'views/budget_menu.xml',
    ],
    'installable': True,
    'application': True,
}