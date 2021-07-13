from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.osv import expression
from datetime import datetime, date, timedelta
from dateutil.relativedelta import *


class ContractType(models.Model):
    _inherit = 'hr.contract.type'

    name = fields.Char(string='Contract Type', required=False, help="Name")
    notify_expire_contract_before = fields.Integer(string='Notify Expire Contract Before', default=30)
    item_check_category_id = fields.Many2one('item.check.category')
    code = fields.Selection([('official', 'Official'), ('trial', 'Trial'), ('contributor', 'Contributor'),
                             ('other', 'Other')], default='official')
    period = fields.Selection([('1_mon', '1 Month'), ('2_mon', '2 Month'), ('3_mon', '3 Month'), ('6_mon', '6 Month'),
                               ('1_year', '1 Year'), ('2_year', '2 Year'), ('3_year', '3 Year'),
                               ('no_limit', 'No Limit')], default='1_year')
    active = fields.Boolean('Active', default=True)

    @api.onchange('code')
    def onchange_remaining_day(self):
        if not self.code:
            return
        if self.code == 'trial':
            self.notify_expire_contract_before = 15
            self.period = '2_mon'
        elif self.code == 'official':
            self.notify_expire_contract_before = 30
            self.period = '1_year'
        elif self.code == 'contributor':
            self.notify_expire_contract_before = 30
            self.period = '6_mon'
        elif self.code == 'other':
            self.notify_expire_contract_before = 30
            self.period = '6_mon'


class HrContractConfigBase(models.Model):
    _name = 'hr.contract.config'

    name = fields.Char(default='Contract Configure')
    insurance_salary_base = fields.Float('Salary level insurance')
    deduct_personal_base = fields.Float()
    deduct_dependent_base = fields.Float()
    social_ins = fields.Float('Social Insurance (%)', default=8)
    health_ins = fields.Float('Health Insurance (%)', default=1.5)
    unemployment_ins = fields.Float('Unemployment Insurance (%)', default=1)
    social_ins_com = fields.Float('Social Insurance Company(%)', default=17.5)
    health_ins_com = fields.Float('Health Insurance Company(%)', default=3)
    unemployment_ins_com = fields.Float('Unemployment Insurance Company(%)', default=1)


