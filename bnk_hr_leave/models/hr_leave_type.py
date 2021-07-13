from odoo import fields, models, api
from datetime import datetime
from copy import deepcopy


class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'
    _description = 'Inherit leave type'

    def cron_create_leave_type(self):
        year = datetime.today().year
        start_date = '{}-01-01'.format(year)
        end_date = '{}-12-31'.format(year)
        domain = [('validity_start', '=', start_date), ('validity_stop', '=', end_date)]
        self.create_legal_type(domain, start_date, end_date, year)
        self.create_unpaid_type(domain, start_date, end_date, year)
        self.create_holiday_type(domain, start_date, end_date, year)
        self.create_sick_type(domain, start_date, end_date, year)

    def create_legal_type(self, domain, start_date, end_date, year):
        domain_ex = deepcopy(domain)
        domain_ex.append(('code', '=', 'legal'))
        check_exist = self.env['hr.leave.type'].search(domain_ex)
        if check_exist:
            return
        self.env['hr.leave.type'].create({
            'code': 'legal',
            'validity_start': start_date,
            'validity_stop': end_date,
            'name':  'Legal Leaves {}'.format(year),
            'allocation_type': 'fixed',
            'unpaid': False,
        })

    def create_unpaid_type(self, domain, start_date, end_date, year):
        domain_ex = deepcopy(domain)
        domain_ex.append(('code', '=', 'unpaid'))
        check_exist = self.env['hr.leave.type'].search(domain_ex)
        if check_exist:
            return
        self.env['hr.leave.type'].create({
            'code': 'unpaid',
            'validity_start': start_date,
            'validity_stop': end_date,
            'name': 'Unpaid Days {}'.format(year),
            'allocation_type': 'no',
            'unpaid': True,
        })

    def create_holiday_type(self, domain, start_date, end_date, year):
        domain_ex = deepcopy(domain)
        domain_ex.append(('code', '=', 'annual'))
        check_exist = self.env['hr.leave.type'].search(domain_ex)
        if check_exist:
            return
        self.env['hr.leave.type'].create({
            'code': 'annual',
            'validity_start': start_date,
            'validity_stop': end_date,
            'name':  'Holidays {}'.format(year),
            'allocation_type': 'fixed',
            'unpaid': False,
        })

    def create_sick_type(self, domain, start_date, end_date, year):
        domain_ex = deepcopy(domain)
        domain_ex.append(('code', '=', 'sick'))
        check_exist = self.env['hr.leave.type'].search(domain_ex)
        if check_exist:
            return
        self.env['hr.leave.type'].create({
            'code': 'sick',
            'validity_start': start_date,
            'validity_stop': end_date,
            'name': 'Sick Days {}'.format(year),
            'allocation_type': 'no',
            'unpaid': True,
        })
