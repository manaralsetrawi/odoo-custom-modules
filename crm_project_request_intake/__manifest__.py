
{
    'name': 'CRM Project Request Intake',
    'version': '1.0',
    'summary': 'Website project request form and CRM lead intake workflow',
    'description': """
CRM Project Request Intake
==========================
This module adds a website-based project request intake flow.

Main features:
- Extend Contact Us form with message type
- Show extra fields for project requests
- Create CRM lead from website submission
- Allow project manager to approve or reject request
- Allow approved lead to be converted into opportunity
""",
    'author': 'Fatima Hasan - NCST',
    'category': 'Sales/CRM',
    'license': 'LGPL-3',
    'depends': [
        'crm',
        'website',
        'mail',
        'crm_workflow_custom',
    ],
    'data': [
        'security/crm_project_request_security.xml',
        'security/ir.model.access.csv',
        'data/crm_stage_data.xml',
        'views/crm_lead_views.xml',
        'views/project_request_page.xml',
        'views/crm_project_request_menu.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'crm_project_request_intake/static/src/js/project_request_form.js',
            'crm_project_request_intake/static/src/scss/project_request_form.scss',
        ],
    },
    'installable': True,
    'application': False,
}