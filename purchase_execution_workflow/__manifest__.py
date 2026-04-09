{
    'name': 'Purchase Execution Workflow',
    'version': '1.0',
    'summary': 'Custom procurement execution flow for RFQ, receipt, and financial processing',
    'category': 'Purchase',
    'depends': ['purchase', 'stock', 'account', 'purchase_request'],
    'data': [
        'security/security.xml',
        'views/purchase_order_views.xml',
        'views/stock_picking_views.xml',
        'views/account_move_views.xml',
    ],
    'installable': True,
    'application': False,
}