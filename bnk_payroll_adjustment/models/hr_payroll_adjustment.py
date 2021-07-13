from odoo import api, models, fields, _
from datetime import datetime
from odoo.exceptions import ValidationError


class HrPayrollAdjustment(models.Model):
    _name = 'hr.payroll.adjustment'

    def _default_employee(self):
        name = 'new'
        if self.env.user.employee_ids:
            name = self.env.user.employee_ids[0].name
        return name

    def _default_period(self):
        m = datetime.today().month
        if m < 10:
            month = '0' + str(m)
        else:
            month = str(m)
        year = datetime.today().year
        period = self.env['hr.period'].check_or_create_period(month, year)
        return period

    name = fields.Char(compute='_compute_payslip_type', default=_default_employee)
    employee_id = fields.Many2one('hr.employee', required=True, string='Employee')
    type = fields.Selection([
        ('deduction', _('Deduction')),
        ('reimburse', _('Reimburse')),
        ('bonus', _('Bonus')),
    ], required=True, default='deduction')
    month_year = fields.Many2one('hr.period', default=_default_period, string='Month/Year')
    period_name = fields.Char(related='month_year.name')
    amount = fields.Float(string='Amount')
    notes = fields.Text()
    state = fields.Selection([
        ('draft', 'Draft'),
        ('wait_approved', 'Waiting For Approval'),
        ('approved', 'Approved'),
        ('cancel', 'Cancel'),
    ], default='draft')

    @api.depends('type', 'month_year', 'employee_id.name')
    def _compute_payslip_type(self):
        for rec in self:
            if rec.type == 'deduction':
                rec.name = ('Deduction of {} - {}').format(rec.employee_id.name, rec.period_name)
            elif rec.type == 'reimburse':
                rec.name = ('Reimburse of {} - {}').format(rec.employee_id.name, rec.period_name)
            elif rec.type == 'bonus':
                rec.name = ('Bonus of {} - {}').format(rec.employee_id.name, rec.period_name)

    @api.constrains('amount')
    def _constrains_amount(self):
        for rec in self:
            if rec.amount < 0:
                raise ValidationError(_('The amount must be greater than 0!!!'))

    def action_cancel(self):
        for rec in self:
            return rec.write({'state': 'cancel'})

    def action_wait_approved(self):
        for rec in self:
            return rec.write({'state': 'wait_approved'})

    def action_approved(self):
        for rec in self:
            return rec.write({'state': 'approved'})
