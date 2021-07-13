from odoo import api, fields, models


class HrPayslipSummary(models.Model):
    _name = 'hr.payslip.summary'

    payslip_id = fields.Many2one('hr.payslip')
    number = fields.Char('No.')
    description = fields.Char()
    amount_payable = fields.Float()
    notes = fields.Char()
    is_title = fields.Boolean(default=False)
    is_line = fields.Boolean(default=False)
