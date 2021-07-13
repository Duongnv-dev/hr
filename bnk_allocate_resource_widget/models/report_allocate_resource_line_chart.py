# -*- coding: utf-8 -*-
import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT


class ReportAllocateResourceLineChart(models.TransientModel):
    _name = 'report.allocate.resource.line.chart'

    @api.model
    def selection_compute_get_month(self):
        return self.env['report.allocate.resource'].selection_compute_get_month()

    name = fields.Char(compute='_compute_name')
    group_by = fields.Selection(
        [('week', 'Week'), ('month', 'Month'), ('quarter', 'Quarter')],
        required=True, default='week')
    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    project_ids = fields.Many2many(
        'project.project', 'report_allocate_resource_line_chart_project_rel',
        'report_id', 'project_id', 'Projects')
    employee_ids = fields.Many2many(
        'hr.employee', 'report_allocate_resource_line_chart_employee_rel',
        'report_id', 'employee_id', 'Employees')

    site_ids = fields.Many2many(
        'hr.site', 'report_allocate_resource_line_chart_site_rel',
        'report_id', 'site_id', 'Sites')

    company_ids = fields.Many2many(
        'res.company', 'report_allocate_resource_line_chart_company_rel',
        'report_id', 'company_id', 'Companies')

    billable = fields.Selection(
        [('none', 'None'), ('billable', 'Billable'),
         ('investment', 'Investment')],
        required=False)
    ot = fields.Selection([('ot', 'OT'), ('not_ot', 'Not ot')],
                          string='OT')
    month = fields.Selection(selection_compute_get_month)

    @api.depends('date_from', 'date_to')
    def _compute_name(self):
        for report in self:
            date_from = report.date_from or ''
            date_to = report.date_to or ''
            name = _('Report line chart allocate resource {} - {}').format(date_from, date_to)
            report.name = name

    @api.model
    def default_get(self, fields_list):
        res = super(ReportAllocateResourceLineChart, self).default_get(fields_list)
        month_list = self.selection_compute_get_month()
        current_month = datetime.datetime.now().strftime('%Y-%m')

        if (current_month, current_month) in month_list:
            res['month'] = current_month

        return res

    @api.onchange('month')
    def month_change(self):
        if self.month:
            self.date_from = '{}-01'.format(self.month)
            next_month = '{}-01'.format(self.env['report.allocate.resource'].next_month_str(self.month))
            next_month = datetime.datetime.strptime(next_month, DEFAULT_SERVER_DATE_FORMAT)
            self.date_to = (next_month + datetime.timedelta(days=-1)).strftime(DEFAULT_SERVER_DATE_FORMAT)
        else:
            self.date_from = False
            self.date_to = False

    @api.multi
    def next_month(self):
        self.ensure_one()
        if not self.month:
            return True

        month_selection = self.selection_compute_get_month()
        next_month = self.env['report.allocate.resource'].next_month_str(self.month)

        if (next_month, next_month) in month_selection:
            self.write({'month': next_month})
            self.month_change()
        return True

    @api.multi
    def previous_month(self):
        self.ensure_one()
        if not self.month:
            return True

        month_selection = self.selection_compute_get_month()
        previous_month = self.env['report.allocate.resource'].previous_month_str(self.month)

        if (previous_month, previous_month) in month_selection:
            self.write({'month': previous_month})
            self.month_change()
        return True

    @api.model
    def get_where_clause(self, report_id):
        report = self.browse(report_id)
        res = "where ar.date >= '{}' and ar.date <= '{}'".format(
            report.date_from.strftime(DEFAULT_SERVER_DATE_FORMAT),
            report.date_to.strftime(DEFAULT_SERVER_DATE_FORMAT))
        if report.project_ids:
            project_ids = ','.join([str(project_id) for project_id in report.project_ids._ids])
            res = res + ' and project_id in ({})'.format(project_ids)

        if report.employee_ids:
            employee_ids = ','.join([str(employee_id) for employee_id in report.employee_ids._ids])
            res = res + ' and employee_id in ({})'.format(employee_ids)

        if report.site_ids:
            site_ids = ','.join([str(site_id) for site_id in report.site_ids._ids])
            res = res + ' and site_id in ({})'.format(site_ids)

        if report.company_ids:
            company_ids = ','.join([str(company_id) for company_id in report.company_ids._ids])
            res = res + ' and company_id in ({})'.format(company_ids)

        if report.billable:
            res = res + " and billable = '{}'".format(report.billable)

        if report.ot:
            if report.ot == 'not_ot':
                res = res + " and (ot is false or ot is null)"
            elif report.ot == 'ot':
                res = res + " and ot is true"

        return res


    @api.model
    def get_allocate_resource_line_chart_widget_data(self, report_id):
        if not report_id:
            return {}

        def process_number(num):
            if num >= 0 and num < 10:
                return '0{}'.format(num)
            return str(num)
        def get_week(allocate):
            # return '{}/W{}'.format(int(allocate['year']), int(allocate['week']))
            return allocate['week'].replace('-', '/W')

        def get_month(allocate):
            return '{}/{}'.format(int(allocate['year']), process_number(int(allocate['month'])))

        def get_quarter(allocate):
            return '{}/Q{}'.format(int(allocate['year']), process_number(int(allocate['quarter'])))

        def next_week(time_value):
            year, week = time_value.split('/W')
            if week == '52':
                return '{}/W01'.format(int(year) + 1)
            return '{}/W{}'.format(year, process_number(int(week) + 1))

        def next_month(time_value):
            year, month = time_value.split('/')
            if month == '12':
                return '{}/01'.format(int(year) + 1)
            return '{}/{}'.format(year, process_number(int(month) + 1))

        def next_quarter(time_value):
            year, quarter = time_value.split('/Q')
            if quarter == '4':
                return '{}/Q01'.format(int(year) + 1)
            return '{}/Q{}'.format(year, process_number(int(quarter) + 1))

        def process_allocate_item(allocate, data_dict, get_function):
            time_value = get_function(allocate)

            if not data_dict.get(time_value, False):
                data_dict[time_value] = {
                    'total': 0,
                    'total_billable': 0,
                    'employee_ids': [],
                }
            data_dict[time_value]['total'] += allocate['percent']/100
            if allocate['billable'] == 'billable':
                data_dict[time_value]['total_billable'] += allocate['percent'] / 100

            employee_id = allocate['employee_id'] or 0

            if employee_id and employee_id not in \
                    data_dict[time_value]['employee_ids']:
                data_dict[time_value]['employee_ids'].append(employee_id)

        report = self.browse(report_id)
        cr = self.env.cr

        group_by = report.group_by

        function_dict = {
            'week': get_week,
            'month': get_month,
            'quarter': get_quarter,
        }

        get_function = function_dict[group_by]

        where_clause = self.get_where_clause(report_id)

        querry = """
            select ar.id, ar.date, billable, employee_id, percent,
                to_char(ar.date, 'IYYY-IW') as week,
                EXTRACT(QUARTER FROM ar.date) as quarter,
                EXTRACT(Month FROM ar.date) as month,
                EXTRACT(year FROM ar.date) as year
            from allocate_resource as ar
            {}
        """.format(where_clause)

        cr.execute(querry)

        data_dict = {}

        for allocate in cr.dictfetchall():
            process_allocate_item(allocate, data_dict, get_function)

        for time_value in data_dict.keys():
            data_dict[time_value]['ee'] = 0
            if data_dict[time_value]['total']:
                data_dict[time_value]['ee'] = \
                    data_dict[time_value]['total_billable'] * 100 / \
                    data_dict[time_value]['total']
            data_dict[time_value]['ee'] = round(data_dict[time_value]['ee'], 2)
            data_dict[time_value]['total_billable'] = round(data_dict[time_value]['total_billable'], 2)
            data_dict[time_value]['total'] = round(data_dict[time_value]['total'], 2)
            data_dict[time_value]['employee_count'] = len(data_dict[time_value]['employee_ids'])

        querry = """
                select
                    to_char(TIMESTAMP '{date_from}', 'IYYY-IW') as week,
                    EXTRACT(QUARTER FROM TIMESTAMP '{date_from}') as quarter,
                    EXTRACT(Month FROM TIMESTAMP '{date_from}') as month,
                    EXTRACT(year FROM TIMESTAMP '{date_from}') as year,

                    to_char(TIMESTAMP '{date_to}', 'IYYY-IW') as to_week,
                    EXTRACT(QUARTER FROM TIMESTAMP '{date_to}') as to_quarter,
                    EXTRACT(Month FROM TIMESTAMP '{date_to}') as to_month,
                    EXTRACT(year FROM TIMESTAMP '{date_to}') as to_year
                from allocate_resource as ar
                limit 1
        """.format(date_from=report.date_from.strftime(DEFAULT_SERVER_DATE_FORMAT),
                   date_to=report.date_to.strftime(DEFAULT_SERVER_DATE_FORMAT))

        cr.execute(querry)
        querry_result = cr.dictfetchone()

        allocate_from = {
            'week': querry_result['week'],
            'quarter': querry_result['quarter'],
            'month': querry_result['month'],
            'year': querry_result['year'],
        }
        time_from = get_function(allocate_from)

        allocate_to = {
            'week': querry_result['to_week'],
            'quarter': querry_result['to_quarter'],
            'month': querry_result['to_month'],
            'year': querry_result['to_year'],
        }
        time_to = get_function(allocate_to)

        same_year = True
        if allocate_from['year'] != allocate_to['year']:
            same_year = False

        pre_labels = []

        next_function_dict = {
            'week': next_week,
            'month': next_month,
            'quarter': next_quarter,
        }

        next_function = next_function_dict[group_by]

        current_time = time_from
        for i in range(0, 1000):
            if current_time == time_to:
                pre_labels.append(current_time)
                break

            pre_labels.append(current_time)
            current_time = next_function(current_time)

        total_data = []
        total_billable_data = []
        labels = []
        for label in pre_labels:
            ee = data_dict.get(label, {}).get('ee', 0)
            employee_count = data_dict.get(label, {}).get('employee_count', 0)
            total_billable = data_dict.get(label, {}).get('total_billable', 0)
            total = data_dict.get(label, {}).get('total', 0)

            if same_year:
                label = label.split('/')[1]

            final_label = '{} ({})({}%)'.format(label, employee_count, ee)
            labels.append(final_label)
            total_billable_data.append(total_billable)
            total_data.append(total)

        datas = {
            'labels': labels,
            'datasets': [
                {
                'data': total_data,
                'label': "Total",
                'borderColor': "#3e95cd",
                'fill': False
            },
                {
                'data': total_billable_data,
                'label': "Total billable",
                'borderColor': "#f56962",
                'fill': False
            }
            ]
        }
        return datas
