# -*- coding: utf-8 -*-

import datetime
import logging
from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import AccessError, Warning

_logger = logging.getLogger(__name__)

_MAP_COLORS = {
  'oranje': 8,
  'red': 9,
  'green': 7,
  'purple': 6,
}

class CrmLead(models.Model):
    """ CRM Lead Case """
    _inherit = "crm.lead"

    remainder_mail = fields.Boolean(string='FollowUp Mail')
    warning_mail = fields.Boolean(string='Reminder Mail')
    custom_ids = fields.Many2many('crm.stage.custom', string='Performed Actions')

    @api.model
    def create(self, vals):
        existing_partner = [x.partner_id.id for x in self.message_follower_ids]
        res = super(CrmLead, self).create(vals)
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
                        message_partner_ids=[(4, self.partner_id.id)],
                        custom_ids=[(5, 0, 0)])
        return super(CrmLead,self).write(vals)

    @api.model
    def send_mail(self, custom):
        ''' send mail to opportunity customer based on crm stage configuration'''

        Mail = self.env['mail.mail']
        for rec in self:
            email_to =  rec.email_from
            template = self.env['mail.compose.message'].generate_email_for_composer(
                custom.template_id.id, rec.id)
            vals = {'auto_delete': False,
                    'email_to': email_to,
                    'subject': template.get('subject'),
                    'body_html': template.get('body')
                    }
            mail_id = Mail.create(vals)
            if not rec.partner_id:
                mail_id.mail_message_id.write({
                    'model':'crm.lead',
                    'body': mail_id.body_html,
                    'res_id' : rec.id,
                    'message_type' : 'comment',
                    'subtype_id': self.env['ir.model.data'].xmlid_to_res_id('mail.mt_comment'),
                    'record_name': rec.name,
                  })
            mail_id.send()
            rec.message_post(body=mail_id.body_html,
                              subject=mail_id.subject,
                              message_type='comment',
                              subtype='mail.mt_comment')
            mail_id.unlink()
        return True

    def compare_date(self, date, after_before, real_date):
        duration, unit = date.split('_')
        if(unit == "m"):
            return real_date + datetime.timedelta(minutes=int(duration))
        hours = int(duration) if unit == "h" else int(duration) * 24
        hours = hours * -1 if after_before == 'before' else hours * 1
        return real_date + datetime.timedelta(hours=hours)

    def _create_meeting(self, custAct, rec, dateDeadline):
        ''' create meeting based on configuration on crm stage'''

        if rec.user_id:
            user = rec.user_id
        else:
            user = custAct.user_id
        meeting = self.env['calendar.event'].create({
            'name': custAct.name +' - '+ rec.name,
            'opportunity_id': rec.id,
            'partner_ids': [[6, False, [user.partner_id.id]]],
            'user_id': user.id,
            'start': dateDeadline,
            'stop': dateDeadline + relativedelta(minutes=30),
            'state': 'open',
            'description': custAct.note,
        })

    def _do_custom_action(self, rec, stage, current_date):
        ''' create activity based on configuration in crm stage'''

        custAct = stage.custom_action_id
        custTime = int(custAct.time)
        if rec.user_id:
            userId = rec.user_id
        else:
            userId = custAct.user_id
        if userId:
            crmModel = self.env['ir.model'].search([('model', '=', 'crm.lead')],
                            limit=1)
            if custAct.period == 'day':
                dateDeadline = current_date + relativedelta(days=custTime)
            if custAct.period == 'month':
                dateDeadline = current_date + relativedelta(months=custTime)
            if custAct.period == 'year':
                dateDeadline = current_date + relativedelta(years=custTime)
            activity = self.env['mail.activity'].create({
                    'res_id': rec.id,
                    'res_model_id': crmModel.id,
                    'activity_type_id': custAct.next_activity_id.id,
                    'note': custAct.note,
                    'date_deadline': dateDeadline,
                    'user_id': userId.id,
                })
            if custAct.next_activity_id.category == 'meeting':
                self._create_meeting(custAct, rec, dateDeadline)
            rec.custom_ids = [(4, stage.id)]

    @api.model
    def email_send_stages(self):
        CrmStage = self.env['crm.stage']
        if not self.ids:
            CrmStageIds = CrmStage.search([('custom_ids','!=', False)])
            rec_ids = self.search([
                ('type','=','opportunity'),('stage_id', 'in', CrmStageIds.ids)])
            for rec in rec_ids:
                try:
                    value = getattr(rec, field.key) if hasattr(rec, field.key) else False
                    if value:
                        if field.field_id.ttype == 'datetime':
                            date = value
                            date_to_compare = self.compare_date(stage.action_time, when, date)
                            current_date = datetime.datetime.now()
                        else:
                            date = value
                            date_to_compare = self.compare_date(stage.action_time, when, date)
                            current_date = datetime.date.today()
                        if (date >= current_date >= date_to_compare and when == "before") or (
                            when == "after" and current_date >= date_to_compare):
                            if stage.mail_action == 'remainder':
                                rec.send_mail(stage)
                                rec.remainder_mail = True
                            if stage.mail_action == 'warning':
                                rec.send_mail(stage)
                                rec.warning_mail = True
                            if stage.custom_action_id and not stage in rec.custom_ids:
                                self._do_custom_action(rec, stage, current_date)
                except Exception as e:
                    _logger.error("Error in record <%s>, so skipped this record to fix mail issue ", rec.id)
                    continue

    def read(self, fields=None, load='_classic_read'):
        ''' Add color in crm kanban records based on crm stage configuration'''

        records = super(CrmLead, self).read(fields=fields, load=load)
        crm_stage = self.env['crm.stage']
        def compare_date(date, after_before, real_date):
            duration, unit = date.split('_')
            if(unit == "m"):
                return real_date + datetime.timedelta(minutes=int(duration))
            hours = int(duration) if unit == "h" else int(duration) * 24
            hours = hours * -1 if after_before == 'before' else hours * 1
            return real_date + datetime.timedelta(hours=hours)
        for rec in records:
            stage_id =  rec.get('stage_id')[0] if isinstance(rec.get('stage_id'), tuple) else rec.get('stage_id')
            crm_browse = crm_stage.browse(stage_id)
            if rec.get('color') in [6,7,8,9]:rec['color'] = 0
            for custom in crm_browse.custom_ids:
                when, field = custom.action_when, custom.action_perform
                value = rec.get(field.key)
                if value:
                    if field.field_id.ttype == 'datetime':
                        date = value
                        date_to_compare = compare_date(custom.action_time, when, date)
                        current_date = datetime.datetime.now()
                    else:
                        date = value
                        date_to_compare = compare_date(custom.action_time, when, date)
                        current_date = datetime.date.today()
                    if (date >= current_date >= date_to_compare and when == "before") or (when == "after" and current_date >= date_to_compare):
                        rec['color'] = _MAP_COLORS[custom.action_color]
        return records

