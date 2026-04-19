{
    'name': 'CRM Workflow Custom',
    'version': '18.0.1.0.0',
    'summary': 'Custom CRM workflow, reminders, approvals, dashboards, and support integration',
    'category': 'Sales/CRM',
    'author': 'Manar Alsetrawi - NCST',
    'depends': [ #update later get Fatima module name 
        'crm',
        'mail',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/crm_stage_data.xml',
        'views/crm_lead_views.xml',
        'views/crm_support_ticket_views.xml',
        'views/crm_menu_views.xml',
        'data/crm_reminder_cron.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'crm_workflow_custom/static/src/scss/crm_workflow.scss',
        ],
    },
    'installable': True,
    'application': False,
}