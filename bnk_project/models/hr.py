# -*- coding: utf-8 -*-
import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    # @api.multi
    # def get_employee(self):
    #     self.ensure_one()
    #
    #     employee_ids = []
    #     if self.holiday_type == 'employee':
    #         employee_ids.append(self.employee_id.id)
    #     elif self.holiday_type == 'company':
    #         employees = self.env['hr.employee'].search(
    #             [('company_id', '=', self.mode_company_id.id)])
    #         employee_ids.extend(employees._ids)
    #     elif self.holiday_type == 'department':
    #         employees = self.env['hr.employee'].search(
    #             [('department_id', '=', self.department_id.id)])
    #         employee_ids.extend(employees._ids)
    #     elif self.holiday_type == 'category':
    #         employees = self.env['hr.employee'].search(
    #             [('category_ids', 'in', self.category_id.id)])
    #         employee_ids.extend(employees._ids)
    #     return employee_ids

    # when approve leave request: add allocate resource to leave project,
    # reduction other project allocate resource
    @api.multi
    def action_approve(self):
        res = super(HrLeave, self).action_approve()
        leave_project = self.env.ref('bnk_project.project_leave_data')
        leave_project_id = leave_project and leave_project.id or 0

        to_process = self.filtered(lambda l: l.request_date_from and l.request_date_to and l.holiday_type == 'employee')
        if not to_process:
            return res

        half_process = to_process.filtered(lambda l: l.request_unit_half is True)
        if half_process:
            employee_ids = half_process.mapped('employee_id')._ids
            if employee_ids:
                for half in half_process:
                    domain = [('employee_id', '=', half.employee_id.id), ('date', '>=', half.request_date_from),
                              ('date', '<=', half.request_date_to)]

                    allocates = self.env['allocate.resource'].sudo().search(domain)
                    remaining = 50
                    for allo in allocates:
                        if remaining == 0 or allo.project_id.id == leave_project_id:
                            allo.unlink()
                            continue
                        effort = min(remaining, allo.percent)
                        allo.write({'percent': effort})
                        remaining = remaining - effort

                    if not leave_project:
                        continue
                    val = {
                        'project_id': leave_project.id,
                        'employee_id': half.employee_id.id,
                        'date': datetime.datetime.strftime(half.request_date_from, '%Y-%m-%d'),
                        'percent': 50,
                        'billable': 'none',
                    }
                    self.env['allocate.resource'].sudo().create(val)

        full_process = to_process.filtered(lambda l: not l.request_unit_half)
        if full_process:
            employee_ids = full_process.mapped('employee_id')._ids
            if employee_ids:
                for leave in full_process:
                    domain = [('employee_id', '=', leave.employee_id.id),
                              ('date', '>=', leave.request_date_from),
                              ('date', '<=', leave.request_date_to)]

                    allocates = self.env['allocate.resource'].sudo().search(domain)
                    if allocates:
                        allocates.unlink()

                    days_allocate = leave.get_worked_day()
                    if not leave_project:
                        continue
                    for day in days_allocate:
                        val = {
                            'project_id': leave_project.id,
                            'employee_id': leave.employee_id.id,
                            'date': datetime.datetime.strftime(day, '%Y-%m-%d'),
                            'billable': 'none',
                            }
                        self.env['allocate.resource'].sudo().create(val)
        return res

    # delete allocate resource on leave project when refuse leave request
    @api.multi
    def action_refuse(self):
        res = super(HrLeave, self).action_refuse()

        leave_project = self.env.ref('bnk_project.project_leave_data')
        leave_project_id = leave_project and leave_project.id or 0

        if not leave_project_id:
            return res

        to_process = self.filtered(lambda l: l.request_date_from and l.request_date_to and l.holiday_type == 'employee')
        if not to_process:
            return res

        for leave in to_process:
            if not leave.employee_id:
                continue

            domain = [('employee_id', '=', leave.employee_id.id), ('date', '>=', leave.request_date_from),
                      ('date', '<=', leave.request_date_to), ('project_id', '=', leave_project_id)]
            allocates = self.env['allocate.resource'].sudo().search(domain)
            allocates.unlink()

        return res

    def get_worked_day(self):
        resource_id = self.employee_id.resource_calendar_id
        if resource_id:
            work_list = []
            for attendance in resource_id.attendance_ids:
                dayofweek = int(attendance.dayofweek)
                if dayofweek not in work_list:
                    work_list.append(dayofweek)
        else:
            work_list = [0, 1, 2, 3, 4]

        days = []
        request_date_from = self.request_date_from
        request_date_to = self.request_date_to
        while request_date_from <= request_date_to:
            if request_date_from.weekday() in work_list:
                days.append(request_date_from)
            request_date_from = request_date_from + datetime.timedelta(days=1)
        return days
