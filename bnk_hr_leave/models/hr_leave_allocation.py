from odoo import fields, models, api


class HrLeaveAllocation(models.Model):
    _inherit = 'hr.leave.allocation'
    _description = 'Inherit leave allocation'

    contract_id = fields.Many2one('hr.contract')