# -*- coding: utf-8 -*-
import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
import json


class ReportDeliveryAllocateResource(models.TransientModel):
    _name = 'report.delivery.allocate.resource'

    @api.model
    def selection_compute_get_year(self):
        min_allocate = self.env['allocate.resource'].search(
            [], order='date', limit=1)
        if not min_allocate:
            current_year = datetime.datetime.now().strftime('%Y')
            return [current_year, current_year]
        min_year = min_allocate.date.strftime('%Y')
        max_allocate = self.env['allocate.resource'].search(
            [], order='date desc', limit=1)
        max_year = max_allocate.date.strftime('%Y')
        year_list = []
        current_year = int(min_year)
        while current_year <= int(max_year):
            if current_year not in year_list:
                year_list.append(str(current_year))
            current_year += 1
        res = []
        for year in year_list:
            res.append((year, year))
        return res

    name = fields.Char(default='Allocate resource')
    project_ids = fields.Many2many(
        'project.project', 'report_delivery_allocate_resource_project_rel',
        'report_id', 'project_id', 'Projects')

    year = fields.Selection(selection_compute_get_year)

    date_from = fields.Date()
    date_to = fields.Date()

    @api.onchange('year')
    def year_change(self):
        if self.year:
            self.date_from = '{}-01-01'.format(self.year)
            self.date_to = '{}-12-31'.format(self.year)
        else:
            self.date_from = False
            self.date_to = False

    @api.multi
    def next_year(self):
        self.ensure_one()
        if not self.year:
            return True

        year_selection = self.selection_compute_get_year()
        next_year = str(int(self.year) + 1)

        if (next_year, next_year) in year_selection:
            self.write({'year': next_year})
            self.year_change()
        return True

    @api.multi
    def previous_year(self):
        self.ensure_one()
        if not self.year:
            return True

        year_selection = self.selection_compute_get_year()
        prev_year = str(int(self.year) - 1)
        if (prev_year, prev_year) in year_selection:
            self.write({'year': prev_year})
            self.year_change()
        return True

    @api.model
    def default_get(self, fields_list):
        res = super(ReportDeliveryAllocateResource, self).default_get(fields_list)
        year_list = self.selection_compute_get_year()
        current_year = datetime.datetime.now().strftime('%Y')

        if (current_year, current_year) in year_list:
            res['year'] = current_year
        return res

    @api.multi
    def json_dumps_employee(self, source):
        for month in source.keys():
            if month in ('employee', 'total'):
                continue
            source[month]['employee'] = json.dumps(source[month]['employee'])
        return json.dumps(source)

    @api.multi
    def get_general_delivery_report_data(self):
        report_id = self.id
        if not report_id:
            return {}

        head_count_dict = self.get_head_count()
        year_month_list = self.get_month_list()
        month_list = [m.split('-')[1] for m in year_month_list]

        billable_dict = self.get_billable()

        unbillable_dict = self.get_un_bill()

        training_dict = self.get_training()

        available_dict = self.get_available()

        ee_dict = self.get_ee(billable_dict, head_count_dict)

        un_allocated = self.get_un_allocated(head_count_dict)

        res = {
            'head_count_dict': head_count_dict,
            'year_month_list': year_month_list,
            'month_list': month_list,
            'full_month_list': self.get_full_month_list(),
            'billable_dict': billable_dict,
            'unbillable_dict': unbillable_dict,
            'training_dict': training_dict,
            'available_dict': available_dict,
            'ee_dict': ee_dict,
            'un_allocated': un_allocated,
        }
        return res

    def ok(self):
        return True

    def get_employee(self):
        if not self.project_ids:
            return []
        employee_ids = []
        for e in self.project_ids.mapped('employee_ids'):
            if e.member_id.id not in employee_ids:
                employee_ids.append(e.member_id.id)
        return employee_ids

    @api.model
    def get_domain(self, report_id):
        report = self.browse(report_id)
        domain = []
        if report.project_ids:
            domain.append(('project_id', 'in', report.project_ids._ids))
        return domain

    @api.model
    def previous_month(self, month):
        y, m = month.split('-')
        y = int(y)
        m = int(m)
        if m == 1:
            return '{}-12'.format(y - 1)
        return '{}-{}'.format(y, m - 1)

    @api.model
    def next_month(self, month):
        y, m = month.split('-')
        y = int(y)
        m = int(m)
        if m == 12:
            return '{}-1'.format(y + 1)
        return '{}-{}'.format(y, m + 1)

    @api.model
    def compare_month(self, source, dest):
        y, m = source.split('-')
        sy = int(y)
        sm = int(m)

        y, m = dest.split('-')
        dy = int(y)
        dm = int(m)

        if sy == dy:
            if sm == dm:
                return '='
            if sm > dm:
                return '>'
            return '<'

        if sy > dy:
            return '>'
        return '<'

    def get_contract_range(self):
        year = self.year
        start = '{}-1-1'.format(year)
        end = '{}-12-31'.format(year)

        employee_ids = self.get_employee()
        employee_ids.append(0)
        employee_where = ''
        if self.project_ids:
            employee_where = ' and employee_id in ({}) '.format(','.join([str(employee_id) for employee_id in employee_ids]))

        query = """
            select id, employee_id, date_start, date_end 
            from hr_contract 
            where state in ('open', 'close')
                and employee_id is not null 
                and (
                (date_start <= '{start}' and date_end <= '{start}')
                or
                (date_start <= '{end}' and date_end <= '{end}')
                or
                (date_start <= '{end}' and date_end is null)
                )
                {employee_where}
        """.format(start=start, end=end, employee_where=employee_where)
        self.env.cr.execute(query)

        res = {}
        for contract in self.env.cr.dictfetchall():
            employee_id = contract.get('employee_id', False)
            if not res.get(employee_id, False):
                res[employee_id] = []
            res[employee_id].append({
                'start': contract['date_start'].strftime(DEFAULT_SERVER_DATE_FORMAT),
                'end': contract['date_end'].strftime(DEFAULT_SERVER_DATE_FORMAT)
            })

        return res

    @api.multi
    def get_month_list(self):
        current_month = '{}-{}'.format(datetime.datetime.now().year, int(datetime.datetime.now().month))
        full_month_list = self.get_full_month_list()

        month_list = []
        for m in full_month_list:
            if self.compare_month(current_month, m) in ('>', '='):
                month_list.append(m)
        return month_list

    @api.multi
    def get_full_month_list(self):
        month_list = []
        for m in range(1, 13):
            month_list.append('{}-{}'.format(self.year, m))

        return month_list

    @api.model
    def check_overlap(self, period, contract):
        period_start = datetime.datetime.strptime(period[0], DEFAULT_SERVER_DATE_FORMAT)
        period_stop = datetime.datetime.strptime(period[1], DEFAULT_SERVER_DATE_FORMAT)
        contract_start = datetime.datetime.strptime(contract[0], DEFAULT_SERVER_DATE_FORMAT)
        contract_stop = False
        if contract[1]:
            contract_stop = datetime.datetime.strptime(contract[1], DEFAULT_SERVER_DATE_FORMAT)

        if not contract_stop:
            if contract_start <= period_start:
                return 1
            if contract_start <= period_stop:
                return 0.5
            return 0

        # else contract stop not false
        if contract_start <= period_start and period_stop <= contract_stop:
            return 1
        if (contract_start >= period_start and contract_start <= period_stop) or (contract_stop >= period_start and contract_stop <= period_stop):
            return 0.5
        return 0

    @api.multi
    def get_head_count(self):
        month_list = self.get_month_list()
        # get contract
        contract_range = self.get_contract_range()

        head_count_dict = {'total': 0}

        employee_ids = []

        for month in month_list:
            if not head_count_dict.get(month, False):
                head_count_dict[month] = {
                    'total': 0,
                    'employee': []
                }
            for employee_id in contract_range.keys():
                last_day_of_month = self.next_month(month) + '-01'
                last_day_of_month = datetime.datetime.strptime(last_day_of_month, DEFAULT_SERVER_DATE_FORMAT)
                last_day_of_month = last_day_of_month + datetime.timedelta(days=-1)
                last_day_of_month = last_day_of_month.strftime(DEFAULT_SERVER_DATE_FORMAT)
                period = [month + '-01', last_day_of_month]
                employee_month_value = [0]
                for contract in contract_range[employee_id]:
                    contract_value = self.check_overlap(period, [contract['start'], contract['end']])
                    employee_month_value.append(contract_value)

                head_count_dict[month][employee_id] = max(employee_month_value)
                if head_count_dict[month][employee_id] > 0:
                    head_count_dict[month]['employee'].append(employee_id)
                    employee_ids.append(employee_id)

                head_count_dict[month]['total'] += head_count_dict[month][employee_id]
            head_count_dict['total'] += head_count_dict[month]['total']

        employee_name_get = self.env['hr.employee'].browse(employee_ids).name_get()
        employee_name_dict = dict((employee[0], employee) for employee in employee_name_get)

        for month in head_count_dict.keys():
            if month == 'total':
                continue

            employee_ids = head_count_dict[month]['employee']
            employee = [employee_name_dict.get(employee_id) for employee_id in employee_ids]

            head_count_dict[month]['employee'] = employee

        full_month_list = self.get_full_month_list()
        for m in full_month_list:
            if not head_count_dict.get(m, False):
                head_count_dict[m] = {
                    'total': '',
                    'employee': []
                }

        self.json_dumps_employee(head_count_dict)
        return head_count_dict

    @api.multi
    def get_billable(self):
        full_month_list = self.get_full_month_list()

        start_date = '{}-01-01'.format(self.year)
        current_month = datetime.datetime.now().strftime('%Y-%m')
        next_month = self.next_month(current_month)
        end_date = next_month + '-01'


        billable_dict = {'total': 0}
        domain = [('date', '>=', start_date),('date', '<', end_date),('billable', '=', 'billable'),('ot', '=', False)]
        if self.project_ids:
            domain.append(('project_id', 'in', self.project_ids._ids))

        # allocates = self.env['allocate.resource'].search(domain)
        allocate_group = self.env['allocate.resource'].read_group(domain, ['percent'], ['month'])

        for allocate in allocate_group:
            percent = allocate['percent'] or 0
            percent = percent/100
            month = allocate['month'] or ''
            billable_dict[month] = percent
            billable_dict['total'] += percent

        for month in full_month_list:
            if month not in billable_dict.keys():
                billable_dict[month] = ''

        return billable_dict

    def get_month_working_day(self):
        # tính ra danh sách các ngày làm việc trong từng tháng
        def get_day_list_from_month(month):
            month_int = int(month.split('-')[1])
            start_day = datetime.datetime.strptime(month + '-01', DEFAULT_SERVER_DATE_FORMAT)
            res = []
            for i in range(0, 32):
                res.append(start_day)
                start_day = start_day + datetime.timedelta(days=1)
                if start_day.month != month_int:
                    break
            return res

        # get weekly working day
        weekly_working_day = []
        calendar = self.env.ref('resource.resource_calendar_std')
        for attendance in calendar.attendance_ids:
            dayofweek = int(attendance.dayofweek)
            if dayofweek not in weekly_working_day:
                weekly_working_day.append(dayofweek)

        # get public holiday
        public_holidays = self.env['public.holiday'].search([('state', '=', 'approved')])
        domain = [('date', '>=', '{}-01-01'.format(self.year)),
                  ('date', '<=', '{}-12-31'.format(self.year)),
                  ('public_holiday_id', 'in', public_holidays._ids)]
        public_holiday_lines = self.env['public.holiday.line'].search(domain)

        holidays = [line.date.strftime(DEFAULT_SERVER_DATE_FORMAT) for line in public_holiday_lines]

        # get month working day foreach employee
        month_list = self.get_month_list()
        res = {}
        for month in month_list:
            res[month] = []
            for day in get_day_list_from_month(month):
                if day.weekday() not in weekly_working_day:
                    continue

                if day.strftime(DEFAULT_SERVER_DATE_FORMAT) in holidays:
                    continue

                res[month].append(day.strftime(DEFAULT_SERVER_DATE_FORMAT))
        return res

    # def get_month_working_day(self):
    #     full_month_list = self.get_full_month_list()
    #
    #     contract_range = self.get_contract_range()
    #     employee_ids = self.get_employee()
    #     if not employee_ids:
    #         employee_ids = self.env['hr.employee'].search([])._ids
    #
    #     month_working_day = self.get_month_working_day()
    #     return

    @api.multi
    def get_un_bill(self):
        def check_contract_valid(employee_contract, day):
            day = datetime.datetime.strptime(day, DEFAULT_SERVER_DATE_FORMAT)
            for contract in employee_contract:
                contract_start = contract['start']
                contract_start = datetime.datetime.strptime(contract_start, DEFAULT_SERVER_DATE_FORMAT)
                contract_end = contract['end']
                if contract_end:
                    contract_end = datetime.datetime.strptime(contract_end, DEFAULT_SERVER_DATE_FORMAT)
                if contract_start <= day and (not contract_end or contract_end >= day):
                    return True

            return False

        full_month_list = self.get_full_month_list()
        month_list = self.get_month_list()

        # contract foreach employee
        contract_range = self.get_contract_range()
        employee_ids = self.get_employee()
        if not employee_ids:
            employee_ids = self.env['hr.employee'].search([])._ids

        # general working calendar foreach month
        month_working_day = self.get_month_working_day()

        billable_dict = self.get_billable()

        # sum working day number by contract foreach month
        res = {}
        for month in month_list:
            res[month] = 0
            month_days = month_working_day.get(month, [])
            for day in month_days:
                for employee_id in employee_ids:
                    employee_contract = contract_range.get(employee_id, [])
                    if not check_contract_valid(employee_contract, day):
                        continue
                    res[month] += 1

        # calculate unbill = sum working day number - billable day number
        total = 0
        for month in month_list:
            working_day_number = res.get(month, 0) or 0
            month_billable = billable_dict.get(month, 0) or 0
            res[month] = working_day_number - month_billable
            total += res[month]

        # calculate total
        res['total'] = total
        for month in full_month_list:
            if month not in res.keys():
                res[month] = ''
        return res

    @api.model
    def get_training(self):
        full_month_list = self.get_full_month_list()
        month_list = self.get_month_list()
        res = dict((m, 0) for m in month_list)

        res['total'] = 0

        start_date = '{}-01-01'.format(self.year)
        current_month = datetime.datetime.now().strftime('%Y-%m')
        next_month = self.next_month(current_month)
        end_date = next_month + '-01'

        domain = [('date', '>=', start_date), ('date', '<', end_date), ('training', '=', True),
                  ('ot', '=', False)]
        if self.project_ids:
            domain.append(('project_id', 'in', self.project_ids._ids))

        allocate_group = self.env['allocate.resource'].read_group(domain, ['percent'], ['month'])

        for allocate in allocate_group:

            percent = allocate['percent'] or 0
            percent = percent/100
            month = allocate['month'] or ''

            if not month:
                continue

            res[month] = percent
            res['total'] += percent

        for m in full_month_list:
            if m not in res.keys():
                res[m] = ''

        return res

    @api.model
    def get_available(self):
        full_month_list = self.get_full_month_list()
        month_list = self.get_month_list()
        # res = dict((m, 0) for m in month_list)
        res = {}
        res['total'] = 0

        start_date = '{}-01-01'.format(self.year)
        current_month = datetime.datetime.now().strftime('%Y-%m')
        next_month = self.next_month(current_month)
        end_date = next_month + '-01'

        domain = [('date', '>=', start_date), ('date', '<', end_date), ('available', '=', True),
                  ('ot', '=', False)]
        if self.project_ids:
            domain.append(('project_id', 'in', self.project_ids._ids))

        allocate_group = self.env['allocate.resource'].read_group(domain, ['percent'], ['month'])

        project_clause = ''
        if self.project_ids:
            project_clause = ' and ar.project_id in ({}) '.format(
                ','.join([str(project_id) for project_id in self.project_ids._ids]))
        query = """
            select ar.month, ar.employee_id
            from allocate_resource as ar 
            where ar.date >= '{start_date}'
                and ar.date <= '{end_date}'
                and ar.available = true 
                and ar.ot = false
                {project_clause}
            group by ar.month, ar.employee_id 
        """.format(start_date=start_date, end_date=end_date, project_clause=project_clause)
        self.env.cr.execute(query)

        employee_ids = []
        employee_available_dict = {}
        for row in self.env.cr.dictfetchall():
            month = row['month']
            employee_id = row['employee_id']

            if not employee_available_dict.get(month, False):
                employee_available_dict[month] = []

            if employee_id not in employee_available_dict[month]:
                employee_available_dict[month].append(employee_id)

            if employee_id not in employee_ids:
                employee_ids.append(employee_id)

        employee_name_get = self.env['hr.employee'].browse(employee_ids).name_get()
        employee_name_dict = dict((employee[0], employee) for employee in employee_name_get)

        for allocate in allocate_group:

            percent = allocate['percent'] or 0
            percent = percent/100
            month = allocate['month'] or ''

            if not month:
                continue

            res[month] = {}
            res[month]['percent'] = percent
            res[month]['employee'] = []
            employee_ids = employee_available_dict.get(month, [])
            for employee_id in employee_ids:
                employee_name = employee_name_dict.get(employee_id, False)
                if not employee_name:
                    continue

                if employee_name not in res[month]['employee']:
                    res[month]['employee'].append(employee_name)

            res['total'] += percent

        for m in full_month_list:
            if m not in res.keys():
                res[m] = {
                    'percent': '',
                    'employee': []
                }
        self.json_dumps_employee(res)
        return res

    @api.model
    def get_ee(self, billable_dict, head_count_dict):
        full_month_list = self.get_full_month_list()
        month_list = self.get_month_list()
        res = {'total': 0}

        for m in month_list:
            billable = billable_dict.get(m, 0)
            head_count = head_count_dict.get(m, {}).get('total', 0)

            ee = 0
            if head_count and billable:
                ee = round(billable / head_count, 2)

            res[m] = '{} %'.format(ee)
            res['total'] += ee

        for m in full_month_list:
            if m not in res.keys():
                res[m] = ''
        return res

    @api.model
    def get_un_allocated(self, head_count_dict):
        full_month_list = self.get_full_month_list()
        month_list = self.get_month_list()
        res = {'total': 0}

        start_date = '{}-01-01'.format(self.year)
        current_month = datetime.datetime.now().strftime('%Y-%m')
        next_month = self.next_month(current_month)
        end_date = next_month + '-01'

        # domain = [('date', '>=', start_date), ('date', '<', end_date)]
        # if self.project_ids:
        #     domain.append(('project_id', 'in', self.project_ids._ids))
        #
        # resource_group = self.env['allocate.resource'].read_group(domain, ['employee_id'], ['month'])

        project_clause = ''
        if self.project_ids:
            project_clause = ' and ar.project_id in ({}) '.format(','.join([str(project_id) for project_id in self.project_ids._ids]))

        query = """
            select ar.month, ar.employee_id 
            from allocate_resource as ar 
            where ar.date >= '{start_date}'
                and ar.date <= '{end_date}' 
                {project_clause}
            group by ar.month, ar.employee_id
        """.format(start_date=start_date, end_date=end_date, project_clause=project_clause)
        self.env.cr.execute(query)
        resource_group = self.env.cr.dictfetchall()

        employee_ids = []
        allocated_dict = {}
        for resource in resource_group:
            month = resource['month']
            employee_id = resource['employee_id']

            if not allocated_dict.get(month, False):
                allocated_dict[month] = []

            if employee_id not in allocated_dict[month]:
                allocated_dict[month].append(employee_id)

        for month in month_list:
            un_allocated = 0
            month_employee_ids = []
            for employee_id in head_count_dict.get(month, {}).keys():
                if employee_id in ('total', 'employee'):
                    continue

                if employee_id in allocated_dict.get(month, []):
                    continue

                un_allocated += head_count_dict.get(month, {}).get(employee_id, 0)
                if head_count_dict.get(month, {}).get(employee_id, 0):
                    month_employee_ids.append(employee_id)
            res[month] = {
                'percent': un_allocated,
                'employee_ids': month_employee_ids
            }
            employee_ids.extend(month_employee_ids)

        employee_name_get = self.env['hr.employee'].browse(employee_ids).name_get()
        employee_name_dict = dict((employee[0], employee) for employee in employee_name_get)

        for month in res.keys():
            if month == 'total':
                continue

            month_employee_ids = res[month]['employee_ids']
            employee_name_ids = []
            for month_employee_id in month_employee_ids:
                employee_name = employee_name_dict.get(month_employee_id, [])
                employee_name_ids.append(employee_name)
            res[month]['employee'] = employee_name_ids

        for m in full_month_list:
            if m not in res.keys():
                res[m] = {
                'percent': '',
                'employee': []
            }
        self.json_dumps_employee(res)
        return res


