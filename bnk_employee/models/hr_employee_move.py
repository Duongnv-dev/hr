from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from datetime import datetime


class HrEmployeeMove(models.Model):
    _name = 'hr.employee.move'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Employee Movement'

    name = fields.Char('No.', readonly=True, copy=False, default='Movement No.')
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_for_approval', 'Waiting For Approval'),
        ('done', 'Done'),
    ], default='draft')

    department_id = fields.Many2one('hr.department', string='Department')
    department_loc = fields.Char(string='Work Location')
    manager_id = fields.Many2one('hr.employee', string='Manager', compute='_compute_manager_id', store=True)
    resource_calendar_id = fields.Many2one('resource.calendar', string='Working Hours')

    old_department_id = fields.Many2one('hr.department', string='Department')
    old_department_loc = fields.Char(string='Work Location')
    old_manager_id = fields.Many2one('hr.employee', string='Manager')
    old_resource_calendar_id = fields.Many2one('resource.calendar', string='Working Hours')

    date = fields.Date(string='Date')

    @api.depends('department_id')
    def _compute_manager_id(self):
        for employee in self.filtered('department_id.manager_id'):
            employee.manager_id = employee.department_id.manager_id

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        if self.employee_id:
            self.old_department_id = self.employee_id.department_id
            self.old_department_loc = self.employee_id.work_location
            self.old_manager_id = self.employee_id.parent_id
            self.old_resource_calendar_id = self.employee_id.resource_calendar_id

    @api.model
    def create(self, vals):
        res = super(HrEmployeeMove, self).create(vals)
        if res.name == 'Movement No.':
            sequence_id = self.env['ir.sequence'].get('hp.employee.move') or 'Movement No.'
            res.write({'name': sequence_id})
        return res

    def action_waiting_for_approval(self):
        return self.write({'state': 'waiting_for_approval'})

    def action_done(self):
        vals_list = {}
        employee = self.employee_id
        department_change = ''
        work_location_change = ''
        manager_change = ''
        working_hours_change = ''
        if self.department_id:
            vals_list['department_id'] = self.department_id.id
            department_change = '<br/>* Department: {} -> {}<br/>'.format(self.old_department_id.name, self.department_id.name)
        if self.department_loc:
            vals_list['work_location'] = self.department_loc
            work_location_change = '* Work Location: {} -> {}<br/>'.format(self.old_department_loc, self.department_loc)
        if self.manager_id:
            vals_list['parent_id'] = self.manager_id.id
            manager_change = '* Manager: {} -> {}<br/>'.format(self.old_manager_id.name, self.manager_id.name)
        if self.resource_calendar_id:
            vals_list['resource_calendar_id'] = self.resource_calendar_id.id
            working_hours_change = '* Working Hours: {} -> {}'.format(self.old_resource_calendar_id.name,
                                                                        self.resource_calendar_id.name)
        if not vals_list:
            raise ValidationError(_("Nothing Change!!!"))
        log = '''Employee Movement: 
                    {} 
                    {}
                    {}
                    {}
        '''
        body = log.format(department_change, manager_change, work_location_change, working_hours_change)
        employee.message_post(body=body)
        self.employee_id.write(vals_list)
        if not self.date:
            self.date = datetime.today().date()
        return self.write({'state': 'done'})
