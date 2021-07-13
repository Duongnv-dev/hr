# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ot_normal_rate = fields.Float('Normal day rate')
    ot_weekend_rate = fields.Float('Weekend day rate')
    ot_holiday_rate = fields.Float('Holiday day rate')

    def get_values(self):
        res = super().get_values()
        config_param = self.env['ir.config_parameter']
        ot_normal_rate = config_param.sudo().get_param('bnk_payroll_ot.ot_normal_rate')
        ot_weekend_rate = config_param.sudo().get_param('bnk_payroll_ot.ot_weekend_rate')
        ot_holiday_rate = config_param.sudo().get_param('bnk_payroll_ot.ot_holiday_rate')
        try:
            normal = float(ot_normal_rate)
        except:
            normal = 0
        try:
            weekend = float(ot_weekend_rate)
        except:
            weekend = 0
        try:
            holiday = float(ot_holiday_rate)
        except:
            holiday = 0

        res.update({
            'ot_normal_rate': normal,
            'ot_weekend_rate': weekend,
            'ot_holiday_rate': holiday,
        })
        return res

    def set_values(self):
        super().set_values()
        set_param = self.env['ir.config_parameter'].sudo()

        ot_normal_rate = self.ot_normal_rate or 0
        ot_weekend_rate = self.ot_weekend_rate or 0
        ot_holiday_rate = self.ot_holiday_rate or 0

        set_param.set_param('bnk_payroll_ot.ot_normal_rate', ot_normal_rate)
        set_param.set_param('bnk_payroll_ot.ot_weekend_rate', ot_weekend_rate)
        set_param.set_param('bnk_payroll_ot.ot_holiday_rate', ot_holiday_rate)