class BnKContract(models.Model):
    _inherit = 'hr.contract'

    type_id = fields.Many2one('hr.contract.type', string="Contract Type", required=False,
                              default=lambda self: self.env['hr.contract.type'].search([], limit=1))
    date_start = fields.Date('Start Date', required=True, copy=False,
                             help="Start date of the contract.")
    date_end = fields.Date('End Date', copy=False,
                           help="End date of the contract (if it's a fixed-term contract).")

    @api.model
    def default_get(self, fields):
        res = super(BnKContract, self).default_get(fields)
        employee = self.env['hr.employee'].browse(self._context.get('active_ids', False))
        if not employee:
            return res
        res['date_start'] = employee.join_date
        return res

    @api.onchange('employee_id')
    def _onchange_start_date_from_join_date(self):
        if self.employee_id:
            self.date_start = self.employee_id.join_date

    @api.constrains('state')
    def constraints_state(self):
        contract_state_open = self.search([('employee_id', '=', self.employee_id.id), ('state', '=', 'open')])
        if len(contract_state_open) > 1:
            raise ValidationError(_('Employee can have only one contract at running state!'))
        return

    def get_contract_domain_overlap(self):
        return [('id', '!=', self.id), ('employee_id', '=', self.employee_id.id),
                '|', ('state', 'in', ['draft', 'open', 'close']), ('state', '=', 'draft')]

    @staticmethod
    def get_contract_state():
        return lambda c: (c.state not in ['cancel'] or c.state == 'draft') and c.employee_id

    @api.constrains('employee_id', 'state', 'date_start', 'date_end')
    def _check_current_contract(self):
        if self._context.get('duplicate', False):
            return
        for contract in self.filtered(self.get_contract_state()):
            domain = self.get_contract_domain_overlap()
            if not contract.date_end:
                start_domain = []
                end_domain = ['|', ('date_end', '>=', contract.date_start), ('date_end', '=', False)]
            else:
                start_domain = [('date_start', '<=', contract.date_end)]
                end_domain = ['|', ('date_end', '>', contract.date_start), ('date_end', '=', False)]
            domain = expression.AND([domain, start_domain, end_domain])
            if self.search_count(domain):
                raise ValidationError(_('Contracts start/end date overlap!!!'))

    @api.constrains('date_start', 'date_end', 'employee_id')
    def _constrains_same_date_in_contract(self):
        date_end = ''
        employee = self.employee_id
        if len(employee.contract_ids) > 1:
            date_end = employee.contract_ids[-2].date_end
        date_start = employee.contract_ids[-1].date_start
        if date_start == date_end:
            raise ValidationError(_('Start/End date overlap!!!'))

    @api.constrains('employee_id')
    def constrains_contract_from_resigned_date(self):
        resign_date = self.employee_id.resigned_date
        is_resign = self.employee_id.is_resign
        today = datetime.today().date()
        date_start = self.date_start
        date_end = self.date_end
        contract = self.employee_id.contract_ids
        if resign_date and is_resign == True:
            if contract and date_start >= resign_date or date_end >= resign_date:
                raise ValidationError(_('Can not create contract!'))
            elif contract and resign_date <= today:
                raise ValidationError(_('Can not create contract when employee is resigned!'))

    def change_wage(self, vals, old_wage):
        new_wage = str(vals.get('wage'))
        employee = self.employee_id
        employee.message_post(body='Update Contract: Wage: {} -> {}'.format(old_wage, new_wage))

    def write(self, vals):
        for contract in self:
            old_wage = ''
            if vals.get('wage'):
                old_wage = str(contract.wage)
            res = super(BnKContract, contract).write(vals)
            if 'wage' in vals and str(vals.get('wage')) != old_wage:
                contract.change_wage(vals, old_wage)
        return True

    def get_default_insurance(self):
        config = self.env['hr.contract.config'].search([])
        insurance_salary = 0
        if not config:
            return insurance_salary
        insurance_salary = config[-1].insurance_salary_base
        return insurance_salary

    def get_default_deduct_personal(self):
        config = self.env['hr.contract.config'].search([])
        deduct_personal = 0
        if not config:
            return deduct_personal
        deduct_personal = config[-1].deduct_personal_base
        return deduct_personal

    def get_default_deduct_dependent(self):
        config = self.env['hr.contract.config'].search([])
        deduct_dependent = 0
        if not config:
            return deduct_dependent
        deduct_dependent = config[-1].deduct_dependent_base
        return deduct_dependent

    def get_social_ins(self):
        config = self.env['hr.contract.config'].search([])
        social_ins = 0
        if not config:
            return social_ins
        social_ins = config[-1].social_ins
        return social_ins

    def get_health_ins(self):
        config = self.env['hr.contract.config'].search([])
        health_ins = 0
        if not config:
            return health_ins
        health_ins = config[-1].health_ins
        return health_ins

    def get_unemployment_ins(self):
        config = self.env['hr.contract.config'].search([])
        unemployment_ins = 0
        if not config:
            return unemployment_ins
        unemployment_ins = config[-1].unemployment_ins
        return unemployment_ins

    def get_unemployment_ins_com(self):
        config = self.env['hr.contract.config'].search([])
        unemployment_ins_com = 0
        if not config:
            return unemployment_ins_com
        unemployment_ins_com = config[-1].unemployment_ins_com
        return unemployment_ins_com

    def get_health_ins_com(self):
        config = self.env['hr.contract.config'].search([])
        health_ins_com = 0
        if not config:
            return health_ins_com
        health_ins_com = config[-1].health_ins_com
        return health_ins_com

    def get_social_ins_com(self):
        config = self.env['hr.contract.config'].search([])
        social_ins_com = 0
        if not config:
            return social_ins_com
        social_ins_com = config[-1].social_ins_com
        return social_ins_com

    @api.onchange('employee_id', 'type_id')
    def onchange_employee_contract(self):
        if self.employee_id and self.type_id:
            self.name = '[{}] - {}\'s contract'.format(self.type_id.code, self.employee_id.name)

    @api.multi
    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        new_contract = super(BnKContract, self.with_context(duplicate=True)).copy()
        new_contract.date_start = self.date_end + timedelta(days=1)
        new_contract.onchange_date_end()
        return new_contract

    insurance_salary = fields.Float('Salary Insurance', default=get_default_insurance, track_visibility="onchange")
    deduct_personal = fields.Float(default=get_default_deduct_personal, track_visibility="onchange")
    deduct_dependent = fields.Float(default=get_default_deduct_dependent, track_visibility="onchange")
    income_non_tax = fields.Float(track_visibility="onchange")
    income_tax = fields.Float(track_visibility="onchange")
    daily_allowment = fields.Float()
    day_allowment = fields.Integer()
    salary_cash = fields.Float(track_visibility="onchange")
    salary_contract = fields.Float(track_visibility="onchange")
    external_note = fields.Text()
    contract_attachment_ids = fields.Many2many('ir.attachment', string='Contract Files')
    contract_config = fields.Many2one('hr.contract.config')
    sub_type = fields.Selection(related='type_id.code')
    salary_percent = fields.Integer('Salary Trial Percent (%)', default=85)
    salary_per_hour = fields.Float('Salary/hour')
    period = fields.Selection(related='type_id.period')
    social_ins = fields.Float('Social Insurance (%)', default=get_social_ins)
    health_ins = fields.Float('Health Insurance (%)', default=get_health_ins)
    unemployment_ins = fields.Float('Unemployment Insurance (%)', default=get_unemployment_ins)
    social_ins_com = fields.Float('Social Insurance (%)', default=get_social_ins_com)
    health_ins_com = fields.Float('Health Insurance (%)', default=get_health_ins_com)
    unemployment_ins_com = fields.Float('Unemployment Insurance (%)', default=get_unemployment_ins_com)
    dependent_person = fields.Integer(related='employee_id.dependent_person')
    contribute_tax = fields.Selection([('tax', 'Tax 10%'), ('tax_progressive', 'Tax Progressive'),
                                       ('non_tax', 'Non Tax')], default='non_tax')
    parent_contract = fields.Many2one('hr.contract', 'Origin Contract')
    child_contracts = fields.One2many('hr.contract', 'parent_contract')
    is_origin_contract = fields.Boolean('Origin', default=False, copy=False)
    is_calculate_leave = fields.Selection([('no', 'No'), ('yes', 'Yes')], default='no', copy=False)
    child_contract_trial = fields.Integer()

    def get_list_email(self, contract):
        contract_manager_id = self.env.ref('hr_contract.group_hr_contract_manager')
        user_contract_manager = self.env['res.users'].search([('groups_id', 'in', [contract_manager_id.id])])
        user_contract_manager_id = [u.id for u in user_contract_manager]
        hr_employee = self.env['hr.employee'].search([('user_id', 'in', user_contract_manager_id)])
        list_email_hr = [hr.work_email for hr in hr_employee if hr.work_email is not False]
        email_remind_list = []
        if contract.employee_id.department_id.manager_id.work_email:
            email_remind_list.append(contract.employee_id.department_id.manager_id.work_email)
        if contract.employee_id.department_id.employee_remind_extend:
            extend_emails = [emp.work_email for emp in contract.employee_id.department_id.employee_remind_extend if emp.work_email is not False]
            email_remind_list.extend(extend_emails)
        email_remind_list.extend(list_email_hr)
        if email_remind_list:
            return list(set(email_remind_list))
        else:
            contract.message_post(body='The contract will be expired at {} but no email to send remind'.format(contract.date_end))

    def send_notify_expired_email(self):
        today = date.today()
        domain_contract = [('employee_id', '!=', False), ('active', '=', True), ('state', '=', 'open'), ('date_end', '>', today)]
        list_contract = self.env['hr.contract'].search(domain_contract)
        for contract in list_contract:
            time_delta = timedelta(days=contract.type_id.notify_expire_contract_before)
            date_remind = contract.date_end - time_delta
            if date_remind == today or date_remind == today - timedelta(days=1):
                list_email_hr = self.get_list_email(contract)
                if list_email_hr:
                    self.remind_contract(contract, list_email_hr, today)

    def remind_contract(self, contract, list_email, today):
        contract = self.env['hr.contract'].browse(contract.id)
        template_obj = self.sudo().env.ref('bnk_hr.remind_expired_contract_template')
        body = template_obj.body_html
        body = body.replace('--name employee--', str(contract.employee_id.name))
        body = body.replace('--end date--', str(contract.date_end))

        email_cc_string = ';'.join(list_email)
        mail_values = {
            'subject': '[{}] {}'.format(contract.employee_id.name, template_obj.subject),
            'body_html': body,
            'email_to': email_cc_string,
            # 'email_cc': email_cc_string,
            'email_from': 'system@bnksolution.com',
            'auto_delete': True
        }
        create_email = self.env['mail.mail'].create(mail_values)

    @api.multi
    def print_nda(self):
        return self.env.ref('bnk_hr.report_bnk_nda').report_action(self)

    @api.multi
    def print_contract(self):
        if self.type_id.code == 'trial':
            return self.env.ref('bnk_hr.account_probationary_contract_action').report_action(self)
        if self.type_id.code == 'official':
            return self.env.ref('bnk_hr.account_employee_contract_action').report_action(self)
        if self.type_id.code == 'contributor':
            return self.env.ref('bnk_hr.account_collaborative_contract_action').report_action(self)

    def get_date_time(self, string_date):
        d = datetime.date.strftime(string_date, '%d-%m-%Y')
        return d

    @api.constrains('state', 'date_start', 'date_end', 'employee_id')
    def check_something(self):
        something = self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id),
                                                    ('state', '=', 'open')])
        if len(something) <= 1:
            return

        def sortSecond(val):
            return val[0]

        something_lst = [[i.date_start, i.date_end] for i in something]
        something_lst.sort(key=sortSecond)
        for s in range(1, len(something_lst)):
            index = s - 1
            check_overlap = self.get_overlap_interval(
                {'start': something[index].date_start, 'stop': something[index].date_end},
                {'start': something[index+1].date_start, 'stop': something[index+1].date_end}
            )
            if check_overlap:
                raise ValidationError(_('Cannot possible to have multiple contracts for an employee to running'))

    @api.model
    def get_overlap_interval(self, first_interval, second_interval):
        point_list = [first_interval['start'], second_interval['start']]
        if first_interval.get('stop', False):
            point_list.append(first_interval['stop'])
        if second_interval.get('stop', False):
            point_list.append(second_interval['stop'])
        point_list.sort()
        if len(point_list) < 4 and False not in point_list:
            point_list.append(False)
        index_intervals = [[0, 1], [1, 2]]
        if len(point_list) == 4:
            index_intervals = [[0, 1], [1, 2], [2, 3]]
        for index_interval in index_intervals:
            interval = {
                'start': point_list[index_interval[0]],
                'stop': point_list[index_interval[1]],
            }
            if not self.env['hr.contract'].check_interval(interval):
                continue
            if self.check_first_interval_inside_second_interval(interval, first_interval) \
                    and self.check_first_interval_inside_second_interval(interval, second_interval):
                return interval
        return False

    @api.model
    def check_first_interval_inside_second_interval(self, first_interval, second_interval):
        if first_interval['start'] < second_interval['start']:
            return False
        if not first_interval.get('stop', False) and not second_interval.get('stop', False):
            return True
        if first_interval.get('stop', False) and second_interval.get('stop', False):
            if first_interval.get('stop', False) <= second_interval.get('stop', False):
                return True
        if first_interval.get('stop', False) and not second_interval.get('stop', False):
            return True
        return False

    @api.model
    def check_interval(self, interval):
        if not interval.get('stop', False):
            return True
        if interval['start'] >= interval['stop']:
            return False
        return True

    # @api.model
    # def create(self, vals):
    #     res_contract = super(BnKContract, self).create(vals)
    #     if res_contract.employee_id and res_contract.type_id.item_check_category_id:
    #         val = {}
    #         self.env['onboarding.checklist'].with_context(create_from_context=True,
    #                                                       employee_id=res_contract.employee_id,
    #                                                       item_check_id=res_contract.type_id.item_check_category_id).create(val)
    #     return res_contract

    @api.onchange('period', 'date_start')
    def onchange_date_end(self):
        if not self.period or not self.date_start:
            return
        if self.period == '1_mon':
            self.date_end = self.date_start + relativedelta(months=+1) - timedelta(days=1)
        elif self.period == '2_mon':
            self.date_end = self.date_start + relativedelta(months=+2) - timedelta(days=1)
        elif self.period == '3_mon':
            self.date_end = self.date_start + relativedelta(months=+3) - timedelta(days=1)
        elif self.period == '6_mon':
            self.date_end = self.date_start + relativedelta(months=+6) - timedelta(days=1)
        elif self.period == '1_year':
            self.date_end = self.date_start + relativedelta(months=+12) - timedelta(days=1)
        elif self.period == '2_year':
            self.date_end = self.date_start + relativedelta(months=+24) - timedelta(days=1)
        elif self.period == '3_year':
            self.date_end = self.date_start + relativedelta(months=+36) - timedelta(days=1)
        elif self.period == 'no_limit':
            self.date_end = False

    @api.onchange('is_origin_contract')
    def onchange_parent_contract(self):
        if self.is_origin_contract:
            self.parent_contract = False

    @api.constrains('wage', 'type_id')
    def constrains_log_contract(self):
        old_wage = 0
        old_contract_type = ''
        employee = self.employee_id
        if len(employee.contract_ids) > 1:
            old_wage = employee.contract_ids[-2].wage
            old_contract_type = employee.contract_ids[-2].type_id.name
        new_wage = employee.contract_ids[-1].wage
        new_contract_type = employee.contract_ids[-1].type_id.name
        if new_wage != old_wage:
            employee.message_post(
                    body='Update wage from new contract: Wage: {} -> {}'.format(old_wage, new_wage))
        if new_contract_type != old_contract_type:
            employee.message_post(
                    body='Update contract type: {} -> {}'.format(old_contract_type, new_contract_type))


