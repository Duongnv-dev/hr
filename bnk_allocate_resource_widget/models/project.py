# -*- coding: utf-8 -*-
import datetime
import copy
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT


class AllocateResource(models.Model):
    _inherit = 'allocate.resource'

    month = fields.Char(compute='_compute_month', store=True)

    @api.depends('date')
    def _compute_month(self):
        for s in self:
            if not s.date:
                s.month = False
            month = '{}-{}'.format(s.date.year, int(s.date.month))
            s.month = month


class Project(models.Model):
    _inherit = 'project.project'

    @api.model
    def get_public_holiday(self, date_from, date_to):
        domain = [('date', '>=', date_from), ('date', '<=', date_to)]
        holidays = self.env['public.holiday.line'].search(domain)

        public_holiday_list = \
            [holiday.date.strftime(DEFAULT_SERVER_DATE_FORMAT) for holiday in holidays]
        return public_holiday_list

    @api.model
    def get_lock_date(self, lock_dict, date, project_id):
        res = date in lock_dict.get(project_id, [])
        return res

    @api.model
    def get_working_weekday(self):
        resource_calendar_id = self.env.user.resource_calendar_id
        if resource_calendar_id:
            working_dow_list = []
            for attendance in resource_calendar_id.attendance_ids:
                dayofweek = int(attendance.dayofweek)
                if dayofweek not in working_dow_list:
                    working_dow_list.append(dayofweek)
        else:
            working_dow_list = [0, 1, 2, 3, 4]
        return working_dow_list

    @api.model
    def check_holiday(self, date_item, working_weekday):
        date_item = datetime.datetime.strptime(
            date_item, DEFAULT_SERVER_DATE_FORMAT)
        if date_item.weekday() in working_weekday:
            return False
        return True

    @api.model
    def process_field_value(self, value):
        if value == False:
            return 'Undefine', 'Undefine'
        if isinstance(value, (list, tuple)):
            return value[0], value[1]
        if isinstance(value, (datetime.datetime)):
            value = value.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        if isinstance(value, (datetime.date)):
            value = value.strftime(DEFAULT_SERVER_DATE_FORMAT)
        return value, value

    @api.model
    def get_allocate_resource_widget_data(
            self, date_from, date_to, domain=[], user_groupby=False,
            show_detail=False, project_id=False):

        if user_groupby in ('employee_id', 'date'):
            user_groupby = False

        groupby = user_groupby and [user_groupby, 'employee_id', 'date'] \
                  or ['employee_id', 'date']

        fields = ['project_id', 'employee_id', 'billable', 'percent', 'lock', 'date', 'ot']

        allocate_obj = self.env['allocate.resource'].search(domain)

        projects = allocate_obj.mapped('project_id')
        lock_dict = projects.get_lock_dict()

        allocates = allocate_obj.read(fields)

        if not allocates:
            return {}

        start_date = allocates[0]['date']
        end_date = allocates[0]['date']

        allocate_dict = {}
        group_field_key_dict = dict((f, []) for f in groupby)
        group_field_value_dict = dict((f, {}) for f in groupby)

        employees = self.env['hr.employee'].search([])
        employee_dict = dict((e.id, {'place': e.site_id.name, 'skill': e.skill}) for e in employees)

        working_time_dict = employees.get_contractual_working_time()

        for allocate in allocates:
            start_date = min(start_date, allocate['date'])
            end_date = max(end_date, allocate['date'])

            item = allocate_dict
            for f in groupby:
                key, value = self.process_field_value(allocate[f])

                group_field_key_dict[f].append(key)
                group_field_value_dict[f][key] = value

                if f != groupby[-1]:
                    if not item.get(key, False):
                        item[key] = {}
                else:
                    if not item.get(key, False):
                        item[key] = []
                item = item[key]
            allocate['date'] = allocate['date'].strftime(DEFAULT_SERVER_DATE_FORMAT)
            item.append(allocate)

        working_weekday = self.get_working_weekday()

        if date_from:
            start_date = date_from

        if date_to:
            end_date = date_to

        date_list = []
        month_dict = {}
        holiday_list = []
        current_date = start_date
        while current_date <= end_date:
            current_date_str = current_date.strftime(DEFAULT_SERVER_DATE_FORMAT)
            date_list.append(current_date_str)

            month = current_date.month
            if month < 10:
                month = '0{}'.format(month)
            current_month = '{}-{}'.format(current_date.year, month)
            if not month_dict.get(current_month, False):
                month_dict[current_month] = 0
            month_dict[current_month] += 1

            holiday = self.check_holiday(current_date_str, working_weekday)
            if holiday:
                holiday_list.append(current_date_str)
            current_date = current_date + datetime.timedelta(days=1)

        months = list(month_dict.keys())
        months.sort()
        month_list = [{'month': month,
                       'num_day': month_dict[month]} for month in months]

        grid = []
        sum_line = {
            'total': 0,
            'billable_total': 0,
            'unallocate_total': 0,

        }
        public_holiday_list = self.get_public_holiday(start_date, end_date)
        if user_groupby:
            for k in allocate_dict.keys():
                user_groupby_label = group_field_value_dict[user_groupby][k]
                for employee_id in allocate_dict[k].keys():
                    employee = self.env['hr.employee'].browse(employee_id)
                    employee_label = group_field_value_dict['employee_id'][employee_id]
                    current_row = {
                        'label': [user_groupby_label, employee_label],
                        'skill': employee_dict.get(employee_id, {}).get('skill', ''),
                        'place': employee_dict.get(employee_id, {}).get('place', ''),
                        'date': {},
                        'project_id': k,
                        'employee_id': employee_id,
                        'total': 0,
                        'billable_total': 0,
                        'unallocate_total': 0,
                    }

                    for date_item in date_list:
                        current_date = {
                            'total_percent': 0,
                            'un_ot_total': 0,
                            'lines': [],
                            'billable': False,
                            'lock': self.get_lock_date(lock_dict, date_item, k),
                            'working_time': employee.check_contractual_working_time(working_time_dict, date_item)
                        }
                        if date_item in public_holiday_list:  # Nếu ngày đang xét thuộc ngày nghỉ công khai thì cộng tổng và billabel lên 1
                            current_row['total'] += 1
                            current_row['billable_total'] += 1
                        else:
                            for allocate in allocate_dict[k][employee_id].get(date_item, []):
                                current_date['total_percent'] += allocate['percent']

                                current_row['total'] += round(allocate['percent'] / 100, 2)

                                if not allocate['ot']:
                                    current_date['un_ot_total'] += allocate['percent']

                                if allocate['billable'] == 'billable':
                                    current_row['billable_total'] += round(allocate['percent'] / 100, 2)
                                    current_date['billable'] = True

                                if allocate['lock']:
                                    current_date['lock'] = True

                                current_date['lines'].append(allocate)

                        current_date['line_ids'] = ','.join([str(line['id']) for line in current_date['lines']])

                        current_row['date'][date_item] = current_date

                        if current_date['total_percent'] < 100 and date_item not in holiday_list: #Nếu tổng phần trăm của ngày hiện tại nhỏ hơn 100 và ngày đang xét không thuộc ngày nghỉ
                            if date_item not in public_holiday_list:
                                current_row['unallocate_total'] += 1

                        if not sum_line.get(date_item, False):
                            sum_line[date_item] = 0
                        sum_line[date_item] += current_date['total_percent']

                    current_row['total'] = round(current_row['total'], 2)
                    current_row['billable_total'] = round(current_row['billable_total'], 2)
                    current_row['unallocate_total'] = round(current_row['unallocate_total'], 2)

                    sum_line['total'] += current_row['total']
                    sum_line['billable_total'] += current_row['billable_total']
                    sum_line['unallocate_total'] += current_row['unallocate_total']

                    grid.append(current_row)
        else:
            for employee_id in allocate_dict.keys():
                employee = self.env['hr.employee'].browse(employee_id)
                employee_label = group_field_value_dict['employee_id'][employee_id]
                current_row = {
                    'label': [employee_label],
                    'skill': employee_dict.get(employee_id, {}).get('skill', ''),
                    'place': employee_dict.get(employee_id, {}).get('place', ''),
                    'date': {},
                    'project_id': project_id,
                    'employee_id': employee_id,
                    'total': 0,
                    'billable_total': 0,
                    'unallocate_total': 0,
                }
                for date_item in date_list:
                    current_date = {'total_percent': 0,
                                    'un_ot_total': 0,
                                    'lines': [],
                                    'billable': False,
                                    'lock': self.get_lock_date(lock_dict, date_item, project_id),
                                    'working_time': employee.check_contractual_working_time(working_time_dict,
                                                                                            date_item)
                                    }

                    if date_item in public_holiday_list:  # Nếu ngày đang xét thuộc ngày nghỉ công khai thì cộng tổng và billabel lên 1
                        current_row['total'] += 1
                        current_row['billable_total'] += 1
                    else:
                        for allocate in allocate_dict[employee_id].get(date_item, []):
                            current_date['total_percent'] += allocate['percent']
                            current_row['total'] += round(allocate['percent'] / 100, 2)

                            if not allocate['ot']:
                                current_date['un_ot_total'] += allocate['percent']

                            if allocate['billable'] == 'billable':
                                current_row['billable_total'] += round(allocate['percent'] / 100, 2)
                                current_date['billable'] = True

                            # if allocate['lock']:
                            #     current_date['lock'] = True

                            current_date['lines'].append(allocate)

                    current_date['line_ids'] = ','.join([str(line['id']) for line in current_date['lines']])

                    current_row['date'][date_item] = current_date

                    if current_date['total_percent'] < 100 and date_item not in holiday_list: #Nếu tổng phần trăm của ngày hiện tại nhỏ hơn 100 và ngày đang xét không thuộc ngày nghỉ
                        if date_item not in public_holiday_list:
                            current_row['unallocate_total'] += 1

                    if not sum_line.get(date_item, False):
                        sum_line[date_item] = 0
                    sum_line[date_item] += current_date['total_percent']

                current_row['total'] = round(current_row['total'], 2)
                current_row['billable_total'] = round(current_row['billable_total'], 2)
                current_row['unallocate_total'] = round(current_row['unallocate_total'], 2)

                sum_line['total'] += current_row['total']
                sum_line['billable_total'] += current_row['billable_total']
                sum_line['unallocate_total'] += current_row['unallocate_total']

                grid.append(current_row)

        # for line in grid:
        #     print('----------')
        #     print(line['label'])
        #     print(line['date'])

        sum_line['total'] = round(sum_line['total'], 2)
        sum_line['billable_total'] = round(sum_line['billable_total'], 2)
        sum_line['unallocate_total'] = round(sum_line['unallocate_total'], 2)
        for date_item in date_list:
            sum_line[date_item] = round(sum_line[date_item] / 100, 2)

        grid_dict = {
            'date_list': date_list,
            'allocate_dict': allocate_dict,
            'grid': grid,
            'holiday_list': holiday_list,
            'group_field_key_dict': group_field_key_dict,
            'group_field_value_dict': group_field_value_dict,
            'month_list': month_list,
            'show_detail': show_detail,
            'public_holiday_list': public_holiday_list,
            'sum_line': sum_line,
        }
        return grid_dict

    # report group
    @api.model
    def set_sub_group_by(self, current_row, allocate, date_item, sub_groupby,
                         group_field_value_dict, employee_dict, date_list):
        # set sub group by
        sub_key = allocate[sub_groupby] and allocate[sub_groupby][0] or 'Undefine'
        if not current_row['sub_group_by'].get(sub_key, False):
            current_row['sub_group_by'][sub_key] = {
                'label': group_field_value_dict[sub_groupby].get(sub_key, ''),
                'skill': sub_groupby == 'employee_id' and employee_dict.get(sub_key, {}).get('skill', '') or '',
                'place': sub_groupby == 'employee_id' and employee_dict.get(sub_key, {}).get('place', '') or '',
                'date': dict(
                    (date_item, {'total_percent': 0, 'un_ot_total': 0, 'billable': False}) for date_item in date_list),
                'total': 0,
                'billable_total': 0,
                'unallocate_total': 0,
            }

        current_row['sub_group_by'][sub_key]['date'][date_item]['total_percent'] += allocate['percent']
        current_row['sub_group_by'][sub_key]['total'] += round(allocate['percent'] / 100, 2)
        if allocate['billable'] == 'billable':
            current_row['sub_group_by'][sub_key]['billable_total'] += round(allocate['percent'] / 100, 2)
            current_row['sub_group_by'][sub_key]['date'][date_item]['billable'] = True

        if not allocate['ot']:
            current_row['sub_group_by'][sub_key]['date'][date_item]['un_ot_total'] += allocate['percent']

        current_row['sub_group_by'][sub_key]['total'] = \
            round(current_row['sub_group_by'][sub_key]['total'], 2)
        current_row['sub_group_by'][sub_key]['billable_total'] = \
            round(current_row['sub_group_by'][sub_key]['billable_total'], 2)
        current_row['sub_group_by'][sub_key]['unallocate_total'] = \
            round(current_row['sub_group_by'][sub_key]['unallocate_total'], 2)

    @api.model
    def set_contract_working_time(
            self, grid, date_list, working_time_dict, groupby):
        if groupby[0] == 'employee_id':
            for line in grid:
                employee_id = line['key']
                employee = self.env['hr.employee'].browse(employee_id)
                for date_item in date_list:
                    working_time = \
                        employee.check_contractual_working_time(
                            working_time_dict, date_item)

                    line['date'][date_item]['working_time'] = working_time

                    for sub_key in line['sub_group_by'].keys():
                        line['sub_group_by'][sub_key]['date'
                        ][date_item]['working_time'] = working_time
        else:
            for line in grid:
                for date_item in date_list:
                    line['date'][date_item]['working_time'] = True

                for employee_id in line['sub_group_by'].keys():
                    employee = self.env['hr.employee'].browse(employee_id)
                    sub_line = line['sub_group_by'][employee_id]
                    for date_item in date_list:
                        sub_line['date'][date_item]['working_time'] = \
                            employee.check_contractual_working_time(
                                working_time_dict, date_item)
        return grid

    @api.model
    def get_allocate_resource_group_widget_data(self, date_from, date_to, domain, groupby):

        sub_groupby = 'project_id'

        groupby_label = ['Employee']
        if groupby == ['project_id']:
            groupby_label = ['Project']
            sub_groupby = 'employee_id'

        if 'date' in groupby:
            groupby.remove('date')

        groupby.append('date')

        fields = ['project_id', 'employee_id', 'billable', 'percent', 'lock', 'date', 'ot']

        allocates = self.env['allocate.resource'].search(domain).read(fields)

        if not allocates:
            return {}

        start_date = allocates[0]['date']
        end_date = allocates[0]['date']

        allocate_dict = {}
        group_field_key_dict = dict((f, []) for f in groupby)
        group_field_value_dict = dict((f, {}) for f in groupby)
        group_field_value_dict[sub_groupby] = {}

        employees = self.env['hr.employee'].search([])
        employee_dict = dict((e.id, {'place': e.site_id.name or '',
                                     'skill': e.skill or '',
                                     'name': e.name or ''}) for e in employees)
        working_time_dict = employees.get_contractual_working_time()

        for allocate in allocates:
            start_date = min(start_date, allocate['date'])
            end_date = max(end_date, allocate['date'])

            key, value = self.process_field_value(allocate[sub_groupby])
            group_field_value_dict[sub_groupby][key] = value

            item = allocate_dict
            for f in groupby:
                key, value = self.process_field_value(allocate[f])

                group_field_key_dict[f].append(key)
                group_field_value_dict[f][key] = value

                if f != groupby[-1]:
                    if not item.get(key, False):
                        item[key] = {}
                else:
                    if not item.get(key, False):
                        item[key] = []
                item = item[key]
            allocate['date'] = allocate['date'].strftime(DEFAULT_SERVER_DATE_FORMAT)
            item.append(allocate)

        working_weekday = self.get_working_weekday()

        if date_from:
            start_date = date_from

        if date_to:
            end_date = date_to

        date_list = []
        month_dict = {}
        holiday_list = []
        current_date = start_date
        while current_date <= end_date:
            current_date_str = current_date.strftime(DEFAULT_SERVER_DATE_FORMAT)
            date_list.append(current_date_str)

            month = current_date.month
            if month < 10:
                month = '0{}'.format(month)
            current_month = '{}-{}'.format(current_date.year, month)
            if not month_dict.get(current_month, False):
                month_dict[current_month] = 0
            month_dict[current_month] += 1

            holiday = self.check_holiday(current_date_str, working_weekday)
            if holiday:
                holiday_list.append(current_date_str)
            current_date = current_date + datetime.timedelta(days=1)

        months = list(month_dict.keys())
        months.sort()
        month_list = [{'month': month,
                       'num_day': month_dict[month]} for month in months]

        grid = []
        sum_line = {
            'total': 0,
            'billable_total': 0,
            'unallocate_total': 0,

        }
        for key in allocate_dict.keys():
            label = group_field_value_dict[groupby[0]][key]

            skill, place = '', ''
            if groupby[0] == 'employee_id':
                skill = employee_dict.get(key, {}).get('skill', '')
                place = employee_dict.get(key, {}).get('place', '')

            current_row = {
                'label': [label],
                'skill': skill,
                'place': place,
                'date': {},
                'sub_group_by': {},
                'total': 0,
                'billable_total': 0,
                'unallocate_total': 0,
                'key': key,
            }
            for date_item in date_list:
                current_date = {
                    'total_percent': 0,
                    'un_ot_total': 0,
                    'lines': [],
                    'billable': False,
                    'lock': False,
                }
                for allocate in allocate_dict[key].get(date_item, []):
                    current_date['total_percent'] += allocate['percent']
                    current_row['total'] += round(allocate['percent'] / 100, 2)
                    sum_line['total'] += round(allocate['percent'] / 100, 2)

                    if allocate['billable'] == 'billable':
                        current_row['billable_total'] += round(allocate['percent'] / 100, 2)
                        sum_line['billable_total'] += round(allocate['percent'] / 100, 2)
                        current_date['billable'] = True

                    if not allocate['ot']:
                        current_date['un_ot_total'] += allocate['percent']

                    if allocate['lock']:
                        current_date['lock'] = True

                    current_date['lines'].append(allocate)

                    self.set_sub_group_by(current_row, allocate, date_item, sub_groupby,
                                          group_field_value_dict, employee_dict, date_list)

                current_row['total'] = round(current_row['total'], 2)
                current_row['billable_total'] = round(current_row['billable_total'], 2)
                current_row['unallocate_total'] = round(current_row['unallocate_total'], 2)
                current_row['date'][date_item] = current_date

                if not sum_line.get(date_item, False):
                    sum_line[date_item] = 0
                sum_line[date_item] += current_date['total_percent']

                # set sub group by total
                if date_item not in holiday_list:
                    if current_date['total_percent'] < 100:
                        current_row['unallocate_total'] += 1

            for date_item in date_list:
                if date_item in holiday_list:
                    continue
                for sub_key in current_row['sub_group_by'].keys():
                    if current_row['sub_group_by'][sub_key]['date'][date_item]['total_percent'] < 100:
                        current_row['sub_group_by'][sub_key]['unallocate_total'] += 1

            sum_line['unallocate_total'] += current_row['unallocate_total']

            grid.append(current_row)

        sum_line['total'] = round(sum_line['total'], 2)
        sum_line['billable_total'] = round(sum_line['billable_total'], 2)
        sum_line['unallocate_total'] = round(sum_line['unallocate_total'], 2)
        for date_item in date_list:
            sum_line[date_item] = round(sum_line[date_item] / 100, 2)

        public_holiday_list = self.get_public_holiday(start_date, end_date)

        if groupby[0] == 'employee_id':
            date_row = {}
            unallocate_total = 0
            for date_item in date_list:
                current_date = {
                    'total_percent': 0,
                    'un_ot_total': 0,
                    'lines': [],
                    'billable': False,
                    'lock': False,
                }
                if date_item not in holiday_list \
                        and date_item not in public_holiday_list:
                    unallocate_total += 1

                date_row[date_item] = current_date
            for employee in employees:
                if employee.id in allocate_dict.keys():
                    continue

                copy_date_row = copy.deepcopy(date_row)
                grid.append({
                    'label': [employee_dict[employee.id]['name']],
                    'date': copy_date_row,
                    'sub_group_by': {},
                    'key': employee.id,
                    'place': employee_dict[employee.id]['place'],
                    'skill': employee_dict[employee.id]['skill'],
                    'billable_total': 0,
                    'unallocate_total': unallocate_total,
                    'total': 0,
                })
                sum_line['unallocate_total'] += unallocate_total

        grid = self.set_contract_working_time(
            grid, date_list, working_time_dict, groupby)

        grid_dict = {
            'date_list': date_list,
            'allocate_dict': allocate_dict,
            'grid': grid,
            'holiday_list': holiday_list,
            'group_field_key_dict': group_field_key_dict,
            'group_field_value_dict': group_field_value_dict,
            'month_list': month_list,
            'groupby_label': groupby_label,
            'public_holiday_list': public_holiday_list,
            'sum_line': sum_line,
        }
        return grid_dict
