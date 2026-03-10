{
    'name': 'Backend Theme Custom',
    'version': '1.0',
    'depends': ['web'],
    'assets': {
       'web.assets_backend': [
        ('before', 'web/static/src/scss/primary_variables.scss', 'backend_theme/static/src/scss/backend_theme.scss'),
        ],
    },
    'installable': True,
}