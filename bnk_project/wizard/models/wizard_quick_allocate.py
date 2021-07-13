# -*- coding: utf-8 -*-
import datetime
from datetime import date
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class WizardQuickAllocateLine(models.TransientModel):
    _name = 'wizard.quick.allocate.line'

    quick_allocate_id = fields.Many2one('wizard.quick.allocate')
    project_id = fields.Many2one('project.project', related='quick_allocate_id.project_id')
    employee_id = fields.Many2one('hr.employee')
    from_date = fields.Date(required=True)
    to_date = fields.Date(required=True)
    percent = fields.Float(default=100)
    billable = fields.Selection([('none', 'None'), ('billable', 'Billable'),
                                 ('investment', 'Investment')],
                                required=True, default='billable')

    @api.multi
    def generate_employee_allocate_resource(self, employee_id, leaves_dict, holidays_list, current_date):
        self.ensure_one()
        if current_date in holidays_list:
            return False

        for leave in leaves_dict.get(str(employee_id), []):
            from_date = leave['from_date']
            to_date = leave['to_date']

            if from_date <= current_date and to_date >= current_date:
                return False
        vals = {
            'date': current_date,
            'project_id': self.project_id.id,
            'employee_id': employee_id,
            'percent': self.percent,
            'billable': self.billable
        }
        return self.env['allocate.resource'].create(vals)


class WizardQuickAllocate(models.TransientModel):
    _name = 'wizard.quick.allocate'

    project_id = fields.Many2one(
        'project.project', 'Project', required=True)

    allocate_line_ids = fields.One2many('wizard.quick.allocate.line', 'quick_allocate_id')

    @api.constrains('percent')
    def _check_percent(self):
        for wizard in self:
            if wizard.percent <= 0 or wizard.percent > 100:
                raise ValidationError(
                    _('Percent must be > 0 and <= 100!'))

    @api.multi
    def get_leaves(self):
        employee_ids_list = []
        from_date_min = date.today()
        to_date_max = date.today()
        for allocate_line in self.allocate_line_ids:
            employee_ids_list.append(allocate_line.employee_id.id)
            if allocate_line.from_date < from_date_min:
                from_date_min = allocate_line.from_date
            if allocate_line.to_date > to_date_max:
                to_date_max = allocate_line.to_date

        domain = [
            ('state', 'in', ('validate', 'validate1')),
            ('request_unit_half', '=', False),
            ('holiday_type', '=', 'employee'),
            ('request_date_from', '>=', from_date_min),
            ('request_date_to', '<=', to_date_max),
            ('employee_id', 'in', employee_ids_list)
        ]
        leaves = self.env['hr.leave'].search(domain)

        res = {}

        for leave in leaves:
            emloyee_id = str(leave.employee_id.id)
            if not res.get(emloyee_id, False):
                res[emloyee_id] = []
            res[emloyee_id].append({
                'from_date': leave.request_date_from,
                'to_date': leave.request_date_to
            })
        return res

    @api.multi
    def get_holidays(self):

        # get min_date and max date
        from_date_min = date.today()
        to_date_max = date.today()
        for allocate_line in self.allocate_line_ids:
            if allocate_line.from_date < from_date_min:
                from_date_min = allocate_line.from_date
            if allocate_line.to_date > to_date_max:
                to_date_max = allocate_line.to_date

        domain = [
            ('state', '=', 'approved'),
            ('date', '>=', from_date_min),
            ('date', '<=', to_date_max),
            ]

        holidays = self.env['public.holiday.line'].search(domain)

        holiday_list = []

        if len(holidays) == 0:
            holiday_list = []
        else:
            for holiday in holidays:
                if not (holiday.date in holiday_list):
                    holiday_list.append(holiday.date)
        return holiday_list

    @api.multi
    def generate_allocate_resource(self):
        self.ensure_one()

        leaves_dict = self.get_leaves()

        holidays_list = self.get_holidays()

        resource_calendar_id = self.env.user.resource_calendar_id
        if resource_calendar_id:
            working_dow_list = []
            for attendance in resource_calendar_id.attendance_ids:
                dayofweek = int(attendance.dayofweek)
                if dayofweek not in working_dow_list:
                    working_dow_list.append(dayofweek)
        else:
            working_dow_list = [0, 1, 2, 3, 4]
        allocate_ids = []

        for allocate_line in self.allocate_line_ids:
            current_date = allocate_line.from_date + datetime.timedelta(days=-1)
            to_date = allocate_line.to_date
            while current_date < to_date:
                current_date = current_date + datetime.timedelta(days=1)
                dow = current_date.weekday()
                if dow not in working_dow_list:
                    continue
                allocate_id = allocate_line.generate_employee_allocate_resource(
                    allocate_line.employee_id.id, leaves_dict, holidays_list, current_date)
                if allocate_id:
                    allocate_ids.append(allocate_id)

        return allocate_ids
