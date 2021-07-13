from odoo import fields, models, api
from datetime import datetime, timedelta


class HrContractLeave(models.Model):
    _name = 'hr.contract.leave'
    _description = 'Link leave already create by contract'
    _rec_name = 'year'

    contract_id = fields.Many2one('hr.contract')
    leave = fields.Float()
    leave_trial = fields.Float()
    year = fields.Integer()


class HrContract(models.Model):
    _inherit = 'hr.contract'

    allocation_leave = fields.Boolean(default=False)
    leaves_contract = fields.One2many('hr.contract.leave', 'contract_id')
    gen_leave = fields.Boolean(default=False, copy=False)

    def cron_gen_auto_legal_leave(self):
        contracts = self.env['hr.contract'].search([('state', 'in', ['draft', 'open', 'pending', 'close'])])
        for contract in contracts:
            contract.gen_auto_legal_leave()

    def gen_auto_legal_leave(self):
        """
        check leave by contract, create new if not exist
        skip if exist
        :return:
        """
        current_year = datetime.today().year
        exist = self.check_legal_leave(current_year)
        if not exist:
            self.gen_legal_leave(current_year)
        return

    def check_legal_leave(self, current_year):
        """
        check legal allocation with current contract
        :return: True if exist
                False if not exist
        """
        date_end = datetime.strptime('{}-12-31'.format(current_year), '%Y-%m-%d')
        date_start = datetime.strptime('{}-01-01'.format(current_year), '%Y-%m-%d')
        allocation = self.env['hr.leave.allocation'].search([
            ('holiday_type', '=', 'employee'),
            ('employee_id', '=', self.employee_id.id),
            ('holiday_status_id.code', '=', 'legal'),
            ('holiday_status_id.validity_start', '<=', date_start),
            ('holiday_status_id.validity_stop', '>=', date_end),
            ('state', '=', 'validate'),
            ('contract_id', '=', self.id)
        ])
        if allocation:
            return True
        return False

    def gen_legal_leave(self, current_year):
        """
        generate legal leave
        :return: allcation created
        """
        leave_origin = self.check_gen_leave_origin(current_year)
        frt_mon = datetime.strptime('{}-01-01'.format(current_year), '%Y-%m-%d')
        lst_mon = datetime.strptime('{}-12-31'.format(current_year), '%Y-%m-%d')
        if self.date_end and self.date_end < frt_mon.date():
            return
        if frt_mon.date() <= self.date_start:
            date_start = self.date_start
        else:
            date_start = frt_mon.date()

        if self.date_end and lst_mon.date() >= self.date_end:
            date_end = self.date_end
        else:
            date_end = lst_mon.date()

        current_legal = self.env['hr.leave.type'].search([
            ('code', '=', 'legal'),
            ('allocation_type', '=', 'fixed'),
            ('validity_start', '=', '{}-01-01'.format(current_year)),
            ('validity_stop', '=', '{}-12-31'.format(current_year)),
        ], limit=1)

        list_mons = self.get_list_mon([datetime.strftime(date_start, '%Y-%m-%d'),
                                        datetime.strftime(date_end, '%Y-%m-%d')])
        legal_leave = self.calculate_leave_by_contract(self, list_mons, current_year, current_legal)
        current_leave = legal_leave + leave_origin
        res = self.create_allocation_leave(current_leave, current_legal)
        contract_leaves = self.check_create_contract_leaves(legal_leave, leave_origin, current_year)
        self.gen_leave = True
        return res

    def check_gen_leave_origin(self, current_year):
        leave = 0
        if not self.parent_contract:
            return leave
        if self.parent_contract.type_id.code != 'trial':
            return leave
        if self.parent_contract.allocation_leave:
            return leave
        date_start = datetime.strftime(self.parent_contract.date_start, '%Y-%m-%d')
        date_end = datetime.strftime(self.parent_contract.date_end, '%Y-%m-%d')
        list_mons = self.get_list_mon([date_start, date_end])
        leave = self.calculate_leave_by_contract_trial(self.parent_contract, list_mons, current_year)
        self.parent_contract.allocation_leave = True
        return leave

    def get_list_mon(self, dates):
        """
        convert date end, date end to list of month
        :param dates: list date start, date end
        :return: list of month format %Y-%m
        """
        start, end = [datetime.strptime(_, "%Y-%m-%d") for _ in dates]
        total_months = lambda dt: dt.month + 12 * dt.year
        mlist = []
        for tot_m in range(total_months(start) - 1, total_months(end)):
            y, m = divmod(tot_m, 12)
            mlist.append(datetime(y, m + 1, 1).strftime("%Y-%m"))
        return mlist

    def create_allocation_leave(self, leave, current_legal):
        """
        create allocation legal
        :param leave: number of leave legal
        :param year: current allocation
        :return: allocation created
        """
        if leave == 0:
            return
        allocation_val = {
            'name': 'Allocation of Legal for employee {}'.format(self.employee_id.name),
            'holiday_status_id': current_legal.id,
            'number_of_days': leave,
            'holiday_type': 'employee',
            'employee_id': self.employee_id.id,
            'notes': 'contract: {}'.format(self.name),
            'contract_id': self.id,
        }
        allocation = self.env['hr.leave.allocation'].create(allocation_val)
        allocation.action_approve()
        return allocation

    def calculate_leave_by_contract(self, contract, list_mons, year, current_legal):
        """
        function calculate legal leave day by contract
        :param contract: contract calculate leave
        :param list_mons: list month of contract
        :param year: current year allocation legal leave
        :return: number of leave days, list month generate
        """
        previous_mons = self.check_previous_allocation(year, self.employee_id.id, current_legal)
        leave = 0
        c_start_date = contract.date_start.day
        date_end = datetime.strptime('{}-12-31'.format(year), '%Y-%m-%d')
        c_end_date = date_end.day
        if contract.date_end:
            date_end = contract.date_end
            c_end_date = contract.date_end.day

        mon_start = datetime.strftime(contract.date_start, '%Y-%m')
        mon_end = datetime.strftime(date_end, '%Y-%m')
        for mon in list_mons:
            mon_ = mon.split('-')
            y, m = int(mon_[0]), int(mon_[1])
            if y != year:
                continue
            elif mon in previous_mons[1:-1]:
                continue
            elif mon == mon_start:
                if c_start_date <= 7:
                    leave += 1
                elif c_start_date < 20:
                    leave += 0.5
            elif mon == mon_end:
                if c_end_date >= 20:
                    leave += 1
                elif c_end_date > 7:
                    leave += 0.5
            else:
                leave += 1
        return leave

    def calculate_leave_by_contract_trial(self, contract, list_mons, year):
        """
        calculated number days of legal leave by trial contract
        :param contract: trial contract
        :param list_mons: list of month offical contract
        :param year: current year
        :return: number of leave days
        """
        leave = 0
        c_start_date = contract.date_start.day
        date_end = datetime.strptime('{}-12-31'.format(year), '%Y-%m-%d')
        c_end_date = date_end.day
        c_end_year = date_end.year
        if contract.date_end:
            date_end = contract.date_end
            c_end_date = contract.date_end.day
            c_end_year = contract.date_end.year
        mon_start = datetime.strftime(contract.date_start, '%Y-%m')
        mon_end = datetime.strftime(date_end, '%Y-%m')
        previous_mon = '{}-12'.format(year-1)
        if c_end_year == year:
            for mon in list_mons:
                if mon == mon_start:
                    if c_start_date <= 7:
                        leave += 1
                    elif c_start_date < 20:
                        leave += 0.5
                elif mon == mon_end:
                    if c_end_date >= 20:
                        leave += 1
                    elif c_end_date >= 7:
                        leave += 0.5
                else:
                    leave += 1
        elif mon_end == previous_mon:
            if c_end_date < 30:
                return leave

            for mon in list_mons:
                if mon == mon_start:
                    if c_start_date <= 7:
                        leave += 1
                    elif c_start_date < 20:
                        leave += 0.5
                elif mon == mon_end:
                    if c_end_date >= 20:
                        leave += 1
                    elif c_end_date >= 7:
                        leave += 0.5
                else:
                    leave += 1
        return leave

    def check_create_contract_leaves(self, leave, leave_trial, year):
        if self.is_origin_contract:
            contract_id = self.id
        else:
            contract_id = self.parent_contract.id
        check_leave = self.env['hr.contract.leave'].search([('contract_id', '=', contract_id), ('year', '=', year)])
        if check_leave and check_leave.leave >= 12:
            return False
        leaves = self.create_contract_leaves(leave, leave_trial, year, contract_id)
        return leaves

    def create_contract_leaves(self, leave, leave_trial, year, contract_id):
        check_leave = self.env['hr.contract.leave'].search([('contract_id', '=', contract_id), ('year', '=', year)])
        if not check_leave:
            leave_contact = self.env['hr.contract.leave'].create({
                'year': year,
                'leave': leave,
                'leave_trial': leave_trial,
                'contract_id': contract_id
            })
            return leave_contact
        new_leave = check_leave.leave + leave
        new_trial = check_leave.leave_trial + leave_trial
        check_leave.write({'check_leave': new_leave, 'leave_trial': new_trial})
        return check_leave

    def check_previous_allocation(self, year, employee_id, current_legal):
        previous_allocations = self.env['hr.leave.allocation'].search([
            ('holiday_type', '=', 'employee'),
            ('holiday_status_id.validity_start', '=', '{}-01-01'.format(year)),
            ('holiday_status_id.validity_stop', '=', '{}-12-31'.format(year)),
            ('state', '=', 'validate'),
            ('holiday_status_id', '=', current_legal.id),
            ('employee_id', '=', employee_id),
        ])
        previous_mon = []
        for pre_all in previous_allocations:
            if not pre_all.contract_id:
                continue
            pre_start = datetime.strftime(pre_all.contract_id.date_start, '%Y-%m-%d')
            date_end = datetime.strptime('{}-12-31'.format(year), '%Y-%m-%d')
            if pre_all.contract_id.date_end:
                date_end = pre_all.contract_id.date_end
            pre_end = datetime.strftime(date_end, '%Y-%m-%d')
            mons = self.get_list_mon([pre_start, pre_end])
            previous_mon.extend(mons)
        previous_mon = list(set(previous_mon))
        previous_mon.sort()
        return previous_mon

    @api.onchange('parent_contract', 'type_id')
    def onchange_date_start(self):
        if not self.parent_contract:
            return
        next_date = self.parent_contract.date_end + timedelta(days=1)
        self.date_start = next_date
        return
