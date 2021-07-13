# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import datetime
from calendar import monthrange
from odoo.exceptions import ValidationError


class HrAllowanceLine(models.Model):
    _name = 'hr.allowance.line'

    allowance_id = fields.Many2one('hr.allowance')
    employee_id = fields.Many2one('hr.employee')
    day_of_allowance = fields.Float('Days')
    value_per_day = fields.Float('Allowance per day')
    total = fields.Float()
    date_from = fields.Date(related='allowance_id.date_from')
    date_to = fields.Date(related='allowance_id.date_to')
    state = fields.Selection(related='allowance_id.state')

    @api.onchange('day_of_allowance', 'value_per_day')
    def onchange_total(self):
        total = self.day_of_allowance * self.value_per_day
        if self.day_of_allowance < 0:
            warning_mess = {
                'title': _('Days warning!'),
                'message': _('Days cannot less than 0!')
            }
            self.day_of_allowance = 0
            return {'warning': warning_mess}

        if self.value_per_day < 0:
            warning_mess = {
                'title': _('Allowance warning!'),
                'message': _('Allowance cannot less than 0!')
            }
            self.value_per_day = 0
            return {'warning': warning_mess}
        self.total = total


class HrAllowance(models.Model):
    _name = 'hr.allowance'

    def default_month(self):
        mon = datetime.today().month
        if mon < 10:
            month = '0' + str(mon)
        else:
            month = str(mon)
        return month

    name = fields.Char()
    state = fields.Selection([('draft', 'Draft'), ('validated', 'Validated'), ('cancel', 'Cancel')], default='draft')
    month = fields.Selection([('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'),
        ('05', 'May'), ('06', 'June'), ('07', 'July'), ('08', 'August'), ('09', 'September'),
        ('10', 'October'), ('11', 'November'), ('12', 'December')], default=default_month)
    year = fields.Char(default=str(datetime.today().year))
    date_from = fields.Date(compute='cp_date_from', store=True)
    date_to = fields.Date(compute='cp_date_to', store=True)
    allowance_ids = fields.One2many('hr.allowance.line', 'allowance_id')

    @api.depends('month', 'year')
    def cp_date_from(self):
        for s in self:
            if not s.month or not s.year:
                s.date_from = datetime.today()
            else:
                date_from = datetime.strftime(datetime.strptime('{}-{}-01'.format(s.year, s.month), '%Y-%m-%d'), '%Y-%m-%d')
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
                date_to_str = datetime.strftime(date_to,  '%Y-%m-%d')
                s.date_to = date_to_str
                s.name = 'Allowance {}/{}'.format(s.month, s.year)

    def set_cancel(self):
        self.write({'state': 'cancel'})

    def set_validate(self):
        for s in self:
            if not s.allowance_ids:
                continue
            for line in s.allowance_ids:
                check = s.env['hr.allowance.line'].search([('date_from', '=', s.date_from),
                                                            ('date_to', '=', s.date_to), ('state', '=', 'validated'),
                                                            ('employee_id', '=', line.employee_id.id)])
                if len(check) >= 1:
                    raise ValidationError(_('Cannot validate for "{}"').format(line.employee_id.name))
        self.write({'state': 'validated'})

    @api.onchange('allowance_ids')
    def onchange_employee(self):
        if not self.allowance_ids:
            return
        employee_ids = []
        for alw in self.allowance_ids:
            if not alw.employee_id:
                continue
            if alw.employee_id.id in employee_ids:
                alw.employee_id = False
                return {'warning':
                    {
                        'title': _('Employee warning!'),
                        'message': _('Duplicate Employee!')
                    }
                }
            employee_ids.append(alw.employee_id.id)

