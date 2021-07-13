# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model
    def hide_group_system_group_erp_manager_selection(self):
        view = self.sudo().env.ref('base.user_groups_view')
        group_system = self.env.ref('base.group_system')
        group_erp_manager = self.env.ref('base.group_erp_manager')

        element1 = '<field name="sel_groups_{}_{}"'.format(group_erp_manager.id, group_system.id)
        element1_replace = element1.replace('field', 'field groups="base.group_system" ')
        element2 = '<field name="sel_groups_{}_{}"'.format(group_system.id, group_erp_manager.id)
        element2_replace = element2.replace('field', 'field groups="base.group_system" ')

        arch_db = view.arch_db.replace(element1, element1_replace).replace(element2, element2_replace)
        view.write({'arch_db': arch_db})
        return True
