# -*- coding: utf-8 -*-
##############################################################################
#
# Part of Aardug. (Website: www.aardug.nl).
# See LICENSE file for full copyright and licensing details.
#
##############################################################################

import datetime
import math
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, Warning
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

_MAP_issue_FIELDS = ['working_days_close']
_MAP_FIELDS_DATE = ['date_deadline']
_MAP_FIELDS_DATETIME = ['date_last_stage_update', 'create_date',
                        'write_date', 'date_assign','date_end']
_MAP_COLORS = {
    'orange': 8,
    'red': 9,
    'green': 7,
    'purple': 6,
    'yellow': 5,
    'blue': 4,
}

class ProjectTask(models.Model):
    """ Project Task """
    _inherit = "project.task"

    remainder_mail = fields.Boolean(string='FollowUp Mail')
    warning_mail = fields.Boolean(string='Reminder Mail')

    @api.model
    def create(self, vals):
        existing_partner = [x.partner_id.id for x in self.message_follower_ids]
        res = super(ProjectTask, self).create(vals)
        if vals.get('partner_id') and vals.get('partner_id') not in existing_partner:
            partner_id = self.env['res.partner'].browse(vals.get('partner_id'))
            res.message_subscribe(partner_id.ids)
        return res

    def write(self, vals):
        existing_partner = [x.partner_id.id for x in self.message_follower_ids]
        if vals.get('partner_id') and vals.get('partner_id') not in existing_partner:
            partner_id = self.env['res.partner'].browse(vals.get('partner_id'))
            self.message_subscribe(partner_id.ids)
        if 'stage_id' in vals:
            vals.update(remainder_mail=False,
                         warning_mail=False,
                         message_partner_ids=[(4, self.partner_id.id)])
        return super(ProjectTask,self).write(vals)

    def send_mail(self, custom):
        ''' send mail to task customer based on task stage configuration'''

        Mail = self.env['mail.mail']
        partnerObj = self.env['res.partner']
        for rec in self:
            template = self.env['mail.compose.message'].generate_email_for_composer(
                custom.template_id.id, rec.id)
            email_to = [partnerObj.browse(pId).email
                        for pId in template.get('partner_ids',[])
                        if partnerObj.browse(pId) and partnerObj.browse(pId).email]
            vals = {'auto_delete': False,
                    'email_to': ', '.join(email_to),
                    'res_id': rec.id,
                    'model': rec._name,
                    'subject': template.get('subject'),
                    'body_html': template.get('body')}
            mail_id = Mail.create(vals)
            for partner in rec.message_partner_ids:
                mail_noti = self.env['mail.notification'].sudo().create({
                                            'mail_message_id':mail_id.mail_message_id.id,
                                            'res_partner_id':partner.id,
                                            'notification_type':'email'})
            mail_id.mail_message_id.notified_partner_ids = [(6, 0, rec.message_partner_ids.ids)]
            if not rec.partner_id:
                mail_id.mail_message_id.write({
                    'model':'project.task',
                    'body': mail_id.body_html,
                    'res_id' : rec.id,
                    'message_type' : 'comment',
                    'subtype_id': self.env['ir.model.data'].xmlid_to_res_id(
                        'mail.mt_comment'),
                    'record_name': rec.name,
                })
            mail_id.send()
            rec.message_post(body=mail_id.body_html,
                             subject=mail_id.subject,
                             message_type='comment',
                             subtype='mail.mt_comment')
            # mail_id.unlink()
        return True

    def compare_date(self, date, after_before, real_date):
        duration, unit = date.split('_')
        if (unit == "m") and after_before == 'after':
            return real_date + datetime.timedelta(minutes=int(duration))
        elif (unit == "m") and after_before == 'before':
            return real_date - datetime.timedelta(minutes=int(duration))
        hours = int(duration) if unit == "h" else int(duration) * 24
        hours = hours * -1 if after_before == 'before' else hours * 1
        return real_date + datetime.timedelta(hours=hours)

    @api.model
    def email_send_stages(self):
        """ This cron job send mail to customer according configuration on project stage"""

        stage_custom_ids = self.env['project.task.type.custom'].search([
            ('send_mail','=',True),('custom_type_id','!=',False),
            ('action_perform_task','!=',False)])
        for stage in stage_custom_ids:
            if stage.mail_action == 'remainder':
                rec_ids = self.search([
                    ('stage_id', '=', stage.custom_type_id.id),
                    ('remainder_mail','=',False)],)
            else:
                rec_ids = self.search([
                    ('stage_id', '=', stage.custom_type_id.id),
                    ('warning_mail','=',False)],)
            when = stage.action_when
            field = stage.action_perform_task
            for rec in rec_ids:
                try:
                    value = getattr(rec, field) if hasattr(rec, field) else False
                    if value:
                        if field in _MAP_issue_FIELDS:
                            if int(math.floor(value)) == int(stage.action_time.split('_')[0]):
                                if  stage.mail_action=='remainder':
                                    rec.send_mail(stage)
                                    rec.remainder_mail = True
                                if stage.mail_action=='warning':
                                    rec.send_mail(stage)
                                    rec.warning_mail = True
                                continue
                            else:
                                continue
                        if field in _MAP_FIELDS_DATETIME:
                            date = datetime.datetime.strptime(value.strftime('%Y-%m-%d %H:%M:%S'), DEFAULT_SERVER_DATETIME_FORMAT)
                            date_to_compare = self.compare_date(stage.action_time, when, date)
                        elif field in _MAP_FIELDS_DATE:
                            date = datetime.datetime.strptime(value.strftime('%Y-%m-%d'), DEFAULT_SERVER_DATE_FORMAT)
                            date_to_compare = self.compare_date(stage.action_time, when, date)
                        current_date = datetime.datetime.now()
                        if (date >= current_date >= date_to_compare and when == "before") or (
                            when == "after" and current_date >= date_to_compare):
                            if stage.mail_action=='remainder':
                                rec.send_mail(stage) 
                                rec.remainder_mail = True
                            if stage.mail_action=='warning':
                                rec.send_mail(stage) 
                                rec.warning_mail = True
                except Exception as e:
                    _logger.error("Error in record <%s>, so skipped this record to fix mail issue ", rec.id)
                    continue

    def read(self, fields=None, load='_classic_read'):
        ''' Add color in task kanban records based on project stage configuration'''

        records = super(ProjectTask, self).read(fields=fields, load=load)
        ProjectTaskType = self.env['project.task.type']
        def compare_date(date, after_before, real_date):
            duration, unit = date.split('_')
            if (unit == "m") and after_before == 'after':
                return real_date + datetime.timedelta(minutes=int(duration))
            elif (unit == "m") and after_before == 'before':
                return real_date - datetime.timedelta(minutes=int(duration))
            hours = int(duration) if unit == "h" else int(duration) * 24
            hours = hours * -1 if after_before == 'before' else hours * 1
            return real_date + datetime.timedelta(hours=hours)
        for rec in records:
            stage_id =  rec.get('stage_id')[0] if isinstance(rec.get('stage_id'), tuple) else rec.get('stage_id')
            tasktype_browse = ProjectTaskType.browse(stage_id)
            # if rec.get('color') in [4,5,6,7,8,9]:rec['color'] = 0
            for custom in tasktype_browse.custom_ids:
                when, field = custom.action_when, custom.action_perform_task
                value = rec.get(field)
                if value:
                    if field in _MAP_issue_FIELDS:
                        if int(math.floor(value)) == int(custom.action_time.split('_')[0]):
                            rec['color'] = _MAP_COLORS[custom.action_color]
                            continue
                        else:
                            continue
                    if field in _MAP_FIELDS_DATETIME:
                        date = datetime.datetime.strptime(value.strftime('%Y-%m-%d %H:%M:%S'), DEFAULT_SERVER_DATETIME_FORMAT)
                        date_to_compare = self.compare_date(custom.action_time, when, date)
                    elif field in _MAP_FIELDS_DATE:
                        date = datetime.datetime.strptime(value.strftime('%Y-%m-%d'), DEFAULT_SERVER_DATE_FORMAT)
                        date_to_compare = self.compare_date(custom.action_time, when, date)
                    current_date=datetime.datetime.now()
                    if (date >= current_date >= date_to_compare and when == "before") or (when == "after" and current_date >= date_to_compare):
                        rec['color'] = _MAP_COLORS[custom.action_color]
        return records


