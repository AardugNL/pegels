# -*- coding: utf-8 -*-
##############################################################################
#
# Part of Aardug. (Website: www.aardug.nl).
# See LICENSE file for full copyright and licensing details.
#
##############################################################################

{
    'name': 'Web Kanban Custom Project',
    'category': 'Project',
    'description': """
    1) change task records color in kanban view based on project stage configuration.
    2) send mail to customer based on project kanban configuration.
        """,
    'version': '1.0',
    'depends': ['project'],
    'author': "Aardug, Arjan Rosman",
    'website': "http://www.aardug.nl/",
    'support': 'arosman@aardug.nl',
    'data': [
        'views/web_kanban_custom.xml',
        'views/project_view.xml',
        'data/project_action_rule_data.xml',
        'data/project_action_rule_data_user.xml',
        'security/ir.model.access.csv'
    ],
    'auto_install': False,
    'installable': True,
}
