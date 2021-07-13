# -*- coding: utf-8 -*-
import time
import datetime
from odoo import models, fields, api, tools, _
from odoo.exceptions import ValidationError


class PublicHolidayLine(models.Model):
    _name = 'public.holiday.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'description'

    date = fields.Date()
    description = fields.Char()
    public_holiday_id = fields.Many2one('public.holiday')
    state = fields.Selection(related='public_holiday_id.state')


class PublicHoliday(models.Model):
    _name = 'public.holiday'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char()
    year = fields.Char(default=datetime.date.today().strftime("%Y"))
    leave_types_id = fields.Many2one('hr.leave.type')
    state = fields.Selection([('draft', 'Draft'), ('approved', 'Approved'),
                              ('expired', 'Expired')], default="draft", track_visibility='onchange')
    public_holiday_line_ids = fields.One2many('public.holiday.line', 'public_holiday_id', "Holidays",
                                              track_visibility='onchange')
    # category_ids = fields.Many2one('hr.employee.category', string='Tags')

    @api.onchange('public_holiday_line_ids')
    def check_public_holiday_unique(self):
        current_list = []
        current_ids = self.public_holiday_line_ids
        if not current_ids:
            return
        for crr in current_ids:
            if crr.date == False:
                continue
            if crr.date.year != int(self.year):
                warning = {
                    'title': _('Warning!'),
                    'message': _('Invalid date {}'.format(crr.date)),
                }
                crr.date = False
                return {'warning': warning}
            if crr.date in current_list:
                warning = {
                    'title': _('Warning!'),
                    'message': _('Duplicate date {}'.format(crr.date)),
                }
                crr.date = False
                return {'warning': warning}
            current_list.append(crr.date)

    @api.multi
    def set_draft(self):
        self.write({'state': 'draft'})

    @api.multi
    def action_approve(self):
        self.ensure_one()
        check_ph = self.env['public.holiday'].search([('year', '=', self.year), ('state', '=', 'approved')])
        if len(check_ph) >= 1:
            raise ValidationError(_('Cannot Approve Public Holiday same year'))
        self.write({'state': 'approved'})

    def check_public_holiday_expired(self):
        current_today = datetime.date.today()
        current_year = current_today.year
        domain = [('state', '!=', 'expired'), ('year', '<', str(current_year))]
        public_holidays = self.search(domain)
        public_holidays.write({
            'state': 'expired'
        })