class HrContractConfig(models.Model):
    _inherit = 'hr.contract.config'

    contract_ids = fields.One2many('hr.contract', 'contract_config')

    def get_val_update(self):
        vals = {}
        if self.insurance_salary_base > 0:
            vals['insurance_salary'] = self.insurance_salary_base
        if self.deduct_personal_base > 0:
            vals['deduct_personal'] = self.deduct_personal_base
        if self.deduct_dependent_base > 0:
            vals['deduct_dependent'] = self.deduct_dependent_base
        if self.social_ins > 0:
            vals['social_ins'] = self.social_ins
        if self.health_ins > 0:
            vals['health_ins'] = self.health_ins
        if self.unemployment_ins > 0:
            vals['unemployment_ins'] = self.unemployment_ins
        if self.social_ins_com > 0:
            vals['social_ins_com'] = self.social_ins_com
        if self.health_ins_com > 0:
            vals['health_ins_com'] = self.health_ins_com
        if self.unemployment_ins_com > 0:
            vals['unemployment_ins_com'] = self.unemployment_ins_com
        if self.eat_inc > 0:
            vals['eat_inc'] = self.eat_inc
        if self.phone_inc > 0:
            vals['phone_inc'] = self.phone_inc
        if self.work_allo_inc > 0:
            vals['work_allo_inc'] = self.work_allo_inc
        if self.poison_inc > 0:
            vals['poison_inc'] = self.poison_inc
        if self.ins_inc > 0:
            vals['ins_inc'] = self.ins_inc
        if self.uni_inc > 0:
            vals['uni_inc'] = self.uni_inc
        vals['is_eat_inc'] = self.is_eat_inc
        vals['is_phone_inc'] = self.is_phone_inc
        vals['is_work_allo_inc'] = self.is_work_allo_inc
        vals['is_poison_inc'] = self.is_poison_inc
        vals['is_ins_inc'] = self.is_ins_inc
        vals['is_uni_inc'] = self.is_uni_inc
        return vals

    @api.multi
    def update_multi(self):
        self.ensure_one()
        if not self.contract_ids:
            return
        contract_ids = [c.id for c in self.contract_ids]
        vals = self.get_val_update()
        if not vals:
            return
        for contract in contract_ids:
            res = self.env['hr.contract'].browse(contract).write(vals)
        return res
