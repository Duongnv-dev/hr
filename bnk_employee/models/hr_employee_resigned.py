from odoo import models, api, fields, _
from datetime import datetime
from odoo.exceptions import ValidationError


class HrEmployeeInherit(models.Model):
    _inherit = 'hr.employee'

    is_resign = fields.Boolean(string=_('Is Resign'), default=False)
    resigned_date = fields.Date(string=_('Resignation Date'), track_visibility='onchange')
    state = fields.Selection([
        ('wait_approved', _('Waiting For Approval')),
        ('approved', _('Approve'))
    ], default='approved')
    is_trial_15 = fields.Boolean(default=False)

    def action_approve(self):
        resign_date = self.resigned_date
        is_resign = self.is_resign
        if not self.contract_id:
            raise ValidationError(_('Employee have not contract.'))
        if self.contract_id.state == 'cancel':
            raise ValidationError(_('Contract is already cancel.'))
        self.contract_id.state = 'close'
        self.contract_id.date_end = resign_date
        check_leave = self.check_leave_constrains_resign()
        if check_leave:
            raise ValidationError(_('Resign date in leave period. Please change leave before approve resign.'))
        self.check_trial_under_15_day()
        self.write({'state': 'approved'})
        return True

    def check_leave_constrains_resign(self):
        leaves = self.env['hr.leave'].search([
            ('employee_id', '=', self.id),
            ('state', '=', 'validate'),
            ('request_date_to', '>', datetime.strftime(self.resigned_date, '%Y-%m-%d')),
            ('request_date_from', '<=', datetime.strftime(self.resigned_date, '%Y-%m-%d')),
        ])
        if leaves:
            return True
        return False

    def check_trial_under_15_day(self):
        if not self.contract_id:
            return False
        if self.contract_type != 'trial':
            return False
        if not self.resigned_date:
            return False

        workdays = self.get_worked_day()
        if workdays < 15:
            self.is_trial_15 = True
        return True

    def get_worked_day(self):
        workdays = self.env['hr.payslip'].get_worked_day_lines(self.contract_id, self.contract_id.date_start,
                                                               self.contract_id.date_end)
        total = sum([day['number_of_days'] for day in workdays])
        return total

    @api.onchange('is_resign')
    def _onchange_is_resign(self):
        if self.is_resign:
            self.resigned_date = datetime.today().date()
            self.state = 'wait_approved'
        else:
            self.resigned_date = False
            self.state = 'approved'

    @api.onchange('resigned_date')
    def onchange_resign_date(self):
        if not self.resigned_date:
            return
        self.state = 'wait_approved'
