from odoo import fields, models, _, api


class HrDepartmentInherit(models.Model):
    _inherit = 'hr.department'

    manager_ids = fields.Many2many('res.users', 'depart_user_rel', compute='_compute_manager_ids', store=1)
    employee_remind_extend = fields.Many2many('hr.employee')

    def get_all_manager_depart_parent(self, managers=[]):
        self.ensure_one()
        user_id = self.manager_id.user_id.id
        if user_id and user_id not in managers:
            managers.append(user_id)
        if self.parent_id:
            self.parent_id.get_all_manager_depart_parent(managers=managers)
        return self.env['res.users'].sudo().browse(managers) or None

    @api.depends('manager_id', 'manager_id.user_id', 'parent_id.manager_ids')
    def _compute_manager_ids(self):
        for rec in self:
            rec.manager_ids = rec.get_all_manager_depart_parent(managers=[])
