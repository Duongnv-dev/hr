# Copyright 2017 Eficent Business and IT Consulting Services S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    notify_push_cv_interval = fields.Integer(default=0, string="Interval notify push CV",
                                             help="Interval prompting CV care")


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    notify_push_cv_interval = fields.Integer(
        related='company_id.notify_push_cv_interval', readonly=False,
        string="Interval notify push CV",
        help="Interval prompting CV care")