class ProjectTaskType(models.Model):
    _inherit = "project.task.type"

    custom_ids = fields.One2many('project.task.type.custom', 'custom_type_id', string='Kanban Custom')

class ProjectTaskTypeCustom(models.Model):
    _name = "project.task.type.custom"
    _order = 'priority desc'
    _description = "Project Task Type Lines"

    priority = fields.Integer(string='Priority', default=1, required=True)
    send_mail = fields.Boolean('Send mail')
    template_id = fields.Many2one('mail.template', string='Template')
    custom_type_id = fields.Many2one('project.task.type', string='Stage', required=True)
    action_when = fields.Selection([
                                    ('before','Before'),
                                    ('after','After')],
                                    string='Before/After', required=True)
    mail_action = fields.Selection([
                                    ('remainder','FollowUp Mail'),
                                    ('warning','Reminder Mail')],
                                    string='Mail Action')
    action_time = fields.Selection([
                                    ('1_m','1 Minute'),
                                    ('5_m','5 Minutes'),
                                    ('15_m','15 Minutes'),
                                    ('30_m','30 Minutes'),
                                    ('1_h','1 Hour'),
                                    ('2_h','2 Hours'),
                                    ('4_h','4 Hours'),
                                    ('8_h','8 Hours'),
                                    ('1_d','1 Day'),
                                    ('2_d','2 Days'),
                                    ('3_d','3 Days'),
                                    ('4_d','4 Days'),
                                    ('5_d','5 Days'),
                                    ('6_d','6 Days'),
                                    ('7_d','7 Days'),
                                    ('10_d','10 Days'),
                                    ('20_d','20 Days'),
                                    ('30_d','30 Days'),
                                    ('180_d','180 Days'),
                                    ('365_d','365 Days'),],
                                    string='Time', required=True)
    action_color = fields.Selection([
                                    ('orange', 'Orange'),
                                    ('red','Red'),
                                    ('green','Green'),
                                    ('purple','Purple'),
                                    ('yellow','Yellow'),
                                    ('blue','Blue')],
                                    string='Colors', required=True)
    action_perform_task = fields.Selection([('create_date','Creation Date'),
                                       ('write_date','Update Date'),
                                       ('date_end','End Date'),
                                       ('date_deadline','Expected Closing'),
                                       ('working_days_close','Days to Close'),
                                       ('date_assign','Assigning Date'),
                                       ('date_last_stage_update','Last Stage Update'),
                                       ], string='Field')


    @api.constrains('action_time', 'action_perform_task')
    def _check_action_time(self):
        for record in self:
            if (record.action_perform_task in _MAP_FIELDS_DATE or record.action_perform_task in _MAP_issue_FIELDS) and record.action_time in ['1_m','5_m','15_m','30_m','1_h','2_h','4_h','8_h']:
                raise Warning(_('Misconfiguration, check Field and Time. Make sure time should be in days.'))
