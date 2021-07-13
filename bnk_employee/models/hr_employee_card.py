from odoo import fields, models, api, _
from datetime import datetime
from odoo.exceptions import ValidationError


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    join_date = fields.Date(copy=False, required=True, default=datetime.today().date(), track_visibility='onchange')

    @api.constrains('join_date', 'resigned_date')
    def check_date(self):
        for rec in self:
            if rec.resigned_date and rec.resigned_date <= rec.join_date:
                raise ValidationError(_("The resigned date must be than join date"))


