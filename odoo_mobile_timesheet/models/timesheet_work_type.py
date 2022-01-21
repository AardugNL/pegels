# -*- coding: utf-8 -*-

from odoo import models, fields, api

class TimesheetWorkType(models.Model):
    _name = "timesheet.work.type"
    _description = "Timesheet Work Type"

    _sql_constraints = [
        ('code', 'UNIQUE(code)', 'The Code must be unique !')
    ]
    code = fields.Char(
        required=True,
        string="Code",
    )
    name = fields.Char(
        required=True,
        string="Name",
    )
