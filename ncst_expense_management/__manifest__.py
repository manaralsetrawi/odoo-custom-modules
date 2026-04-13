{
    'name': 'NCST Expense Management',
    'version': '1.0',
    'summary': 'Custom expense request and reimbursement workflow',
    'author': 'Fatima - NCST',
    'category': 'Accounting',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'hr',
        'account',
        'ncst_budget_management',
    ],
    'data': [
        'security/expense_security.xml',
        'security/ir.model.access.csv',
        'views/expense_type_views.xml',
        'views/expense_request_views.xml',
        'views/expense_menu.xml',
    ],
    'installable': True,
    'application': True,
}