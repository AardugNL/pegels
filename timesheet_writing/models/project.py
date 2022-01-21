# -*- coding: utf-8 -*-
##############################################################################
#                                                                            #
# Part of Aardug. (Website: www.aardug.nl).                                  #
# See LICENSE file for full copyright and licensing details.                 #
#                                                                            #
##############################################################################


from odoo import api, models, fields


class Project(models.Model):
    _inherit = 'project.project'

    total_project_cost = fields.Float(
        string='Cost', store=True,
        readonly=True, compute='_compute_total_project_cost')
    project_work_type_ids = fields.One2many(comodel_name='project.work.type', inverse_name='project_id', string="Work Type")

    @api.depends('task_ids.total_task_cost')
    def _compute_total_project_cost(self):
        for rec in self:
            rec.total_project_cost = sum(
                [line.total_task_cost for line in rec.task_ids])


class ProjectWorkType(models.Model):
	_name = 'project.work.type'
	_description = 'Project Work Type'
	_rec_name = 'work_type_id'

	work_type_id = fields.Many2one('timesheet.work.type', string='Work Type')
	cost = fields.Float('Cost')
	project_id = fields.Many2one('project.project', string='Project')
