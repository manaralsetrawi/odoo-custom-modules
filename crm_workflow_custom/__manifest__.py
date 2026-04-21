{
    'name': 'CRM Workflow Custom',
    'version': '18.0.1.0.0',
    'summary': 'Custom CRM workflow, reminders, approvals, dashboards, and reporting',
    'category': 'Sales/CRM',
    'author': 'Manar Alsetrawi',
    'depends': [
        'crm',
        'mail',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/crm_sequence_data.xml',
        'views/crm_stage_data.xml',
        'data/crm_stage_cleanup.xml',
        'views/crm_lead_views.xml',
        'views/crm_reporting_views.xml',
        'views/crm_menu_views.xml',
        'views/crm_kanban_views.xml',
        'views/crm_reject_wizard_views.xml',
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