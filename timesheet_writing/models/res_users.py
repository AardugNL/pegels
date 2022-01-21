# -*- coding: utf-8 -*-
##############################################################################
#                                                                            #
# Part of Aardug. (Website: www.aardug.nl).                                  #
# See LICENSE file for full copyright and licensing details.                 #
#                                                                            #
##############################################################################

from odoo import models, fields


class Project(models.Model):
    _inherit = 'res.users'

    is_show_employee = fields.Boolean(
        string='Show Employee on Time sheet',
    )
    show_timesheet = fields.Boolean(string='Allow to show timesheets', default=True)
