from odoo import models, fields, api, tools, _
from datetime import datetime, date, timedelta, time
from odoo.tools.float_utils import float_round


class HrLeave(models.Model):
    _inherit = 'hr.leave'
    _description = 'Inherit leave'

    number_of_hours_text = fields.Char(readonly=True)

    @api.onchange('date_from', 'date_to', 'employee_id')
    def _onchange_leave_dates(self):
        """
        Override function to skip holiday when employee log time off
        """
        for holiday in self:
            if holiday.date_from and holiday.date_to and holiday.employee_id:
                emp_dayofweek = []
                for attendance in holiday.employee_id.resource_calendar_id.attendance_ids:
                    emp_dayofweek.append(dict(attendance._fields['dayofweek'].selection).get(attendance.dayofweek))
                off_dates = []
                for i in range(0, (holiday.date_to - holiday.date_from).days + 1):
                    off_dates.append((holiday.date_from + timedelta(days=i)).date())
                public_holiday_lines = self.env['public.holiday.line'].search([('date', '>=', holiday.date_from),
                                                                               ('date', '<=', holiday.date_to),
                                                                               ('state', '=', 'approved')])
                holidays = []
                for line in public_holiday_lines:
                    if line.date.strftime('%A') not in emp_dayofweek:
                        continue
                    holidays.append(line.date)
                resource_calendar = holiday.employee_id.resource_calendar_id
                result = self.get_work_duration(resource_calendar)
                hours_per_day_config = holiday.employee_id.resource_calendar_id.hours_per_day_config
                skip_holiday_count = 0
                skip_hours_count = 0
                for off_date in off_dates:
                    off_dayofweek = off_date.strftime('%A')
                    if off_date in holidays and off_dayofweek in emp_dayofweek:
                        skip_holiday_count += 1
                        if holiday.request_unit_half:
                            skip_hours_count += 0
                        else:
                            skip_hours_count += result[off_dayofweek]
                    elif off_date not in holidays and off_dayofweek in emp_dayofweek:
                        if result[off_dayofweek] / hours_per_day_config > 0.5:
                            continue
                        if result[off_dayofweek] / hours_per_day_config <= 0.5:
                            skip_holiday_count += 0.5
                holiday.number_of_days = holiday._get_number_of_days(holiday.date_from, holiday.date_to, holiday.employee_id.id) - skip_holiday_count
                hours = self.env.user.company_id.resource_calendar_id.get_work_hours_count(holiday.date_from, holiday.date_to)
                holiday.number_of_hours_text = '%s%g %s%s' % (
                    '' if holiday.request_unit_half or holiday.request_unit_hours else '(',
                    float_round((hours - skip_hours_count), precision_digits=2), _('Hours'), '' if holiday.request_unit_half or holiday.request_unit_hours else ')')
            else:
                holiday.number_of_days = 0

    def get_work_duration(self, resource_calendar):
        result = {}
        if resource_calendar:
            for attendance in resource_calendar.attendance_ids:
                hours = (attendance.hour_to - attendance.hour_from)
                dayofweek = dict(attendance._fields['dayofweek'].selection).get(attendance.dayofweek)
                if dayofweek in result:
                    result[dayofweek] += hours
                    continue
                else:
                    result[dayofweek] = hours
        return result


class ResourceCalendarInherit(models.Model):
    _inherit = 'resource.calendar'

    hours_per_day_config = fields.Integer(default=8, required=True)
