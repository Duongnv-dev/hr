from odoo import fields, models, api, _
from datetime import datetime


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'
    _description = 'inherit model payslip'

    def get_ot(self, contract_date_from, contract_date_to, employee_id):
        ots = self.env['hr.ot.line'].search([('state', '=', 'approved'), ('date', '>=', contract_date_from),
                                             ('date', '<=', contract_date_to), ('employee_id', '=', employee_id)])
        if not ots:
            return False
        ot_contract = self.calculate_ot(ots)
        return ot_contract

    def calculate_ot(self, ots):
        ot_contract = {'otn': 0, 'otw': 0, 'oth': 0}
        for ot in ots:
            if ot.type_day == 'normal':
                ot_contract['otn'] = ot_contract['otn'] + ot.ot_hour
            elif ot.type_day == 'weekend':
                ot_contract['otw'] = ot_contract['otw'] + ot.ot_hour
            else:
                ot_contract['oth'] = ot_contract['oth'] + ot.ot_hour
        return ot_contract

    def get_ot_nor_rate(self):
        ot_normal_rate = self.env['ir.config_parameter'].sudo().get_param('bnk_payroll_ot.ot_normal_rate')
        if float(ot_normal_rate) > 10:
            rate = float(ot_normal_rate) / 100
        else:
            rate = float(ot_normal_rate)
        return rate

    def get_ot_wek_rate(self):
        ot_week_rate = self.env['ir.config_parameter'].sudo().get_param('bnk_payroll_ot.ot_weekend_rate')
        if float(ot_week_rate) > 10:
            rate = float(ot_week_rate) / 100
        else:
            rate = float(ot_week_rate)
        return rate

    def get_ot_hol_rate(self):
        ot_holiday_rate = self.env['ir.config_parameter'].sudo().get_param('bnk_payroll_ot.ot_holiday_rate')
        if float(ot_holiday_rate) > 10:
            rate = float(ot_holiday_rate) / 100
        else:
            rate = float(ot_holiday_rate)
        return rate

