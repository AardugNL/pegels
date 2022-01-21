# -*- coding: utf-8 -*-
##############################################################################
#                                                                            #
# Part of Aardug. (Website: www.aardug.nl).                                  #
# See LICENSE file for full copyright and licensing details.                 #
#                                                                            #
##############################################################################

import base64

from odoo import http, _, fields 
from odoo.http import request
from datetime import datetime, timedelta
from odoo.addons.portal.controllers.portal import CustomerPortal

from odoo.exceptions import UserError

class CustomerPortal(CustomerPortal):

    @http.route(['/my/add_timesheet'], type='http', auth="user", website=True)
    def portal_add_timesheet(self, page=1, date_begin=None, date_end=None,
                             project=False, task=False, **kw):
        # if not (request.env.user.has_group('base.group_user') and request.env.user.has_group('hr_timesheet.group_hr_timesheet_user')):
        #     return request.render("odoo_mobile_timesheet.not_allowed")

        project_ids = request.env['project.project'].sudo().search([('is_close', '=', False)])
        task_ids = request.env['project.task'].sudo().search([('stage_id.is_close', '=', False)])
        work_type_ids = request.env['timesheet.work.type'].sudo().search([])
        duration = kw.get('duration', '00:00')
        start_time = kw.get('start_time', '00:00')
        end_time = kw.get('end_time', '00:00')

        # Overwrite method to pass current employee and employee list.
        employee_id = request.env['hr.employee'].sudo().search([]) 
        current_employee = request.env['hr.employee'].sudo().search([('user_id', '=', request.env.uid)])

        if project != 'False':
            project = int(project)

        if task != 'False':
            task =  int(task)

        values = {
            'project_ids': project_ids,
            'projects':project,
            'task_ids':task_ids,
            'tasks': task,
            'work_type_ids':work_type_ids,
            'portal_timesheet':True,
            'duration': duration,
            'start_time': start_time,
            'end_time': end_time,
            'employee_ids': employee_id,
            'current_employee' : current_employee,
        }
        if kw.get('timesheet_date'):
            values.update({'timesheet_date': kw.get('timesheet_date')})
        else:
            values.update({'timesheet_date': fields.Date.today()})
        return request.render("timesheet_writing.add_new_timesheet", values)


    @http.route(['/my/create_new_timesheet'], type='http', auth="user", website=True)
    def create_new_timesheet(self, **kwargs):
        # if not (request.env.user.has_group('base.group_user') and request.env.user.has_group('hr_timesheet.group_hr_timesheet_user')) or not kwargs:
        #     return request.render("odoo_mobile_timesheet.not_allowed")
        valse ={
            'user_id': request.env.user.id
        }
        # Over write this method to pass employee.
        if kwargs.get('employee_id'):
            valse.update({'employee_id': int(kwargs.get('employee_id'))})
        if kwargs.get('project_id'):
            valse.update({'project_id': int(kwargs.get('project_id'))})
        if kwargs.get('task_id'):
            valse.update({'task_id': int(kwargs.get('task_id'))})
        if kwargs.get('work_type'):
            valse.update({'work_type_id': int(kwargs.get('work_type'))})
        if kwargs.get('start_time'):
            start = datetime.strptime(str(kwargs.get('start_time')),'%H:%M') - datetime.strptime(str('0:0'),'%H:%M')
            start_time = start.total_seconds()/3600.00
            valse.update({'start_time': start_time})
        if kwargs.get('end_time'):
            end = datetime.strptime(str(kwargs.get('end_time')),'%H:%M') - datetime.strptime(str('0:0'),'%H:%M')
            end_time = end.total_seconds()/3600.00
            valse.update({'end_time': end_time})
        if kwargs.get('is_billable'):
            if kwargs.get('is_billable') == 'on':
                valse.update({'is_billable': True})
            else:
                valse.update({'is_billable': False})
        if kwargs.get('is_paid'):
            if kwargs.get('is_paid') == 'on':
                valse.update({'is_paid': True})
            else:
                valse.update({'is_paid': False})
        if kwargs.get('description'):
            valse.update({'name': kwargs.get('description')})
        if kwargs.get('quantity'):
            quantity_str = str(kwargs.get('quantity'))
            try:
                date_tt = datetime.strptime(quantity_str,'%H:%M') - datetime.strptime(str('0:0'),'%H:%M')
            except:
                return request.render("timesheet_writing.hour_usererror_msg")
            quantity = date_tt.total_seconds()/3600.00
            valse.update({'unit_amount': quantity})
        if kwargs.get('start_date'):
            date = datetime.strptime(kwargs.get('start_date'), "%Y-%m-%d")
            valse.update({'date': date.date()})
        if kwargs.get('long_description'):
            valse.update({'long_description': kwargs.get('long_description')})
        if kwargs.get('image_up'):
            valse.update({'image_up': base64.b64encode(kwargs.get('image_up').read()) if kwargs.get('image_up') else None})
        request.env['account.analytic.line'].sudo().create(valse)
        return request.redirect("/odoo_timesheet_portal_user_employee/select_timesheet?start_date="+str(kwargs.get('start_date')))