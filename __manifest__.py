# custom_project_addon/__manifest__.py
{
    'name': 'ik45',
    'version': '1.0',
    'category': 'Project',
    'summary': 'Lock/unlock tasks by milestone, propagate date changes, send notifications',
    'author': 'Your Name',
    'depends': [
        'project',
        'mail',
    ],
    'data': [
        'data/mail_template_data.xml',
        'data/sendmail_dateextend.xml',
    ],

    'installable': True,
    'application': False,
}
