# -*- coding: utf-8 -*-
##############################################################################
#
# Part of Aardug. (Website: www.aardug.nl).
# See LICENSE file for full copyright and licensing details.
#
##############################################################################

{
    'name': 'Web Kanban Custom Help Desk',
    'description': """
    1) change helpdesk records color in kanban view based on helpdesk stage configuration.
    2) send mail to customer based on helpdesk kanban configuration.
    """,
    'version': '1.0',
    'category': 'Custom',
    'author': "Aardug, Arjan Rosman",
    'website': "http://www.aardug.nl/",
    'support': 'arosman@aardug.nl',
    'depends': ['helpdesk','hr'],
    'data': [
        'security/ir.model.access.csv',
        'data/helpdesk_action_rule_data.xml',
        'views/web_kanban_custom.xml',
        'views/helpdesk_view.xml',
        'views/helpdesk_template.xml',
    ],
    'application': False,
    'installable': True,
    'auto_install': False,
}
