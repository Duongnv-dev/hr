# -*- coding: utf-8 -*-
from odoo import models, fields, api, tools, _
from odoo.exceptions import ValidationError
import datetime


class ItemcheckCategoryLine(models.Model):
    _name = 'item.check'

    name = fields.Char(string="To do", required=True)


class ItemcheckCategory(models.Model):
    _name = 'item.check.category'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char()
    item_check_line_ids = fields.Many2many('item.check')
    department_id = fields.Many2many('hr.department', string="Department")


class OnboardingChecklistLine(models.Model):
    _name = 'onboarding.checklist.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    item_list = fields.Many2one('item.check', string="Check list")
    note = fields.Text()
    state = fields.Selection(
        [('not_start', 'Not Start'), ('process', 'Processing'), ('done', 'Done'), ('cancel', 'Cancel')],
        default='not_start', string='Status', track_visibility='onchange')
    onboarding_checklist_id = fields.Many2one('onboarding.checklist')
    start_date = fields.Date()
    end_date = fields.Date('Date Completed')


class OnboardingChecklist(models.Model):
    _name = 'onboarding.checklist'
    _rec_name = 'employee_id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def get_default_employee(self):
        empl = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)])
        if not empl:
            return
        return empl[0].id

    def default_manager(self):
        return self.env.ref('hr.group_hr_manager').id

    employee_id = fields.Many2one('hr.employee', copy=False, default=get_default_employee)
    item_check_id = fields.Many2one('item.check.category', 'Checklist Template', track_visibility='onchange')
    state = fields.Selection(
        [('not_start', 'Not Start'), ('process', 'Processing'), ('done', 'Done'), ('cancel', 'Cancel')],
        default='not_start',
        track_visibility='onchange')
    onboarding_checklist_line_ids = fields.One2many('onboarding.checklist.line', 'onboarding_checklist_id')
    manager_group_id = fields.Many2one('res.groups', compute='_compute_get_manager', default=default_manager)
    department_id = fields.Many2one('hr.department', compute='_compute_get_department')

    @api.multi
    def _compute_get_manager(self):
        for request in self:
            request.manager_group_id = self.env.ref('hr.group_hr_manager').id

    @api.one
    @api.depends('employee_id')
    def _compute_get_department(self):
        if self.employee_id:
            self.department_id = self.employee_id.department_id

    @api.onchange('item_check_id')
    def onchange_item_check_id(self):
        items_check_list = self.item_check_id.item_check_line_ids
        line_list = []
        for item in items_check_list:
            val_line = {
                'item_list': item.id,
                'start_date': datetime.date.today()
            }
            line = self.env['onboarding.checklist.line'].create(val_line)
            line_list.append(line.id)
        self.onboarding_checklist_line_ids = self.env['onboarding.checklist.line'].browse(line_list)

    @api.model
    def create(self, val):
        if self._context.get('create_from_context', False):
            context = self._context
            employee_id = context.get('employee_id')
            item_check_id = context.get('item_check_id')
            val = {}
            val['employee_id'] = employee_id.id
            val['item_check_id'] = item_check_id.id
            line_list = []
            for item in item_check_id.item_check_line_ids:
                val_line = {
                    'item_list': item.id,
                    'start_date': datetime.date.today()
                }
                line = self.env['onboarding.checklist.line'].create(val_line)
                line_list.append(line.id)
            val['onboarding_checklist_line_ids'] = [(6, 0, line_list)]
        return super(OnboardingChecklist, self).create(val)

    @api.onchange('employee_id')
    def check_dupicate_item_check_id(self):
        self.item_check_id = False

    @api.multi
    def action_cancel(self):
        self.write({'state': 'cancel'})

    @api.multi
    def action_confirm(self):
        self.write({'state': 'process'})

    @api.constrains('onboarding_checklist_line_ids')
    def onchange_onboarding_checklist_line_ids(self):
        check_list_lines = self.onboarding_checklist_line_ids
        list_state_done = []
        list_state_cancel = []
        list_state_done_cancel = []
        if check_list_lines:
            for line in check_list_lines:
                if line.state == 'done':
                    list_state_done.append(line.state)
                    list_state_done_cancel.append(line.state)
                elif line.state == 'cancel':
                    list_state_cancel.append(line.state)
                    list_state_done_cancel.append(line.state)
            if len(check_list_lines) == len(list_state_done):
                self.write({
                    'state': 'done'
                })
            elif len(check_list_lines) == len(list_state_cancel):
                self.write({
                    'state': 'cancel'
                })
            elif len(check_list_lines) == len(list_state_done_cancel):
                self.write({
                    'state': 'done'
                })
        else:
            pass

    @api.multi
    def unlink(self):
        for line in self:
            if line.state in ['done', 'cancel']:
                raise ValidationError("Cannot be deleted when status is Done and Cancel")
        else:
            return super(OnboardingChecklist, self).unlink()
