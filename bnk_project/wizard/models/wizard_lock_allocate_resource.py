# -*- coding: utf-8 -*-
import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT


class WizardLockAllocateResource(models.TransientModel):
    _name = 'wizard.lock.allocate.resource'

    from_date = fields.Date(required=True)
    to_date = fields.Date(required=True)
    project_ids = fields.Many2many(
        'project.project', 'wizard_lock_allocate_resource_project_project_rel',
        'wizard_id', 'project_id', required=True)
    type = fields.Selection([('lock', 'Lock'), ('unlock', 'Unlock')],
                            default='lock', required=True)

    @api.model
    def default_get(self, fields_list):
        res = super(WizardLockAllocateResource, self).default_get(fields_list)
        res['project_ids'] = [(6, False, self.env.context.get('active_ids', []))]
        return res

    @api.multi
    def check_security_sm(self):
        if not self.env.user.has_group('bnk_project.group_allocate_resource_sm'):
            raise UserError(_('Access denied, only project SM can do this!'))

    @api.multi
    def action_lock(self):
        if self.type != 'lock':
            return {'type': 'ir.actions.act_window_close'}

        self.check_security_sm()

        for project in self.project_ids:
            from_date = self.from_date
            to_date = self.to_date

            value_list = []

            while from_date <= to_date:
                value_list.append(
                    (0, 0, {'date': from_date.strftime(DEFAULT_SERVER_DATE_FORMAT)})
                )
                from_date = from_date + datetime.timedelta(days=1)
            project.write({'lock_date_ids': value_list})

        # domain = [('project_id', 'in', self.project_ids._ids),
        #           ('lock', '=', False), ('date', '<=', self.to_date)]
        # if self.from_date:
        #     domain.append(('date', '>=', self.from_date))
        #
        # allocates = self.env['allocate.resource'].search(domain)
        #
        # if allocates:
        #     allocates.write({'lock': True})
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def action_unlock(self):
        if self.type != 'unlock':
            return {'type': 'ir.actions.act_window_close'}

        self.check_security_sm()

        domain = [('project_id', 'in', self.project_ids._ids),
                  ('date', '<=', self.to_date)]
        if self.from_date:
            domain.append(('date', '>=', self.from_date))

        locks = self.env['project.lock.date'].search(domain)
        if locks:
            locks.unlink()
        return {'type': 'ir.actions.act_window_close'}
