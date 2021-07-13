from odoo import api, fields, models


class EmployeeSettingInherit(models.TransientModel):
    _inherit = 'res.config.settings'

    days = fields.Integer('Number of days before send email remind birthday:',
                          help="Number of days before employee birthday to send mail remind BUL")

    def set_values(self):
        res = super(EmployeeSettingInherit, self).set_values()
        self.env['ir.config_parameter'].set_param('bnk_employee.days', self.days)
        return res

    @api.model
    def get_values(self):
        res = super(EmployeeSettingInherit, self).get_values()
        config_param = self.env['ir.config_parameter']
        days = config_param.sudo().get_param('bnk_employee.days', default=2)
        res.update(days=int(days))
        return res

    def get_days(self):
        days = self.env['ir.config_parameter'].sudo().get_param('bnk_employee.days') or False
        return days
