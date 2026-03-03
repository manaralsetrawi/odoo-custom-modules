{
    'name': 'HR Holidays Sequential Approval',
    'version': '1.0',
    'summary': 'Two-step approval for leave requests (Supervisor → HR)',
    'category': 'Human Resources',
    'author': 'Your Name',
    'depends': [
        'hr_holidays',   # Required for hr.leave
        'mail',          # Required for chatter & notifications
    ],
    'data': [
        'views/hr_leave_views.xml',

    ],
    'installable': True,
    'application': False,
}