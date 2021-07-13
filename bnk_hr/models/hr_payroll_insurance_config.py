# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    min_day_insurance = fields.Float('Min day insurance', default=14, help="Minimum day to calculate insurance in month")

    def get_values(self):
        res = super().get_values()
        config_param = self.env['ir.config_parameter']
        min_day_insurance = config_param.sudo().get_param('bnk_hr.min_day_insurance')
        res.update({
            'min_day_insurance': min_day_insurance,
        })
        return res

    def set_values(self):
        super().set_values()
        set_param = self.env['ir.config_parameter'].sudo()

        min_day_insurance = self.min_day_insurance or False

        set_param.set_param('bnk_hr.min_day_insurance', min_day_insurance)
