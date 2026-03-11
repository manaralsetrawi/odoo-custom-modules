{
    'name': 'Purchase Request Workflow',
    'version': '1.0',
    'summary': 'Custom purchase request and approval workflow',
    'category': 'Purchase',
    'author': 'Fatima Hasan - NCST',
    'license': 'LGPL-3',
    'depends': ['base', 'mail', 'hr', 'purchase'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'views/purchase_request_views.xml',
        'views/purchase_request_menus.xml',
    ],
    'installable': True,
    'application': True,
}