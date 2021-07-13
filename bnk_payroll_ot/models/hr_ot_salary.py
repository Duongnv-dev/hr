from odoo import fields, models, api, _
from datetime import datetime
from odoo.exceptions import ValidationError
from calendar import monthrange
import copy


class HrOvertimeLine(models.Model):
    _name = 'hr.ot.line'

    ot_id = fields.Many2one('hr.ot', ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', 'Employee', track_visibility='onchange')
    date = fields.Date(copy=False)
    type_day = fields.Selection([('normal', 'Normal day'), ('weekend', 'Weekend'), ('annual', 'Annual')],
                                string='Type', compute='cp_type_day', store=True)
    ot_hour = fields.Float('Overtime Hour')
    salary_ot = fields.Float()
    salary_ot_tax = fields.Float()
    salary_ot_non_tax = fields.Float()
    state = fields.Selection(related='ot_id.state', store=True)

    @api.onchange('type_day', 'ot_hour')
    def _onchange_type_day(self):
        if self.ot_hour < 0:
            raise ValidationError('Overtimes hour must greater than 0')
        # elif self.type_day == 'normal' and self.ot_hour > 4:
        #     raise ValidationError('Overtimes not over 4 hour per day')
        # elif self.type_day == 'weekend' and self.ot_hour > 10:
        #     raise ValidationError('Overtimes not over 10 hour per a day of weekend')
        # elif self.type_day == 'annual' and self.ot_hour > 10:
        #     raise ValidationError('Overtimes not over 10 hour per a day of annual off')
        else:
            return

    @api.depends('date')
    def cp_type_day(self):
        for s in self:
            working_day = s.env['hr.payslip'].get_working_weekday(s.employee_id.id)
            if not s.date:
                s.type_day = 'normal'
                continue
            # check holiday
            is_holiday = s.env['public.holiday.line'].search(
                [('state', '=', 'approved'),
                 ('date', '=', s.date)], limit=1)
            if is_holiday:
                s.type_day = 'annual'
                continue
            # check weekend
            if s.date.weekday() not in working_day:
                s.type_day = 'weekend'
                continue

            s.type_day = 'normal'


class HrOvertime(models.Model):
    _name = 'hr.ot'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(compute='cp_name_ot', store=True)
    manager_id = fields.Many2one('hr.employee', 'Approver', track_visibility='onchange')
    project_id = fields.Many2one('project.project')
    month = fields.Many2one('hr.period', string='Month on payslip')
    state = fields.Selection([('draft', 'Draft'), ('wait', 'Waiting Approve'), ('approved', 'Approved'),
                              ('refused', 'Refused'), ('cancel', 'Cancel')], default='draft',
                             track_visibility='onchange')
    employee_id = fields.Many2one('hr.employee')
    employee_ids = fields.Many2many('hr.employee', 'ot_employee_rel', 'ot_id', 'employee_id')
    multi_employee = fields.Selection([('one', 'One'), ('multi', 'Multi')], default='one', string='Mode')
    note = fields.Text()
    ot_lines = fields.One2many('hr.ot.line', 'ot_id', string='Details')
    is_pm = fields.Boolean(compute='cp_user_approve')
    parent_id = fields.Many2one('hr.ot')
    child_ids = fields.One2many('hr.ot', 'parent_id')

    @api.depends('month')
    def cp_name_ot(self):
        for s in self:
            if not s.id:
                s.name = 'New'
                continue
            month = s.month.name
            s.name = 'OTR/{}/{}'.format(month, s.id)

    @api.onchange('multi_employee')
    def onchange_employee_mode(self):
        if self.multi_employee == 'one':
            self.employee_ids = False
        if self.multi_employee == 'multi':
            self.employee_id = False

    @api.onchange('ot_lines')
    def onchange_check_duplicate_rq_ot(self):
        warning = {
            'title': _('Warning!'),
            'message': _("Cannot send request OT 2 times a day"),
        }
        dates = []
        line_num = 0
        for line in self.ot_lines:
            if line.date in dates:
                self.ot_lines[line_num].date = False
                return {'warning': warning}
            dates.append(line.date)
            line_num += 1

    def action_submit(self):
        duplicate = self.check_duplicate_request()
        if duplicate:
            raise ValidationError(_('Cannot send request OT 2 times a day.\n' 
                                    'Employee {}'.format(self.employee_id.name)))
        self.write({'state': 'wait'})
        # self.send_email_approve()

    def send_email_approve(self):
        template_obj = self.sudo().env.ref('bnk_hr.email_notify_approve_ot_template')
        mail_body = """
Dear {} ,
<br>You have new Overtime Request need approve.
<br>Please login to approve request <b>{}</b><br>
<div class="font-size: 13px;"><p>-- <br/>OdooBot</p></div>
<p style="color: #555555; margin-top:32px;">
    Sent
    <span>
    by
    <a style="text-decoration:none; color: #875A7B;" href="https://bnk.solution.com">
        <span>B&amp;K Software Company Limited</span>
    </a>

    </span>
    using
    <a target="_blank" href="https://www.odoo.com?utm_source=db&amp;utm_medium=email" style="text-decoration:none; color: #875A7B;">Odoo</a>.
</p>""".format(self.manager_id.name, self.name)

        mail_vals = {
            'subject': template_obj.subject,
            'email_to': template_obj.email_to,
            'body_html': mail_body,
            'email_from': template_obj.email_from,
            'auto_delete': True,
        }
        create_email = self.env['mail.mail'].create(mail_vals)
        return

    def action_approve(self):
        dict = {
            'normal': self.env['hr.payslip'].get_ot_nor_rate(),
            'weekend': self.env['hr.payslip'].get_ot_wek_rate(),
            'annual': self.env['hr.payslip'].get_ot_hol_rate(),
        }
        self.check_and_gen_ot(dict)
        self.write({'state': 'approved'})

    def action_refused(self):
        self.write({'state': 'refused'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    @api.depends('manager_id')
    def cp_user_approve(self):
        for s in self:
            if s.env.user.id != s.manager_id.user_id.id:
                s.is_pm = False
                continue
            s.is_pm = True

    def check_and_gen_ot(self, dict):
        if self.multi_employee == 'one':
            self.compute_salary_ot_line(dict, self.employee_id)
        elif self.multi_employee == 'multi':
            self.gen_multi_request_ot(dict)

    def gen_multi_request_ot(self, dict):
        for employee in self.employee_ids:
            new_ot = self.copy()
            new_ot.write({
                'multi_employee': 'one',
                'employee_ids': False,
                'employee_id': employee.id,
                'parent_id': self.id
            })
            ot_line = []
            for line in self.ot_lines:
                ot_line.append((0, 0, {'date': line.date, 'ot_hour': line.ot_hour}))
            new_ot.ot_lines = ot_line
            new_ot.action_approve()

    def compute_salary_ot_line(self, dict, employee):
        last_day_mon = monthrange(self.month.year, int(self.month.month))[1]
        last_date = datetime.strptime('{}-{}-{}'.format(self.month.year, self.month.month, last_day_mon), '%Y-%m-%d')
        for line in self.ot_lines:
            if line.date > last_date.date():
                date_ = datetime.strftime(line.date, '%d/%m/%Y')
                raise ValidationError(_('Can not approve for date in future ({}).\nPlease remove line and approve again.'
                                        .format(date_)))
            rate = dict[line.type_day]
            line.employee_id = employee.id
            contract_id = self.check_contract_for_ot(line.date, employee)
            if not contract_id:
                line.salary_ot = 0
                continue

            workday = self.get_month_workday_by_line(line, contract_id)
            if not contract_id.type_id or contract_id.type_id.code != 'trial':
                line.salary_ot = round((contract_id.wage / workday) / 8 * line.ot_hour * rate, 0)
                line.salary_ot_tax = round((contract_id.wage / workday) / 8 * line.ot_hour, 0)
                line.salary_ot_non_tax = line.salary_ot - line.salary_ot_tax
            elif contract_id.type_id.code == 'trial':
                line.salary_ot = round((contract_id.wage / workday) / 8 * line.ot_hour * rate * \
                                 (contract_id.salary_percent / 100), 0)
                line.salary_ot_tax = round((contract_id.wage / workday) / 8 * line.ot_hour * \
                                     (contract_id.salary_percent / 100), 0)
                line.salary_ot_non_tax = line.salary_ot - line.salary_ot_tax

    def get_month_workday_by_line(self, line, contract):
        date = line.date
        mon = date.month
        year = date.year

        if mon < 10:
            mon = '0{}'.format(mon)
        start_date = '{}-{}-01'.format(year, mon)
        end_date = '{}-{}-{}'.format(year, mon, monthrange(year, int(mon))[1])
        workday = self.env['hr.payslip'].get_worked_day_lines(contract, start_date, end_date)
        total = sum([w['number_of_days'] for w in workday])
        return total

    def check_contract_for_ot(self, date, employee):
        """
        get current contract with date ot
        :param date: date calculate ot
        :param employee: employee ot
        :return: contract
        """
        domain = self.prepare_contract_domain(employee, date)
        contract = self.env['hr.contract'].search(domain)
        if not contract:
            return False
        return contract[0]

    def prepare_contract_domain(self, employee, date):
        domain = [('employee_id', '=', employee.id),
                  ('date_start', '<=', date),
                  ('date_end', '>=', date),
                  ('state', 'not in', ['draft', 'cancel']),
                 ]
        return domain

    def check_duplicate_request(self):
        if self.multi_employee == 'one':
            return self._check_duplicate_request(self.employee_id)
        else:
            return self._check_duplicate_request_multi()

    def _check_duplicate_request_multi(self):
        check = []
        for employee in self.employee_ids:
            check += self._check_duplicate_request(employee)
        if any(check):
            return True

    def _check_duplicate_request(self, employee):
        dates = []
        line_obj = self.env['hr.ot.line']
        for line in self.ot_lines:
            if line.date in dates:
                return True
            dates.append(line.date)
            lines = line_obj.search([('date', '=', line.date), ('state', 'not in', ['refused', 'cancel'])])
            ots = [line for line in lines if line.ot_id.multi_employee == 'one' and line.ot_id.employee_id == employee]
            if len(ots) > 1:
                return True
        return False
