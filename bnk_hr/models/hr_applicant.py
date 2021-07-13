# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT


class HrApplicantEvaluate(models.Model):
    _name = 'hr.applicant.evaluate'
    _description = 'Hr Applicant Evaluate'

    name = fields.Char()
    date = fields.Datetime(default=lambda *a: datetime.now(), readonly=True)
    note = fields.Text()
    hr_applicant_id = fields.Many2one('hr.applicant')
    user_id = fields.Many2one('res.users', string=_('By'), default=lambda self: self.env.user, readonly=True)


class BnKApplicant(models.Model):
    _inherit = 'hr.applicant'

    apply = fields.Boolean(default=False)
    years_experience = fields.Float(default=0.0)
    location_target_ids = fields.Many2many('res.country.state', 'location_country_state_rel', 'location_id', 'state_id')

    def create_schedule_activity_push_cv(self):
        interval = self.env.user.company_id.notify_push_cv_interval
        if interval:
            today = datetime.now()
            day_before = today + timedelta(days=-interval)
            day_before_str = datetime.strftime(day_before, DEFAULT_SERVER_DATETIME_FORMAT)
            domain = [('write_date', '<=', day_before_str), ('emp_id', '=', False)]
            cv_to_push = self.search(domain)
            if cv_to_push:
                for cv in cv_to_push:
                    vals = {
                        'res_id': cv.id,
                        'activity_type_id': self.env['mail.activity.type'].search([('name', '=', 'To Do')])[0].id or self.env['mail.activity.type'].search([])[0].id,
                        'summary': 'PushCV',
                        'note': 'This CV has been too long to be interested. Please review it',
                        'user_id': 2,
                        'res_model_id': self.env['ir.model'].search([('model', '=', self._name)]).id,
                    }
                    cv.env['mail.activity'].create(vals)
        return True


class WizardSuggestCV(models.TransientModel):
    _name = 'wizard.suggest.cv'

    skills = fields.Many2many('hr.applicant.category')
    years_experience_from = fields.Float(default=0, digits=(16, 1))
    years_experience_to = fields.Float(default=0, digits=(16, 1))
    location_target_ids = fields.Many2many('res.country.state', 'suggest_cv_location_country_state_rel', 'location_id',
                                           'state_id')
    hr_jod_id = fields.Many2one('hr.job', required=True)

    def suggest(self):
        domain = []
        if self.skills:
            domain.append(('categ_ids', 'in', self.skills._ids))
        if self.years_experience_from:
            domain.append(('years_experience', '>=', self.years_experience_from))
        if self.years_experience_to:
            domain.append(('years_experience', '<=', self.years_experience_to))
        if self.location_target_ids:
            domain.append(('location_target_ids', 'in', self.location_target_ids._ids))
        cv = self.env['hr.applicant'].search(domain)
        self.hr_jod_id.write({'cv_suggest_ids': [(6, 0, cv._ids)]})
        return True
