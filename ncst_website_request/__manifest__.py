{
    'name': 'NCST Website Request',
    'version': '1.0',
    'summary': 'Website request form for NCST project inquiries',
    'category': 'Website',
    'author': 'NCST',
    'license': 'LGPL-3',
    'depends': [
        'website',
        'crm',
    ],
    'data': [
        'views/website_request_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'ncst_website_request/static/src/js/request_form.js',
        ],
    },
    'installable': True,
    'application': False,
}