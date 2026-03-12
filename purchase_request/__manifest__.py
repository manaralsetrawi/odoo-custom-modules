{
    'name': 'NCST Purchase Request',
    'version': '1.0',
    'summary': 'Purchase Request and Approval Workflow for NCST',
    'category': 'Purchase',
    'author': 'Fatima Hasan - NCST',
    'license': 'LGPL-3',
    'depends': ['base', 'mail', 'hr', 'purchase'],
    'data': [
            'security/ir.model.access.csv',
            'data/purchase_request_sequence.xml',
            'views/purchase_request_views.xml',
            'views/purchase_request_reject_wizard_views.xml',
            'views/purchase_request_menus.xml',
    ],
    'installable': True,
    'application': True,
}