# -*- coding:utf-8 -*-
from datetime import date, datetime, time, timedelta
from pytz import timezone
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from calendar import monthrange, month_name


class HrPayslipExtend(models.Model):
    _inherit = 'hr.payslip'

    bank_account_id = fields.Many2one('res.partner.bank')
    personal_tax_number = fields.Char()
    month = fields.Many2one('hr.payroll.month', compute='cp_mon_period', store=True)
    department_id = fields.Many2one('hr.department')
    has_insurance = fields.Boolean('Insurance')
    check_ins = fields.Boolean('Check insurance')
    mon_str = fields.Char(related='month.name', store=True, string='Month')
    work100 = fields.Float(string='Normal Working Day')
    deduction = fields.Float('Deduction')
    reimburse = fields.Float('Reimburse')
    mon_allowance = fields.Float('Month Allowance')
    mon_bonus = fields.Float('Month Bonus')
    payslip_summary_ids = fields.One2many('hr.payslip.summary', 'payslip_id')
    allowance_contract = fields.Float(compute='cp_allowance_contract', store=True)
    allowance_contract_tax = fields.Float(compute='cp_allowance_contract', store=True)
    site_id = fields.Many2one(string='Location (Site)')
    is_new_employee = fields.Selection([('new', 'New Employee'), ('normal', 'Normal Employee'),
                                        ('resign', 'Resign Employee')],
                                       compute='cp_new_employee', store=True)
    contract_type = fields.Selection([('official', 'Official'), ('trial', 'Trial'), ('contributor', 'Contributor'),
                                      ('other', 'Other')], compute='cp_contract_type', store=True)
    adjustment_manual = fields.Float('Adjustment Manual')

    @api.depends('employee_id')
    def cp_new_employee(self):
        for p in self:
            if not p.employee_id.payslip_ids:
                p.is_new_employee = 'new'
                continue
            payslips = p.employee_id.payslip_ids.filtered(lambda p: p.state != 'cancel')
            if not payslips:
                p.is_new_employee = 'new'
                continue
            if len(payslips) == 1:
                if p.employee_id.resigned_date and \
                        payslips[0].date_from <= p.employee_id.resigned_date <= payslips[0].date_to:
                    p.is_new_employee = 'resign'
                    continue
                p.is_new_employee = 'new'
                continue
            if not p.employee_id.resigned_date:
                p.is_new_employee = 'normal'
                continue
            resign = payslips.filtered(lambda p: p.date_from <= p.employee_id.resigned_date <= p.date_to)
            if not resign:
                p.is_new_employee = 'normal'
                continue
            p.is_new_employee = 'resign'

    @api.depends('contract_id')
    def cp_contract_type(self):
        for p in self:
            if p.contract_id:
                p.contract_type = p.contract_id.type_id.code

    def action_send_email_payslip(self):
        mail_body = self.get_mail_body_payslip()
        template = self.get_mail_message_payslip()
        template.update({
            'body_html': mail_body,
        })
        mail = self.env['mail.mail'].create(template)
        return mail

    def get_mail_body_payslip(self):
        salary_amount = self.payslip_summary_ids.filtered(
            lambda x: x.description.startswith('Salary (1)')).amount_payable
        overtime_salary = self.payslip_summary_ids.filtered(
            lambda x: x.description.startswith('Overtime salary')).amount_payable
        allowance_amount = self.payslip_summary_ids.filtered(
            lambda x: x.description.startswith('Allowance')).amount_payable
        meal_amount = self.payslip_summary_ids.filtered(lambda x: x.description.startswith('Meal')).amount_payable
        telephone_fee = self.payslip_summary_ids.filtered(
            lambda x: x.description.startswith('Telephone Fee')).amount_payable
        other_allowance = self.payslip_summary_ids.filtered(
            lambda x: x.description.startswith('Other allowance')).amount_payable
        total_income = self.payslip_summary_ids.filtered(
            lambda x: x.description.startswith('Total Income')).amount_payable
        deduction = self.payslip_summary_ids.filtered(lambda x: x.description.startswith('Deduction')).amount_payable
        insurances = self.payslip_summary_ids.filtered(
            lambda x: x.description.startswith('Insurances')).amount_payable
        personal_income = self.payslip_summary_ids.filtered(
            lambda x: x.description.startswith('Personal income tax')).amount_payable
        salary_day_off = self.payslip_summary_ids.filtered(
            lambda x: x.description.startswith('Salary for day off')).amount_payable
        other_deduction = self.payslip_summary_ids.filtered(
            lambda x: x.description.startswith('Other deduction')).amount_payable
        net_income = self.payslip_summary_ids.filtered(
            lambda x: x.description.startswith('Net Income')).amount_payable
        month = month_name[self.date_from.month]
        month_year = month + '-' + str(self.date_from.year)
        actual_day = self.get_actual_workday()

        body = '''
                    <div style="margin: 0px; padding: 0px;">
                        <br/>
                        <p style="text-align: center; font-weight: bold; font-size: 22px;
                        ">Salary for period of {month_year}</p>
                        <div style="font-size: 15px;">
                            <p><strong>Employee full name:</strong> {employee_id}</p>
                            <p><strong>Department:</strong> {department_id}</p>
                            <p><strong>Job Position:</strong> {job_id}</p>
                            <p><strong>Salary:</strong> {salary_amount} VND</p>
                            <p><strong>Normal working days:</strong> {nor_working_day}</p>
                            <p><strong>Actual working days:</strong> {actual_day}</p>
                        </div>
                        <br/>
                    </div>
                    <table border="1" style="width: 100%; table-layout: fixed; border: none; border-color: gainsboro;"
                           class="o_list_table table table-sm table-hover table-striped o_list_table_ungrouped">
                        <thead style="background-color: #e9ecef;">
                            <tr>
                                <th style="text-align: center; width: 10%;">No.</th>
                                <th style="text-align: center;">Description</th>
                                <th style="text-align: center;">Amount Payable</th>
                                <th style="text-align: center;">Notes</th>
                            </tr>
                        </thead>
                        <tbody style="background-color:gainsboro;">
                            <tr>
                                <td style="font-weight: bold; text-align: center!important;">I</td>
                                <td style="text-align: left; font-weight: bold;">Salary (1)</td>
                                <td style="text-align: right; font-weight: bold;">{salary_amount}</td>
                                <td></td>
                            </tr>
                            <tr>
                                <td style="font-weight: bold; text-align: center!important;">II</td>
                                <td style="text-align: left; font-weight: bold;">Overtime salary (2)</t>
                                <td style="text-align: right; font-weight: bold;" >{overtime_salary}</td>
                                <td></td>
                            </tr>
                            <tr>
                                <td style="font-weight: bold; text-align: center!important;">III</td>
                                <td style="text-align: left; font-weight: bold;">Allowance (3)</td>
                                <td style="text-align: right; font-weight: bold;">{allowance_amount}</td>
                                <td></td>
                            </tr>
                            <tr>
                                <td></td>
                                <td style="text-align: left; font-style: italic;">Meal</td>
                                <td style="text-align: right;">{meal_amount}</td>
                                <td></td>
                            </tr>
                            <tr>
                                <td></td>
                                <td style="text-align: left; font-style: italic;">Telephone Fee</td>
                                <td style="text-align: right;">{telephone_fee}</td>
                                <td></td>
                            </tr>
                            <tr>
                                <td></td>
                                <td style="text-align: left; font-style: italic;">Other allowance</td>
                                <td style="text-align: right;">{other_allowance}</td>
                                <td></td>
                            </tr>
                            <tr>
                                <td style="font-weight: bold; text-align: center!important;">IV</td>
                                <td style="text-align: left; font-weight: bold;">Total Income(3=2+1)</td>
                                <td style="text-align: right; font-weight: bold;">{total_income}</td>
                                <td></td>
                            </tr>
                            <tr>
                                <td style="font-weight: bold; text-align: center!important;">V</td>
                                <td style="text-align: left; font-weight: bold;">Deduction(4)</td>
                                <td style="text-align: right; font-weight: bold;">{deduction}</td>
                                <td></td>
                            </tr>
                            <tr>
                                <td></td>
                                <td style="text-align: left;  font-style: italic;">Insurances (10.5%)</td>
                                <td style="text-align: right;">{insurances}</td>
                                <td></td>
                            </tr>
                            <tr>
                                <td></td>
                                <td style="text-align: left; font-style: italic;">Personal income tax</td>
                                <td style="text-align: right;">{personal_income}</td>
                                <td></td>
                            </tr>
                            <tr>
                                <td></td>
                                <td style="text-align: left; font-style: italic;">Salary for day off</td>
                                <td style="text-align: right;">{salary_day_off}</td>
                                <td></td>
                            </tr>
                            <tr>
                                <td></td>
                                <td style="text-align: left; font-style: italic;">Other deduction</td>
                                <td style="text-align: right;">{other_deduction}</td>
                                <td></td>
                            </tr>
                            <tr>
                                <td style="font-weight: bold; text-align: center!important;">VI</td>
                                <td style="text-align: left; font-weight: bold;">Net Income(5=3-4)</td>
                                <td style="text-align: right; font-weight: bold;">{net_income}</td>
                                <td></td>
                            </tr>
                        </tbody>
                    </table>
            '''.format(salary_amount="{:,.2f}".format(salary_amount),
                       allowance_amount="{:,.2f}".format(allowance_amount),
                       meal_amount="{:,.2f}".format(meal_amount), overtime_salary="{:,.2f}".format(overtime_salary),
                       telephone_fee="{:,.2f}".format(telephone_fee), other_allowance="{:,.2f}".format(other_allowance),
                       total_income="{:,.2f}".format(total_income), deduction="{:,.2f}".format(deduction),
                       insurances="{:,.2f}".format(insurances), personal_income="{:,.2f}".format(personal_income),
                       salary_day_off="{:,.2f}".format(salary_day_off),
                       other_deduction="{:,.2f}".format(other_deduction),
                       net_income="{:,.2f}".format(net_income), employee_id=self.employee_id.name,
                       department_id=self.department_id.name or '', job_id=self.employee_id.job_id.name or '',
                       nor_working_day=self.work100, month_year=month_year, actual_day=actual_day
                       )
        return body

    def get_mail_message_payslip(self):
        mail_values = {
            'author_id': False,
            'body_html': '',
            'subject': 'Payslip of {}'.format(self.employee_id.name),
            'email_to': self.employee_id.work_email,
            'auto_delete': True,
        }
        return mail_values

    @api.depends('contract_id')
    def cp_allowance_contract(self):
        for pay in self:
            if not pay.contract_id:
                pay.allowance_contract = 0
                pay.allowance_contract_tax = 0
                continue
            allowance_tax, allowance = pay._get_allowance_from_contract(pay.contract_id)
            pay.allowance_contract = allowance
            pay.allowance_contract_tax = allowance_tax

    def _get_allowance_from_contract(self, contract):
        allowance_tax = 0
        allowance = 0

        actual_day = self.get_actual_workday()
        workday = self.work100 or self.get_normal_workdays(contract)

        # Meal
        if contract.is_eat_inc:
            allowance_tax += contract.eat_inc / workday * actual_day
        else:
            allowance += contract.eat_inc / workday * actual_day
        # Phone
        if contract.is_phone_inc:
            allowance_tax += contract.phone_inc / workday * actual_day
        else:
            allowance += contract.phone_inc / workday * actual_day
        # Travel
        if contract.is_work_allo_inc:
            allowance_tax += contract.work_allo_inc / workday * actual_day
        else:
            allowance += contract.work_allo_inc / workday * actual_day
        # Position
        if contract.is_poison_inc:
            allowance_tax += contract.poison_inc / workday * actual_day
        else:
            allowance += contract.poison_inc / workday * actual_day
        # Insurance benefit
        if contract.is_ins_inc:
            allowance_tax += contract.ins_inc / workday * actual_day
        else:
            allowance += contract.ins_inc / workday * actual_day
        # Uniform
        if contract.is_uni_inc:
            allowance_tax += (contract.uni_inc / 12) / workday * actual_day
        else:
            allowance += (contract.uni_inc / 12) / workday * actual_day

        allowance = allowance
        allowance_tax = allowance_tax

        return allowance_tax, allowance

    @api.multi
    def compute_sheet(self):
        for payslip in self:
            payslip.onchange_employee()
            # payslip.generate_payslip_summary()
        res = super(HrPayslipExtend, self).compute_sheet()
        self.generate_payslip_summary()
        return res

    @api.onchange('employee_id', 'date_from', 'date_to', 'contract_id')
    def onchange_employee(self):
        if not self.employee_id:
            return
        old_input = self.get_old_input()
        res = super().onchange_employee()
        date_from_str = datetime.strftime(self.date_from, '%Y-%m-%d')
        date_to_str = datetime.strftime(self.date_to, '%Y-%m-%d')
        contracts = self.get_all_contract(self.employee_id, self.date_from, self.date_to)
        if not contracts:
            self.contract_id = False
            self.worked_days_line_ids = False
            return
        adjustment = self.get_salary_adjustment()
        if adjustment:
            self.set_salary_adjustment(adjustment)

        normal_workdays = self.get_normal_workdays(contracts[0])
        self.work100 = normal_workdays
        workday = self.get_worked_day_holiday(contracts)
        if self.contract_id.type_id.code != 'contributor':
            new_worked_days = self.calculate_worked_day(workday['worked'], workday['holiday'], workday['ot'])
        else:
            new_worked_days = self.calculate_worked_day_contributor(contracts, date_from_str, date_to_str)

        # check_allowance = self.env['hr.allowance.line'].search([
        #     ('date_from', '>=', date_from_str), ('date_to', '<=', date_to_str),
        #     ('state', '=', 'validated'), ('employee_id', '=', self.employee_id.id)])
        input_lines = self.get_input_lines(old_input, contracts, date_from_str, date_to_str)

        if not new_worked_days:
            self.worked_days_line_ids.unlink()
        else:
            self.worked_days_line_ids = new_worked_days

        # self.input_line_ids = input_lines
        # origin = getattr(self, '_origin', False)
        # if not origin:
        #     return res
        # if self._origin.employee_id.id != self.employee_id.id:
        #     return res
        # input_code = [i.code for i in self.input_line_ids]
        # for inp in old_input:
        #     if inp['code'] in input_code:
        #         continue
        #     self.env['hr.payslip.input'].create(inp)
        # return

    def check_overlap_payslip(self, id, from_date, to_date, employee):
        domain = [('state', '!=', 'cancel'), ('employee_id', '=', employee.id)]
        if id:
            domain.append(('id', '!=', id))
        domain1 = [('date_from', '>=', from_date), ('date_to', '<=', to_date)]
        domain2 = [('date_from', '<=', from_date), ('date_to', '>=', to_date)]
        domain3 = [('date_from', '<=', from_date), ('date_to', '>=', from_date), ('date_to', '<=', to_date)]
        domain4 = [('date_from', '>=', from_date), ('date_from', '<=', to_date), ('date_to', '>=', to_date)]
        exist_payslip1 = self.env['hr.payslip'].search(domain + domain1)
        exist_payslip2 = self.env['hr.payslip'].search(domain + domain2)
        exist_payslip3 = self.env['hr.payslip'].search(domain + domain3)
        exist_payslip4 = self.env['hr.payslip'].search(domain + domain4)
        if exist_payslip1 or exist_payslip2 or exist_payslip3 or exist_payslip4:
            return True
        return False

    @api.constrains('date_from', 'date_to', 'employee_id')
    def constrains_overlap_payslip(self):
        if self._context.get('from_batch') or self._context.get('refund'):
            return
        for rec in self:
            id = rec.id
            date_from = rec.date_from
            date_to = rec.date_to
            employee = rec.employee_id
            result = rec.check_overlap_payslip(id, date_from, date_to, employee)
            if result:
                raise ValidationError(_("Duplicate payslip"))
            if rec.employee_id.is_trial_15:
                raise ValidationError(_("Cannot create payslip for trial employee work under 15 days!"))

    def refund_sheet(self):
        self = self.with_context(refund=True)
        res = super(HrPayslipExtend, self).refund_sheet()
        return res

    def get_old_input(self):
        inputs = []
        if self.input_line_ids:
            for ip in self.input_line_ids:
                inputs.append({
                    'name': ip.name, 'display_name': ip.display_name,
                    'contract_id': ip.contract_id.id,
                    'payslip_id': ip.payslip_id.id,
                    'amount': ip.amount,
                    'sequence': ip.sequence,
                    'code': ip.code,
                })
        return inputs

    def get_all_contract(self, employee, date_from, date_to):
        contract_ids = self.get_contract(employee, date_from, date_to)
        if not contract_ids:
            return []
        contracts = self.env['hr.contract'].browse(contract_ids)
        return contracts

    def get_normal_workdays(self, contract):
        first_date = self.date_from.replace(day=1)
        last_date = self.date_to.replace(day=monthrange(self.date_to.year, self.date_to.month)[1])
        w100 = self.get_worked_day_lines(contract, first_date, last_date)
        total = sum([w['number_of_days'] for w in w100])
        return total

    def get_worked_day_holiday(self, contracts):
        worked_days_line_ids = []
        public_holiday_dct = {}
        ot_dct = {}
        for contract in contracts:
            if contract.date_start > self.date_from:
                contract_date_from = contract.date_start
            else:
                contract_date_from = self.date_from
            if contract.date_end and contract.date_end < self.date_to:
                contract_date_to = contract.date_end
            else:
                contract_date_to = self.date_to
            worked_days_line_ids += self.get_worked_day_lines(contract, contract_date_from, contract_date_to)
            public_holiday = self.env['public.holiday.line'].search(
                [('state', '=', 'approved'), ('date', '>=', contract_date_from),
                 ('date', '<=', contract_date_to)])
            public_holiday_day = len(public_holiday)
            public_holiday_dct[contract.id] = public_holiday_day

            ots = self.get_ot(contract_date_from, contract_date_to, self.employee_id.id)
            if ots:
                ot_dct[contract.id] = ots
        return {'worked': worked_days_line_ids, 'holiday': public_holiday_dct, 'ot': ot_dct}

    def calculate_worked_day(self, worked_days_line_ids, public_holiday_dct, ot_dct):
        contract_code = 1
        contract_dct = {}
        contract_lst = []
        worked_days_lines = self.worked_days_line_ids.browse([])
        for c in worked_days_line_ids:
            if c['contract_id'] not in contract_lst:
                contract_lst.append(c['contract_id'])
                contract_dct[c['contract_id']] = contract_code
                contract_code += 1
        work_line = {}
        for r in worked_days_line_ids:
            if r.get('code', False):
                if r['code'] == 'WORK100':
                    if r['contract_id'] in public_holiday_dct.keys():
                        r['number_of_days'] = r['number_of_days'] - public_holiday_dct[r['contract_id']]
                    r['number_of_hours'] = r['number_of_days'] * 8
                    r['name'] = 'Normal Working Days'
                    r['code'] = r['code'] + '_HD{}'.format(contract_dct[r['contract_id']])
                elif r['code'].startswith('Unpaid') or r['code'].startswith('unpaid'):
                    r['code'] = 'UNPAID' + '_HD{}'.format(contract_dct[r['contract_id']])
                elif r['code'].startswith('Sick') or r['code'].startswith('sick'):
                    r['code'] = 'SICK' + '_HD{}'.format(contract_dct[r['contract_id']])
                elif r['code'].startswith('Legal') or r['code'].startswith('legal'):
                    r['code'] = 'LEGAL' + '_HD{}'.format(contract_dct[r['contract_id']])

            if r['code'] not in work_line.keys():
                work_line[r['code']] = r['number_of_days']
            else:
                work_line[r['code']] = work_line[r['code']] + r['number_of_days']

        new_worked_days_line_ids = worked_days_line_ids
        for new_r in new_worked_days_line_ids:
            worked_days_lines += worked_days_lines.new(new_r)
        for key in public_holiday_dct.keys():
            if public_holiday_dct[key] == 0:
                continue
            public_holiday_dict = {
                'name': 'Public Holiday',
                'sequence': 10,
                'code': 'PUBLIC_HD{}'.format(contract_dct[key]),
                'number_of_days': public_holiday_dct[key],
                'number_of_hours': public_holiday_dct[key] * 8,
                'contract_id': key}
            worked_days_lines += worked_days_lines.new(public_holiday_dict)
        for key in ot_dct.keys():
            for key_child in list(ot_dct[key].keys()):
                if key_child == 'otn':
                    txt = 'Normal Day'
                    code = 'N'
                elif key_child == 'otw':
                    txt = 'Weekend'
                    code = 'WK'
                else:
                    txt = 'Holiday'
                    code = 'H'
                if ot_dct[key][key_child] == 0:
                    continue
                ot_ = {
                    'name': 'OverTime {}'.format(txt),
                    'sequence': 15,
                    'code': 'OT{}_HD{}'.format(code, contract_dct[key]),
                    'number_of_days': ot_dct[key][key_child] / 8,
                    'number_of_hours': ot_dct[key][key_child],
                    'contract_id': key
                }
                worked_days_lines += worked_days_lines.new(ot_)
        resign = self.check_resigned_date()
        if not resign:
            return worked_days_lines
        if 'leave' in resign.keys():
            worked_days_lines += worked_days_lines.new(resign['leave'])
        # elif 'trial' in resign.keys():
        #     worked_days_lines = False
        return worked_days_lines

    def calculate_worked_day_contributor(self, contracts, date_from_str, date_to_str):
        work_hour = self.env['hr.contributor.line'].search([('employee_id', '=', self.employee_id.id),
                                                            ('state', '=', 'validated'),
                                                            ('date_from', '>=', date_from_str),
                                                            ('date_to', '<=', date_to_str)])

        contract_ids = contracts.ids
        worked_days_lines = self.worked_days_line_ids.browse([])
        hours = 0
        if work_hour:
            hours = work_hour[0].hour_of_month
        vals_dct = {
            'name': 'Worked',
            'sequence': 11,
            'code': 'CTV',
            'number_of_days': hours / 8,
            'number_of_hours': hours,
            'contract_id': contract_ids[0]}
        worked_days_lines += worked_days_lines.new(vals_dct)
        return worked_days_lines

    def get_input_lines(self, inputs, contracts, date_from_str, date_to_str):
        input_line_ids = self.get_inputs(contracts, date_from_str, date_to_str)
        input_lines = self.input_line_ids.browse([])
        contract_ids = contracts.ids
        for r in input_line_ids:
            input_lines += input_lines.new(r)
        alw_total = 0
        # if check_allowance:
        #     alw_total = check_allowance.total
        input_lines += input_lines.new({
            'name': 'Allowance',
            'contract_id': contract_ids[0],
            'amount': alw_total,
            'code': 'ALW'
        })
        oip_value = 0
        early_payment = 0
        balance = 0
        for i in inputs:
            if i['code'] == 'OIP':
                oip_value = i['amount']
            elif i['code'] == 'SEP':
                early_payment = i['amount']
            elif i['code'] == 'SBL':
                balance = i['amount']

        input_lines += input_lines.new({
            'name': 'Other Input',
            'contract_id': contract_ids[0],
            'amount': oip_value,
            'code': 'OIP'
        })
        input_lines += input_lines.new({
            'name': 'Reimburse',
            'contract_id': contract_ids[0],
            'amount': early_payment,
            'code': 'SEP'
        })
        input_lines += input_lines.new({
            'name': 'Deduction',
            'contract_id': contract_ids[0],
            'amount': balance,
            'code': 'SBL'
        })

        return input_lines

    @api.model
    def get_contract(self, employee, date_from, date_to):
        """
        @param employee: recordset of employee
        @param date_from: date field
        @param date_to: date field
        @return: returns the ids of all the contracts for the given employee that need to be considered for the given dates
        """
        # a contract is valid if it ends between the given dates
        clause_1 = ['&', ('date_end', '<=', date_to), ('date_end', '>=', date_from)]
        # OR if it starts between the given dates
        clause_2 = ['&', ('date_start', '<=', date_to), ('date_start', '>=', date_from)]
        # OR if it starts before the date_from and finish after the date_end (or never finish)
        clause_3 = ['&', ('date_start', '<=', date_from), '|', ('date_end', '=', False), ('date_end', '>=', date_to)]
        clause_final = [('employee_id', '=', employee.id), ('state', 'in', ['open', 'close', 'pending']), '|',
                        '|'] + clause_1 + clause_2 + clause_3
        return self.env['hr.contract'].search(clause_final).ids

    def onchange_has_insurance_multi(self):
        for pay in self:
            pay.onchange_has_insurance()

    @api.onchange('worked_days_line_ids', 'date_from', 'date_to')
    def onchange_has_insurance(self):
        if not self.contract_id:
            self.has_insurance = False
            return
        # check resigned contract
        if self.contract_id.type_id.code == 'official':
            if self.employee_id.resigned_date and self.date_from <= self.employee_id.resigned_date <= self.date_to and \
                    self.employee_id.resigned_date.day < 15:
                self.has_insurance = False
            elif self.date_from <= self.contract_id.date_start <= self.date_to and \
                    self.contract_id.date_start.day >= 15:
                self.has_insurance = False
            else:
                self.has_insurance = True
        else:
            self.has_insurance = False

    @api.depends('date_from')
    def cp_mon_period(self):
        for se in self:
            if not se.date_from:
                se.mon = False
                continue
            month = se.check_create_period()
            se.month = month.id

    def check_create_period(self):
        month_obj = self.env['hr.payroll.month']
        get_month = month_obj.search(
            [('year', '=', self.date_from.year), ('month', '=', str(self.date_from.month))])
        if get_month:
            return get_month

        new_mon = month_obj.create({
            'year': self.date_from.year, 'month': str(self.date_from.month)
        })
        return new_mon

    def get_ot(self, contract_date_from, contract_date_to, employee_id):
        return {}

    def get_ot_nor_rate(self):
        return 0

    def get_ot_wek_rate(self):
        return 0

    def get_ot_hol_rate(self):
        return 0

    @api.model
    def get_public_holiday(self, date_from, date_to):
        domain = [('date', '>=', date_from), ('date', '<=', date_to)]
        holidays = self.env['public.holiday.line'].search(domain)

        public_holiday_list = \
            [holiday.date.strftime('%Y-%m-%d') for holiday in holidays]
        return public_holiday_list

    @api.model
    def get_working_weekday(self, employee):
        resource_calendar_id = self.env['hr.employee'].browse(employee).resource_calendar_id
        if resource_calendar_id:
            working_dow_list = []
            for attendance in resource_calendar_id.attendance_ids:
                dayofweek = int(attendance.dayofweek)
                if dayofweek not in working_dow_list:
                    working_dow_list.append(dayofweek)
        else:
            working_dow_list = [0, 1, 2, 3, 4]
        return working_dow_list

    def get_min_day_insurance(self):
        day = self.env['ir.config_parameter'].sudo().get_param('bnk_hr.min_day_insurance')
        if float(day) < 1:
            day = 14
        else:
            day = float(day)
        return day

    def get_salary_adjustment(self):
        return False

    def set_salary_adjustment(self, adj):
        return True

    def check_resigned_date(self):
        if not self.employee_id.is_resign:
            return False
        if self.employee_id.state == 'wait_approved':
            return False
        if not self.employee_id.resigned_date:
            return False
        if self.date_from <= self.employee_id.resigned_date <= self.date_to:
            resign = self._check_resigned_date(self.employee_id.resigned_date)
            return resign
        else:
            return False

    def _check_resigned_date(self, resign_date):
        year = self.date_from.year
        first_date = '{}-{}-01'.format(year, '01')
        if self.contract_id.date_start > datetime.strptime(first_date, '%Y-%m-%d').date():
            first_date = datetime.strftime(self.contract_id.date_start, '%Y-%m-%d')
        over_legal = self.get_over_legal_leave(resign_date, first_date, year)
        return over_legal

    def get_over_legal_leave(self, resign_date, first_date, year):
        if self.contract_id.type_id.code == 'trial':
            if resign_date.day <= 10:
                return {'trial': True}
            return False
        legal_days = self.get_legal_day(resign_date, first_date)
        current_mon_legal = self.get_current_mon_legal_day(resign_date, first_date, year)
        if current_mon_legal - legal_days >= 0:
            return False
        over = legal_days - current_mon_legal
        leave = {
            'name': 'Leave over (deduction)',
            'sequence': 16,
            'code': 'OverLeave',
            'number_of_days': over,
            'number_of_hours': over * 8,
            'contract_id': self.contract_id.id,
        }
        return {'leave': leave}

    def get_legal_day(self, resign_date, first_date):
        resign_date_str = datetime.strftime(resign_date, '%Y-%m-%d')
        domain = [('employee_id', '=', self.employee_id.id),
                  ('state', '=', 'validate'),
                  ('request_date_from', '>=', first_date),
                  ('request_date_to', '<=', resign_date_str)
                  ]
        legal_domain = ['Paid', 'paid', 'PAID', 'LEGAL', 'legal', 'Legal']
        legal = self.env['hr.leave'].search(domain).\
            filtered(lambda x: x.holiday_status_id.code in legal_domain).mapped('number_of_days')
        legal = sum(legal)
        return legal

    def get_current_mon_legal_day(self, resign_date, first_date, year):
        list_mons = self.get_list_mon([first_date, datetime.strftime(resign_date, '%Y-%m-%d')])
        legal_leave = self.calculate_leave_by_contract(self.contract_id, list_mons, year)
        return legal_leave

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

    def calculate_leave_by_contract(self, contract, list_mons, year):
        """
        function calculate legal leave day by contract
        :param contract: contract calculate leave
        :param list_mons: list month of contract
        :param year: current year allocation legal leave
        :return: number of leave days, list month generate
        """
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
            elif mon == mon_start and mon == mon_end:
                if c_end_date - c_start_date >= 21:
                    leave += 1
                elif c_end_date - c_start_date >= 15:
                    leave += 0.5
            elif mon == mon_start:
                if c_start_date <= 10:
                    leave += 1
                elif c_start_date <= 20:
                    leave += 0.5
            elif mon == mon_end:
                if c_end_date > 20:
                    leave += 1
                elif c_end_date >= 10:
                    leave += 0.5
            else:
                leave += 1
        leave += self.calculate_leave_trial_contract()
        return leave

    def calculate_leave_trial_contract(self):
        current_contract_id = self.contract_id.id
        trials = self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id),
                                                 ('type_id.code', '=', 'trial'),
                                                 '|', ('child_contract_trial', '=', False),
                                                 ('child_contract_trial', '=', current_contract_id)])
        if not trials:
            return 0
        leave = 0
        for trial in trials:
            leave += self._calculate_leave_trial_contract(trial, self.date_from.year, current_contract_id)
        return leave

    def _calculate_leave_trial_contract(self, contract, year, current_contract_id):
        """
        calculated number days of legal leave by trial contract
        :param contract: trial contract
        :param year: current year
        :return: number of leave days
        """
        date_start = datetime.strftime(contract.date_start, '%Y-%m-%d')
        date_end = datetime.strftime(contract.date_end, '%Y-%m-%d')
        list_mons = self.get_list_mon([date_start, date_end])
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
        previous_mon = '{}-12'.format(year - 1)
        if c_end_year == year:
            for mon in list_mons:
                if mon == mon_start and mon == mon_end:
                    if c_end_date - c_start_date >= 21:
                        leave += 1
                    elif c_end_date - c_start_date >= 15:
                        leave += 0.5
                elif mon == mon_start:
                    if c_start_date <= 10:
                        leave += 1
                    elif c_start_date <= 20:
                        leave += 0.5
                elif mon == mon_end:
                    if c_end_date > 20:
                        leave += 1
                    elif c_end_date >= 10:
                        leave += 0.5
                else:
                    leave += 1
        elif mon_end == previous_mon:
            if c_end_date < 28:
                return leave

            for mon in list_mons:
                if mon == mon_start and mon == mon_end:
                    if c_end_date - c_start_date >= 21:
                        leave += 1
                    elif c_end_date - c_start_date >= 15:
                        leave += 0.5
                elif mon == mon_start:
                    if c_start_date <= 10:
                        leave += 1
                    elif c_start_date <= 20:
                        leave += 0.5
                elif mon == mon_end:
                    if c_end_date >= 20:
                        leave += 1
                    elif c_end_date >= 10:
                        leave += 0.5
                else:
                    leave += 1
        contract.child_contract_trial = current_contract_id
        return leave

    def generate_payslip_summary(self):
        summary = []
        for pay in self:
            if not pay.contract_id:
                continue
            pay_val = pay.prepare_summary_val()
            pay_summary = pay._generate_payslip_summary(pay_val)
            summary.append(pay_summary)
        return summary

    def prepare_summary_val(self):
        salary = self.contract_id.wage
        if self.contract_id.type_id.code == 'trial':
            salary = self.contract_id.wage * self.contract_id.salary_percent / 100
        elif self.contract_id.type_id.code == 'contributor':
            salary = self._get_hour_contributor() * self.contract_id.salary_per_hour
        allowance = self._get_other_allowance() + self._get_meal_income() + self._get_phone_income()
        insurance = self._get_insurance()
        pit = self._get_pit()
        dayoff = self._get_salary_timeoff()
        ot = self._get_salary_ot()
        total_income = salary + allowance + ot
        deduction = insurance + pit + dayoff + self._get_other_deduction()
        net_income = self._get_salary_net()
        temp_value = 0

        vals = []
        for i in range(1, 14):
            if i == 1:
                vals.append(self._prepare_summary_val(salary, 'I', 'Salary (1)', title=True))
            elif i == 2:
                vals.append(self._prepare_summary_val(ot, 'II', 'Overtime salary (2)', title=True))
            elif i == 3:
                vals.append(self._prepare_summary_val(allowance, 'III', 'Allowance (3)', title=True))
            elif i == 7:
                vals.append(self._prepare_summary_val(total_income, 'IV', 'Total Income (4=1+2+3)', title=True))
            elif i == 8:
                vals.append(self._prepare_summary_val(deduction, 'V', 'Deduction (5)', title=True))
            elif i == 13:
                vals.append(self._prepare_summary_val(net_income, 'VI', 'Net Income (6=4-5)', title=True))
            else:
                vals.append(self._prepare_summary_val(temp_value, '', '', title=False, count=i))
        return vals

    def _prepare_summary_val(self, amount, number, desc, title, note='', count=False, line=False):
        if count:
            line = True
            if count == 4:
                amount = self._get_meal_income()
                desc = 'Meal'
            elif count == 5:
                desc = 'Telephone Fee'
                amount = self._get_phone_income()
            elif count == 6:
                desc = 'Other allowance'
                amount = self._get_other_allowance()
            elif count == 9:
                desc = 'Insurances (10.5%)'
                amount = self._get_insurance()
            elif count == 10:
                desc = 'Personal income tax'
                amount = self._get_pit()
            elif count == 11:
                desc = 'Salary for dayoff'
                amount = self._get_salary_timeoff()
            elif count == 12:
                desc = 'Other deduction'
                amount = self._get_other_deduction()

        result = {
            'number': number,
            'description': desc,
            'amount_payable': amount,
            'notes': note,
            'is_title': title,
            'is_line': line,
            'payslip_id': self.id,
        }
        return result

    def _get_insurance(self):
        if not self.line_ids:
            return 0
        insurance = sum(self.line_ids.filtered(lambda x: x.code in ['BHXH', 'BHYT', 'BHTN']).mapped('amount'))
        return insurance

    def _get_pit(self):
        if not self.line_ids:
            return 0
        pit = sum(self.line_ids.filtered(lambda x: x.code == 'TTNCN').mapped('amount'))
        return pit

    def _get_salary_ot(self):
        if not self.line_ids:
            return 0
        ot_salary = sum(self.line_ids.filtered(lambda x: x.code in ['OTT', 'OTNT']).mapped('amount'))
        return ot_salary

    def _get_salary_timeoff(self):
        if not self.line_ids:
            return 0
        actual_day = self.get_actual_workday()
        if not self.work100:
            return 0
        dayoff = self.work100 - actual_day
        overleave = self.get_deduction_overleave()
        salary = self.contract_id.wage
        if self.contract_id.type_id.code == 'trial':
            salary = self.contract_id.wage * self.contract_id.salary_percent / 100
        sal = salary / self.work100 * dayoff + overleave
        return sal

    def get_deduction_overleave(self):
        if not self.line_ids:
            return 0
        over_leave = sum(self.line_ids.filtered(lambda x: x.code == 'OLD').mapped('amount'))
        return over_leave

    def _get_salary_net(self):
        if not self.line_ids:
            return 0
        net = sum(self.line_ids.filtered(lambda x: x.code == 'TLB' or x.code == 'TLC').mapped('amount'))
        return net

    def _get_hour_contributor(self):
        if not self.line_ids:
            return 0
        hours = self.worked_days_line_ids.filtered(lambda x: x.code.lower() == 'ctv').mapped('number_of_hours')
        return sum(hours)

    def _get_meal_income(self):
        actual_day = self.get_actual_workday()
        if not self.work100:
            return 0
        meal = self.contract_id.eat_inc / self.work100 * actual_day
        return meal

    def _get_phone_income(self):
        actual_day = self.get_actual_workday()
        if not self.work100:
            return 0
        phone = self.contract_id.phone_inc / self.work100 * actual_day
        return phone

    def _get_other_allowance(self):
        actual_day = self.get_actual_workday()
        other = self.mon_allowance + self.mon_bonus + self.adjustment_manual
        other_allowance = self.contract_id.work_allo_inc + self.contract_id.poison_inc + \
                          self.contract_id.ins_inc + (self.contract_id.uni_inc / 12)
        if self.contract_id.type_id.code == 'contributor':
            other_allowance = other_allowance + other
        if not self.work100:
            return 0
        other_allowance = other_allowance / self.work100 * actual_day + other
        return other_allowance

    def _get_other_deduction(self):
        other_allowance = self.deduction + self.reimburse
        if not self.work100:
            return 0
        return other_allowance

    def get_actual_workday(self):
        if not self.worked_days_line_ids:
            actual_day = self.get_workday_all_contract()
            return actual_day
        day = self.worked_days_line_ids.filtered(
            lambda x: x.code.startswith('WORK') or x.code.startswith('PUBLIC') or x.code.startswith('LEGAL')
            or x.code.startswith('Work') or x.code.startswith('work') or x.code.startswith('Public')
            or x.code.startswith('public') or x.code.startswith('Legal') or x.code.startswith('legal'))\
            .mapped('number_of_days')
        return sum(day)

    def get_workday_all_contract(self):
        contracts = self.get_all_contract(self.employee_id, self.date_from, self.date_to)
        days = 0
        for contract in contracts:
            if self.date_from <= contract.date_start:
                from_ = contract.date_start
            else:
                from_ = self.date_from

            if self.date_to <= contract.date_end:
                to_ = self.date_to
            else:
                to_ = contract.date_end
            workdays = self.env['hr.payslip'].get_worked_day_lines(contract, from_, to_)
            days += sum([day['number_of_days'] for day in workdays])
        return days

    def _generate_payslip_summary(self, vals):
        self.payslip_summary_ids.unlink()
        summaries = []
        for val in vals:
            summary = self.env['hr.payslip.summary'].create(val)
            summaries.append(summary)
        return summaries

    @api.model
    def create(self, vals):
        res = super(HrPayslipExtend, self).create(vals)
        if self.employee_id.bank_account_id:
            res['bank_account_id'] = self.employee_id.bank_account_id
        if self.employee_id.personal_tax_number:
            res['personal_tax_number'] = self.employee_id.personal_tax_number
        if self.employee_id.department_id:
            res['department_id'] = self.employee_id.department_id
        if self.employee_id.site_id:
            res['site_id'] = self.employee_id.site_id
        return res


class HrPayrollMonth(models.Model):
    _name = 'hr.payroll.month'
    # _order

    name = fields.Char(compute='cp_payroll_period', store=True)
    year = fields.Char()
    month = fields.Selection([
        (1, 'January'),
        (2, 'February'),
        (3, 'March'),
        (4, 'April'),
        (5, 'May'),
        (6, 'June'),
        (7, 'July'),
        (8, 'August'),
        (9, 'September'),
        (10, 'October'),
        (11, 'November'),
        (12, 'December')
    ])

    @api.depends('year', 'month')
    def cp_payroll_period(self):
        for se in self:
            if not se.year or not se.month:
                se.name = 'new'
                continue
            if se.month < 10:
                mon = '0{}'.format(se.month)
            else:
                mon = se.month
            se.name = '{}/{}'.format(se.year, mon)


class HrPayslipRunInherit(models.Model):
    _name = 'hr.payslip.run'
    _inherit = ['hr.payslip.run', 'mail.thread', 'mail.activity.mixin']

    def create_log_overlap(self, exists_payslip_emp):
        for rec in self:
            rec.message_post(body='Exists Payslips of Employees: {}'.format(exists_payslip_emp))
