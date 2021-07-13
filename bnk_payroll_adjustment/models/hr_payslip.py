from odoo import api, fields, models


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def get_salary_adjustment(self):
        adjs = self.check_salary_adjustment()
        if not adjs:
            return False
        result = self.process_salary_adjustment(adjs)
        return result

    def check_salary_adjustment(self):
        mon = self.date_from.month
        if self.date_from.month < 10:
            mon = '0{}'.format(self.date_from.month)
        period = self.env['hr.period'].check_or_create_period(mon, self.date_from.year)
        domain = [
            ('employee_id', '=', self.employee_id.id),
            ('state', '=', 'approved'),
            ('month_year', '=', period)
        ]
        adjustments = self.env['hr.payroll.adjustment'].search(domain)
        return adjustments

    def process_salary_adjustment(self, adjs):
        deduction = sum(adjs.filtered(lambda d: d.type == 'deduction').mapped('amount'))
        reimburse = sum(adjs.filtered(lambda d: d.type == 'reimburse').mapped('amount'))
        bonus = sum(adjs.filtered(lambda d: d.type == 'bonus').mapped('amount'))
        return {'deduction': deduction, 'reimburse': reimburse, 'bonus': bonus}

    def set_salary_adjustment(self, adj):
        self.deduction = adj['deduction']
        self.reimburse = adj['reimburse']
        self.mon_bonus = adj['bonus']
        return True
