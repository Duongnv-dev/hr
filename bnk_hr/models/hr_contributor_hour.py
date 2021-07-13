# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import datetime
from calendar import monthrange
from odoo.exceptions import ValidationError


class HrContributorLine(models.Model):
    _name = 'hr.contributor.line'

    contributor_id = fields.Many2one('hr.contributor.hour')
    employee_id = fields.Many2one('hr.employee')
    hour_of_month = fields.Float('Hours')
    days = fields.Float()
    date_from = fields.Date(related='contributor_id.date_from')
    date_to = fields.Date(related='contributor_id.date_to')
    state = fields.Selection(related='contributor_id.state')

    @api.onchange('hour_of_month')
    def onchange_total(self):
        self = self.with_context(on_hour=True)
        if self.hour_of_month < 0:
            warning_mess = {
                'title': _('Days warning!'),
                'message': _('Days cannot less than 0!')
            }
            self.hour_of_month = 0
            return {'warning': warning_mess}

        if not self.env.context.get('on_day', False):
            self.days = self.hour_of_month / 8

    @api.onchange('days')
    def onchange_day_hour(self):
        self = self.with_context(on_day=True)
        if not self.env.context.get('on_hour', False):
            self.hour_of_month = self.days * 8


class HrContributorHour(models.Model):
    _name = 'hr.contributor.hour'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def default_month(self):
        mon = datetime.today().month
        if mon < 10:
            month = '0' + str(mon)
        else:
            month = str(mon)
        return month

    name = fields.Char()
    state = fields.Selection([('draft', 'Draft'), ('validated', 'Validated'), ('cancel', 'Cancel')], default='draft',
                             track_visibility="onchange")
    month = fields.Selection([('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'),
        ('05', 'May'), ('06', 'June'), ('07', 'July'), ('08', 'August'), ('09', 'September'),
        ('10', 'October'), ('11', 'November'), ('12', 'December')], default=default_month)
    year = fields.Char(default=str(datetime.today().year))
    date_from = fields.Date(compute='cp_date_from', store=True)
    date_to = fields.Date(compute='cp_date_to', store=True)
    contributor_ids = fields.One2many('hr.contributor.line', 'contributor_id')

    @api.depends('month', 'year')
    def cp_date_from(self):
        for s in self:
            if not s.month or not s.year:
                s.date_from = datetime.today()
            else:
                date_from = datetime.strftime(datetime.strptime('{}-{}-01'.format(s.year, s.month), '%Y-%m-%d'),
                                              '%Y-%m-%d')
                s.date_from = date_from

    @api.depends('month', 'year')
    def cp_date_to(self):
        for s in self:
            if not s.month or not s.year:
                s.date_to = datetime.today()
                s.name = 'Draft'
            else:
                date_to = datetime.strptime('{}-{}-{}'.format(s.year, s.month,
                                                              monthrange(int(s.year), int(s.month))[1]), '%Y-%m-%d')
                date_to_str = datetime.strftime(date_to, '%Y-%m-%d')
                s.date_to = date_to_str
                s.name = 'Hours of contributor {}/{}'.format(s.month, s.year)

    def set_cancel(self):
        self.write({'state': 'cancel'})

    def set_validate(self):
        for s in self:
            for line in s.contributor_ids:
                check_validate = s.env['hr.contributor.line'].search(
                    [('employee_id', '=', line.employee_id.id), ('date_from', '=', s.date_from),
                     ('date_to', '=', s.date_to), ('state', '=', 'validated')])
                if len(check_validate) >= 1:
                    raise ValidationError(_('Cannot validate contributor hours {}').format(line.employee_id.name))
        self.write({'state': 'validated'})

    @api.onchange('contributor_ids')
    def onchange_employee(self):
        if not self.contributor_ids:
            return
        employee_ids = []
        for con in self.contributor_ids:
            if not con.employee_id:
                continue
            if con.employee_id.id in employee_ids:
                con.employee_id = False
                return {'warning':
                    {
                        'title': _('Employee warning!'),
                        'message': _('Duplicate Employee!')
                    }
                }
            employee_ids.append(con.employee_id.id)


