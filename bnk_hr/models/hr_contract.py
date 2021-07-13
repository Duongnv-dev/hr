from odoo import api, fields, models, _


class HrContract(models.Model):
    _inherit = 'hr.contract'

    def default_struct(self):
        struct_id = self.env.ref('bnk_hr.hr_payroll_salary_structure_bnk')
        if not struct_id:
            return
        return struct_id[0].id


    struct_id = fields.Many2one('hr.payroll.structure', string='Salary Structure', default=default_struct)
