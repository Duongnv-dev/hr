# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class CompanyBnK(models.Model):
    _inherit = 'res.company'

    description = fields.Text()
