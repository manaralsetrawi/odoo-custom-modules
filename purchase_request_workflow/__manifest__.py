{
    'name': 'Purchase Request Workflow',
    'version': '1.0',
    'summary': 'Custom purchase request and approval workflow',
    'category': 'Purchase',
    'author': 'Fatima Hasan - NCST',
    'license': 'LGPL-3',
    'depends': ['purchase', 'hr', 'mail'],
    'data': [
        'views/purchase_order_views.xml',
    ],
    'installable': True,
    'application': False,
}