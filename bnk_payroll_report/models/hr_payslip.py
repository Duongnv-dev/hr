from odoo import fields, models, api


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'
    _description = 'Inherit payslip'

    salary_gross = fields.Float(compute='cp_salary_gross', store=True)
    salary_net = fields.Float(compute='cp_salary_gross', store=True)
    insurances = fields.Float(compute='cp_salary_gross', store=True)

    @api.depends('line_ids')
    def cp_salary_gross(self):
        for pay in self:
            if not pay.line_ids:
                pay.salary_gross = 0
                pay.salary_net = 0
            else:
                for line in pay.line_ids:
                    if line.code == 'WAGB':
                        pay.salary_gross = line.total
                    elif line.code == 'TLB' or line.code == 'TLC':
                        pay.salary_net += line.total
                    elif line.code.startswith('BH'):
                        pay.insurances += line.total

