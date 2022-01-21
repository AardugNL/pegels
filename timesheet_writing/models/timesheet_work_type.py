# -*- coding: utf-8 -*-
##############################################################################
#                                                                            #
# Part of Aardug. (Website: www.aardug.nl).                                  #
# See LICENSE file for full copyright and licensing details.                 #
#                                                                            #
##############################################################################

from odoo import models, fields, api

class TimesheetWorkType(models.Model):
    _inherit = "timesheet.work.type"

    product_id = fields.Many2one('product.product', 'Product')


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    work_type_id = fields.Many2one('timesheet.work.type', string="Work Type")
