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
        'security/ir.model.access.csv',
        'views/finance_review_account_move_views.xml',
        'views/finance_invoice_kanban_views.xml',
        'wizards/finance_wizard_views.xml',
        'report/finance_review_summary_report.xml',
        'report/finance_review_summary_template.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'finance_review_workflow/static/src/scss/finance_review_workflow.scss',
        ],
    },
    'installable': True,
    'application': False,
}