class CrmStage(models.Model):
    """ CRM Lead Case """
    _inherit = "crm.stage"

    custom_ids = fields.One2many('crm.stage.custom', 'crm_stage_id', string='Kanban Custom')


class OpportunityActionConfig(models.Model):
    _name = 'opportunity.action.config'
    _description = "opportunity  config action"

    name = fields.Char(string='Name')
    next_activity_id = fields.Many2one('mail.activity.type', string='Next Activity')
    time = fields.Char(string='Time')
    period = fields.Selection([('day', 'Day'), ('month', 'Month'), ('year', 'Year')],
        string='Period')
    note = fields.Text(string='Note')
    user_id = fields.Many2one('res.users', string='User')

class CrmFieldConfiguration(models.Model):
    _name = 'crm.field.config'
    _description = "CRM Field Configuration"

    name = fields.Char(string='Field Label')
    key = fields.Char(string='Key')
    field_id = fields.Many2one('ir.model.fields', string='Field', domain=[
                ('model', '=', 'crm.lead'), ('ttype', 'in', ['date', 'datetime'])])

    @api.onchange('field_id')
    def onchange_field(self):
        self.name = self.field_id.field_description
        self.key = self.field_id.name


class CrmStageCustom(models.Model):
    _name = "crm.stage.custom"
    _order = 'priority desc'
    _rec_name = 'custom_action_id'
    _description = "CRM Stage Line"

    priority = fields.Integer(string='Priority', default=1, required=True)
    send_mail = fields.Boolean('Send mail')
    template_id = fields.Many2one('mail.template', string='Template')
    crm_stage_id = fields.Many2one('crm.stage', string='Stage')
    action_when = fields.Selection([
                                    ('before','Before'),
                                    ('after','After')],
                                     string='Before/After', required=True)
    custom_action_id = fields.Many2one('opportunity.action.config',
        string='Custom Action')
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
                                    ('7_d','7 Days'),
                                    ('10_d','10 Days'),
                                    ('20_d','20 Days'),
                                    ('30_d','30 Days'),
                                    ('180_d','180 Days'),
                                    ('365_d','365 Days'),],
                                    string='Time', required=True)
    action_color = fields.Selection([('oranje', 'Orange'),
                                    ('red','Red'),
                                    ('green','Green'),
                                    ('purple','Purple')],
                                    string='Colors', required=True)
    action_perform = fields.Many2one('crm.field.config', required=True, string='Action perform')

    @api.constrains('action_time', 'action_perform')
    def _check_action_time(self):
        for record in self:
            if (record.action_perform.field_id.ttype == 'date' and
                record.action_time in ['1_m','5_m','15_m','30_m','1_h','2_h','4_h','8_h']):
                raise Warning(_('Misconfiguration, check Field and Time.'))
