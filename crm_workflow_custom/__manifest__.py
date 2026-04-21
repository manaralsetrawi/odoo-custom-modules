{
    'name': 'CRM Workflow Custom',
    'version': '18.0.1.0.0',
    'summary': 'Custom CRM workflow, reminders, approvals, dashboards, and support integration',
    'category': 'Sales/CRM',
    'author': 'Your Name',
    'depends': [
        'crm',
        'crm_project_request_intake',
        'mail',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/crm_sequence_data.xml',
        'views/crm_stage_data.xml',
        'data/crm_stage_cleanup.xml',
        'views/crm_lead_views.xml',
        'views/crm_support_ticket_views.xml',
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