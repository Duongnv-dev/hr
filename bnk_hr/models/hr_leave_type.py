# -*- coding:utf-8 -*-
from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError


class HrLeaveTypeExtend(models.Model):
    _inherit = 'hr.leave.type'

    code = fields.Selection([('legal', 'Legal'), ('annual', 'Public'),  ('sick', 'Sick'), ('unpaid', 'Unpaid')],
                            default='legal')


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    def action_approve(self):
        check_resign = self.check_resign_employee()
        if check_resign:
            raise ValidationError(_('Cannot approve! Resign date in period leave or leave over resign date.'))
        check_legal = self.check_legal_trial_employee()
        if check_legal:
            raise ValidationError(_('Cannot approve! Request legal leave in trial contract period.'))
        return super(HrLeave, self).action_approve()

    def check_resign_employee(self):
        if not self.employee_id.resigned_date:
            return False
        if self.request_date_to > self.employee_id.resigned_date:
            return True

    def check_legal_trial_employee(self):
        if self.holiday_status_id.code.lower() != 'legal':
            return False
        contract_trials = self.employee_id.contract_ids.filtered(lambda c: c.type_id.code == 'trial')
        if not contract_trials:
            return False
        for c in contract_trials:
            if self.request_date_to <= c.date_end:
                return True
        return False
