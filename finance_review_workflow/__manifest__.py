{
    'name': 'Finance Review Workflow',
    'version': '18.0.1.0.0',
    'summary': 'Simple review workflow for invoices and vendor bills',
    'category': 'Accounting',
    'author': 'NCST',
    'license': 'LGPL-3',
    'depends': ['account'],
    'data': [
        'security/security.xml',
        'views/finance_review_account_move_views.xml',
    ],
    'installable': True,
    'application': False,
}