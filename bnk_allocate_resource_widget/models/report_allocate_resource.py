# -*- coding: utf-8 -*-
import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT


class ReportAllocateResource(models.TransientModel):
    _name = 'report.allocate.resource'

    @api.model
    def next_month_str(self, month_str):
        year = int(month_str.split('-')[0])
        month = int(month_str.split('-')[1])
        if month == 12:
            return '{}-1'.format(year + 1)
        return '{}-{}'.format(year, month + 1)

    @api.model
    def previous_month_str(self, month_str):
        year = int(month_str.split('-')[0])
        month = int(month_str.split('-')[1])
        if month == 1:
            return '{}-12'.format(year - 1)
        return '{}-{}'.format(year, month - 1)

    @api.model
    def format_month(self, month):
        year, m = month.split('-')
        if int(m) < 10:
            m = '0{}'.format(int(m))
        return '{}-{}'.format(year, m)

    @api.model
    def selection_compute_get_month(self):
        def get_value_month(month_str):
            year = int(month_str.split('-')[0])
            month = int(month_str.split('-')[1])
            return year*12 + month

        min_allocate = self.env['allocate.resource'].search(
            [], order='date', limit=1)
        if not min_allocate:
            current_month = datetime.datetime.now().strftime('%Y-%m')
            current_month = self.format_month(current_month)
            return [(current_month, current_month)]
        min_month = min_allocate.date.strftime('%Y-%m')
        max_allocate = self.env['allocate.resource'].search(
            [], order='date desc', limit=1)
        max_month = max_allocate.date.strftime('%Y-%m')
        month_list = []
        current_month = min_month
        while get_value_month(current_month) <= get_value_month(max_month):
            if current_month not in month_list:
                month_list.append(current_month)
            current_month = self.next_month_str(current_month)
        res = []
        for month in month_list:
            month = self.format_month(month)
            res.append((month, month))
        return res

    name = fields.Char(compute='_compute_name')
    project_ids = fields.Many2many(
        'project.project', 'report_allocate_resource_project_rel',
        'report_id', 'project_id', 'Projects')
    employee_ids = fields.Many2many(
        'hr.employee', 'report_allocate_resource_employee_rel',
        'report_id', 'employee_id', 'Employees')

    site_ids = fields.Many2many(
        'hr.site', 'report_allocate_resource_site_rel',
        'report_id', 'site_id', 'Sites')

    company_ids = fields.Many2many(
        'res.company', 'report_allocate_resource_company_rel',
        'report_id', 'company_id', 'Companies')

    billable = fields.Selection(
        [('none', 'None'), ('billable', 'Billable'),
         ('investment', 'Investment')],
        required=False)
    ot = fields.Selection([('ot', 'OT'), ('not_ot', 'Not ot')],
                          string='OT')
    group_by = fields.Selection([('project_employee', 'Project > Employee'),
                                 ('employee_project', 'Employee > Project')],
                                string='Group by', default='employee_project')

    month = fields.Selection(selection_compute_get_month)

    date_from = fields.Date()
    date_to = fields.Date()

    group_by_project = fields.Boolean(default=False)
    show_detail = fields.Boolean(default=False)
    name = fields.Char(default='Allocate resource')
    type = fields.Selection([('normal', 'Normal'), ('group', 'Group')],
                            default='group')

    @api.depends('type', 'date_from', 'date_to')
    def _compute_name(self):
        for report in self:
            report_type = report.type == 'group' and 'group' or ''
            name = _('Report allocate resource {}').format(report_type)
            report.name = name

    def ok(self):
        return True

    @api.model
    def default_get(self, fields_list):
        res = super(ReportAllocateResource, self).default_get(fields_list)
        month_list = self.selection_compute_get_month()
        current_month = datetime.datetime.now().strftime('%Y-%m')
        
        if (current_month, current_month) in month_list:
            res['month'] = current_month

        return res

    @api.onchange('month')
    def month_change(self):
        if self.month:
            self.date_from = '{}-01'.format(self.month)
            next_month = '{}-01'.format(self.next_month_str(self.month))
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
        next_month = self.next_month_str(self.month)

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
        previous_month = self.previous_month_str(self.month)

        if (previous_month, previous_month) in month_selection:
            self.write({'month': previous_month})
            self.month_change()
        return True

    @api.model
    def get_domain(self, report_id):
        report = self.browse(report_id)
        domain = []
        if report.project_ids:
            domain.append(('project_id', 'in', report.project_ids._ids))

        if report.employee_ids:
            domain.append(('employee_id', 'in', report.employee_ids._ids))

        if report.company_ids:
            domain.append(('company_id', 'in', report.company_ids._ids))

        if report.site_ids:
            domain.append(('site_id', 'in', report.site_ids._ids))

        if report.date_from:
            domain.append(('date', '>=', report.date_from))

        if report.date_to:
            domain.append(('date', '<=', report.date_to))

        if report.billable:
            domain.append(('billable', '=', report.billable))

        if report.ot == 'ot':
            domain.append(('ot', '=', True))

        if report.ot == 'not_ot':
            domain.append(('ot', '=', False))
        return domain

    @api.model
    def get_allocate_resource_widget_data(self, report_id):
        if not report_id:
            return {}

        report = self.browse(report_id)
        domain = self.get_domain(report_id)

        project_id = report.project_ids and report.project_ids._ids[0] or False

        res = self.env['project.project'].get_allocate_resource_widget_data(
            report.date_from, report.date_to,
            domain=domain,
            user_groupby=report.group_by_project and 'project_id' or False,
            show_detail=report.show_detail,
            project_id=project_id
        )

        if not res:
            return res

        editable = False

        if report.group_by_project or len(report.project_ids) == 1:
            editable = True

        res['groupby'] = report.group_by_project and 'project_id' or False
        res['groupby_label'] = report.group_by_project and ['Project', 'Employee'] or ['Employee']
        res['group_by_project'] = report.group_by_project
        res['editable'] = editable
        res['ot'] = report.ot or 'all'

        return res

    @api.model
    def get_allocate_resource_group_widget_data(self, report_id):
        if not report_id:
            return {}

        report = self.browse(report_id)
        domain = self.get_domain(report_id)

        group_by = ['employee_id']
        if report.group_by == 'project_employee':
            group_by = ['project_id']
        return self.env['project.project'
        ].get_allocate_resource_group_widget_data(
            report.date_from, report.date_to, domain, group_by)

    @api.model
    def create_allocate(self, info):
        vals = {
            'project_id': info['project_id'],
            'employee_id': info['employee_id'],
            'date': info['date'],
            'percent': info['percent'],
            'billable': int(info['billable']) and 'billable' or 'none'
        }
        allocate_id = self.env['allocate.resource'].create(vals)
        return allocate_id

    @api.model
    def edit_allocate(self, info):
        billable = int(info['billable']) and 'billable' or 'none'
        percent = info['percent']

        str_line_ids = info['line_ids']
        line_ids = [int(line_id) for line_id in str_line_ids.split(',')]
        allocate_resources = self.env['allocate.resource'].browse(line_ids)

        remaining = percent

        for allocate_resource in allocate_resources:
            if not remaining:
                allocate_resource.unlink()
                continue
            write_percent = remaining
            remaining -= write_percent

            allocate_resource.write({
                'percent': write_percent,
                'billable': billable,
            })

        return True

    @api.model
    def delete_allocate(self, info):
        str_line_ids = info['line_ids']
        line_ids = [int(line_id) for line_id in str_line_ids.split(',')]
        allocate_resources = self.env['allocate.resource'].browse(line_ids)
        allocate_resources.unlink()
        return True

    @api.model
    def save(self, report_id, edit_info):
        for info in edit_info:
            info['project_id'] = int(info['project_id'])
            info['employee_id'] = int(info['employee_id'])
            info['percent'] = int(info['percent'] or '0')

            if not info['line_ids']:
                # not line_ids and percent = 0
                if not info['percent']:
                    continue
                # not line_ids and percent > 0
                else:
                    self.create_allocate(info)

            else:
                # has line_ids and percent > 0
                if info['percent']:
                    self.edit_allocate(info)
                # has line_ids and percent = 0
                else:
                    self.delete_allocate(info)
        return True

    @api.onchange('date_from', 'date_to')
    def onchange_name(self):
        if not self.date_from or not self.date_to:
            return
        name = 'Allocate resource from {} to {}'.format(self.date_from, self.date_to)
        self.name = name

