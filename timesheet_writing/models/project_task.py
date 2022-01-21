# -*- coding: utf-8 -*-
##############################################################################
#                                                                            #
# Part of Aardug. (Website: www.aardug.nl).                                  #
# See LICENSE file for full copyright and licensing details.                 #
#                                                                            #
##############################################################################


from odoo import api, models, fields


class Task(models.Model):
    _inherit = 'project.task'

    total_task_cost = fields.Float(
        string='Cost Total', store=True,
        readonly=True, compute='_compute_total_task_cost')

    @api.depends('timesheet_ids.product_cost')
    def _compute_total_task_cost(self):
        for rec in self:
            rec.total_task_cost = sum(
                [line.product_cost for line in rec.timesheet_ids])

    # point 4:
    def show_analytic_account_line(self):
        '''
        This function returns an action that display account analytic line record 
        of given project analytic. When only one found, show the rfq immediately.
        '''
        if self.project_id and self.project_id.analytic_account_id:
            action = self.env.ref('analytic.account_analytic_line_action')
            result = action.read()[0]
            result['context'] = {}
            accountLine = self.env['account.analytic.line'].search([('account_id', '=', self.project_id.analytic_account_id.id)]).ids
            if len(accountLine) > 1:
                result['domain'] = "[('id','in',%s)]" % (accountLine)
            elif len(accountLine) == 1:
                res = self.env.ref('analytic.view_account_analytic_line_form', False)
                result['views'] = [(res and res.id or False, 'form')]
                result['res_id'] = accountLine[0]
            return result
