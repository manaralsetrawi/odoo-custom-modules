{
    'name': 'HR Holidays Sequential Approval',
    'version': '18.0.1.0.0',
    'category': 'Human Resources',
    'depends': ['hr_holidays'],
    'author': 'Fatima Hasan',
    'description': 'Implements sequential approval workflow: Supervisor → HR',
    'data': [
        'views/hr_leave_views.xml',
    ],
    'installable': True,
}