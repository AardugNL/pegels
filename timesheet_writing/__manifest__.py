# -*- coding: utf-8 -*-
##############################################################################
#                                                                            #
# Part of Aardug. (Website: www.aardug.nl).                                  #
# See LICENSE file for full copyright and licensing details.                 #
#                                                                            #
##############################################################################

{
    'name': 'Timesheet writing',
    'version': '13.0.1.1',
    'summary': '',
    'category': '',
    'description': """ timesheet writing
    """,
    'author': 'Aardug, Arjan Rosman',
    'website': 'http://www.aardug.nl/',
    'support': 'arosman@aardug.nl',
    'depends': ['odoo_mobile_timesheet', 'project', 'analytic', 'account', 'hr_timesheet', 'website' ,'portal'],
    'data': [
        'security/ir.model.access.csv',
        'views/analytic_account_views.xml',
        'views/project_task.xml',
        'views/access_assets.xml',
        'views/website_portal_templates.xml',
        'views/res_users_view.xml',
        'views/timesheet_work_type_view.xml',
        'views/project_view.xml'
    ],
    'installable': True,
    'application': True,
}
