{
    'name': 'Purchase Execution Workflow',
    'version': '1.0',
    'summary': 'Custom procurement execution flow for RFQ, receipt, and financial processing',
    'category': 'Purchase',
    'depends': ['purchase', 'stock', 'account', 'purchase_request'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/purchase_order_views.xml',
        'views/stock_picking_views.xml',
        'views/account_move_views.xml',
        'views/financial_reject_wizard_views.xml',
        'views/invoice_reject_wizard_views.xml',
        'views/procurement_execution_kanban_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'purchase_execution_workflow/static/src/scss/rfq_ui.scss',
        ],
    },
    'installable': True,
    'application': False,
}