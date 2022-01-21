# -*- coding: utf-8 -*-
##############################################################################
#                                                                            #
# Part of Aardug. (Website: www.aardug.nl).                                  #
# See LICENSE file for full copyright and licensing details.                 #
#                                                                            #
##############################################################################

from odoo import api, models, fields, _
from odoo.exceptions import UserError


class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    product_cost = fields.Float('Cost')
    account_move_id = fields.Many2one('account.move', string='Journal Entries')
    make_accounting_entry = fields.Boolean(default=True, string='Make Accounting Entry')
    long_description = fields.Text(string="Long Description")
    image_up = fields.Binary('Image', attachment=True)

    def action_view_analytic_line_lond_desc(self):
        return {
            'name': _('Long Description'),
            'view_mode': 'form',
            'res_model': 'account.analytic.line',
            'view_id': self.env.ref('timesheet_writing.view_account_analytic_line_form_desc').id,
            'type': 'ir.actions.act_window',
            'res_id': self.id,
            'target': 'new',
        }

    def action_view_analytic_line_img(self):
        return {
            'name': _('Image'),
            'view_mode': 'form',
            'res_model': 'account.analytic.line',
            'view_id': self.env.ref('timesheet_writing.view_account_analytic_line_form_img').id,
            'type': 'ir.actions.act_window',
            'res_id': self.id,
            'target': 'new',
        }

    def _timesheet_postprocess_values(self, values):
        """ Get the addionnal values to write on record
            :param dict values: values for the model's fields, as a dictionary::
                {'field_name': field_value, ...}
            :return: a dictionary mapping each record id to its corresponding
                dictionnary values to write (may be empty).
        """
        result = {id_: {} for id_ in self.ids}
        sudo_self = self.sudo()  # this creates only one env for all operation that required sudo()
        # (re)compute the amount (depending on unit_amount, employee_id for the cost, and account_id for currency)
        if any([field_name in values for field_name in ['work_type_id', 'unit_amount', 'employee_id', 'account_id']]):
            for timesheet in sudo_self:
                if timesheet.work_type_id and timesheet.work_type_id.product_id:
                    prod_accounts = timesheet.work_type_id.product_id.product_tmpl_id._get_product_accounts()
                    unit = timesheet.work_type_id.product_id.uom_id
                    account = prod_accounts['expense']
                    cost = timesheet.work_type_id.product_id.price_compute('standard_price', uom=unit)[timesheet.work_type_id.product_id.id]
                    for project in timesheet.task_id.project_id.project_work_type_ids:
                        if project.work_type_id == timesheet.work_type_id:
                            if project.cost < 1:
                                project.cost = cost
                            cost = project.cost
                        else:
                            project.create({
                                'work_type_id': timesheet.work_type_id.id,
                                'cost': cost,
                                'project_id': timesheet.task_id.project_id.id
                            })
                    if not timesheet.task_id.project_id.project_work_type_ids:
                        timesheet.task_id.project_id.project_work_type_ids.create({
                            'work_type_id': timesheet.work_type_id.id,
                            'cost': cost,
                            'project_id': timesheet.task_id.project_id.id
                        })
                else:
                    cost = timesheet.employee_id.timesheet_cost or 0.0
                amount = -timesheet.unit_amount * cost
                amount_converted = timesheet.employee_id.currency_id._convert(
                    amount, timesheet.account_id.currency_id, self.env.company, timesheet.date)
                result[timesheet.id].update({
                    'amount': amount_converted,
                    'product_cost': amount_converted * (-1),
                    'product_id': timesheet.work_type_id.product_id.id
                })
        return result
