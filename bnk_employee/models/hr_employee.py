from odoo import models, fields, api, _
from odoo.exceptions import Warning, UserError
from datetime import datetime, date, timedelta


class Employee(models.Model):
    _inherit = 'hr.employee'

    move_ids = fields.One2many('hr.employee.move', 'employee_id', readonly=True)
    personal_email = fields.Char(string='Personal Email')
    id_attendance = fields.Char(string=_('ID Attendance'), required=True, copy=False, index=True,
                                default=lambda self: _('New'))
    perm_address = fields.Text(string=_('Permanent Address'))
    temp_address = fields.Text(string=_('Temporary Address'))
    categ_ids = fields.Many2many('hr.applicant.category', string="Skills")
    payslip_ids = fields.One2many('hr.payslip', 'employee_id')
    identification_date = fields.Date()
    issued_by = fields.Char()
    dependent_person = fields.Integer('Number of dependent person', track_visibility="onchange")
    contract_type = fields.Selection([('official', 'Official'), ('trial', 'Trial'), ('contributor', 'Contributor'),
                                      ('other', 'Other')], compute='cp_contract_type', store=True)
    address_home_id = fields.Many2one('res.partner', 'Private Address', groups="base.group_user",
                                      help='Enter here the private address of the employee, not the one linked to your company.')
    identification_id = fields.Char(string='Identification No', groups="base.group_user")
    bank_account_id = fields.Many2one('res.partner.bank', 'Bank Account Number',
                                      domain="[('partner_id', '=', address_home_id)]", groups="base.group_user",
                                      help='Employee bank salary account')
    birthday = fields.Date('Date of Birth', groups="base.group_user")
    remaining_legal_leaves = fields.Float(compute='get_remaining_legal_leaves')
    remaining_unpaid_leaves = fields.Float(compute='get_remaining_unpaid_leaves')
    personal_tax_number = fields.Char()
    social_insurance_number = fields.Char()
    day_off = fields.Date()
    site_id = fields.Many2one('hr.site', string='Location (Site)')
    skill = fields.Char()
    latest_contract = fields.Many2one('hr.contract', compute='_compute_latest_contract', string='Latest Contract',
                                      store=True)
    latest_contract_state = fields.Selection(related='latest_contract.state', store=True)
    birthday_str = fields.Char('Birthday String', compute='_compute_birthday_str', store=True)

    @api.model
    def default_get(self, fields):
        res = super(Employee, self).default_get(fields)
        applicant = self.env['hr.applicant'].browse(self._context.get('applicant_id'))
        if not applicant:
            return res
        res['site_id'] = applicant.site_id.id
        res['categ_ids'] = applicant.categ_ids
        return res

    @api.constrains('resigned_date')
    def _check_change_of_resigned_date(self):
        day_resign = self.resigned_date
        payslip_states = self.env['hr.payslip'].search([('state', '=', 'done'),('employee_id', '=', self.id)])
        if not self.is_resign:
            return
        for contract in self.contract_ids:
            if contract.date_end:
                if contract.date_start <= day_resign <= contract.date_end:
                    if contract.state in ['draft', 'cancel']:
                        raise Warning(_('Can not update resign date because contract is new or cancelled!'))
                elif contract.date_end < day_resign:
                    if contract.state == 'open':
                        raise Warning(_('Can not update date resign date after end date of contract!'))
                elif day_resign < contract.date_start:
                    if contract.state == 'open':
                        raise Warning(_('Can not update date resign date before start date of contract!'))
            elif not contract.date_end:
                if day_resign > contract.date_start:
                    if contract.state in ['draft', 'cancel']:
                        raise Warning(_('Can not update resign date because contract is new or canceled!'))
                elif day_resign <= contract.date_start:
                    if contract.state == 'open':
                        raise Warning(_('Can not update date resign date before start date of contract!'))
        for payslip_state in payslip_states:
            if not day_resign >= payslip_state.date_from or day_resign <= payslip_state.date_to:
                raise Warning(_('Can not update because payslip have done!'))

    @api.model
    def create(self, vals):
        if vals.get('id_attendance', _('New')) == _('New'):
            vals['id_attendance'] = self.env['ir.sequence'].next_by_code('id.attendance.employee') or _('New')
        return super(Employee, self).create(vals)

    @api.onchange('department_id')
    def onchange_department_id(self):
        department_id = self._context.get('department_id')
        if department_id:
            jobs = self.env['hr.job'].search(['|', ('department_id', '=', department_id), ('department_id', '=', False)])
            return {'domain': {'job_id': [('id', 'in', jobs.ids)]}}

    @api.model
    def get_data_dict(self, model_name, domain, field_list):
        records = self.env[model_name].search_read(
            domain, field_list)

        res_dict = {}
        for record in records:
            employee_id = record['employee_id'] and record['employee_id'][0] or 0
            number_of_days_display = record['number_of_days_display'] or 0
            if not res_dict.get(employee_id, False):
                res_dict[employee_id] = 0
            res_dict[employee_id] += number_of_days_display
        return res_dict

    @api.multi
    def get_remaining_legal_leaves(self):
        employee_ids = self._ids
        begin_current_year = '{}-01-01'.format(date.today().year)
        end_current_year = '{}-12-31'.format(date.today().year)
        legal_holiday_type = self.env['hr.leave.type'].search([('validity_start', '<=', date.today()),
                                                               ('validity_stop', '>=', date.today()),
                                                               ('code', '=', 'legal')])
        legal_holiday = False
        if legal_holiday_type:
            legal_holiday = legal_holiday_type[0]
        else:
            legal_holiday_type = self.env['hr.leave.type'].search(
                [('validity_stop', '=', False), ('code', '=', 'legal')])
            if legal_holiday_type:
                legal_holiday = legal_holiday_type[0]
        if not legal_holiday:
            return
        legal_domain = [('holiday_status_id', '=', legal_holiday.id),
                        ('holiday_type', '=', 'employee'),
                        ('state', '=', 'validate'),
                        ('employee_id', 'in', employee_ids)]

        field_list = ['number_of_days_display', 'employee_id']

        legal_dict = self.get_data_dict(model_name='hr.leave.allocation',
                                        domain=legal_domain, field_list=field_list)
        legal_domain.append(('date_from', '>=', begin_current_year))
        legal_domain.append(('date_to', '<=', end_current_year))
        legal_leave_dict = self.get_data_dict(model_name='hr.leave',
                                              domain=legal_domain, field_list=field_list)

        for employee in self:
            legal = legal_dict.get(employee.id, 0)
            legal_leave = legal_leave_dict.get(employee.id, 0)
            employee.remaining_legal_leaves = legal - legal_leave

    @api.multi
    def get_remaining_unpaid_leaves(self):
        employee_ids = self._ids
        begin_current_year = '{}-01-01'.format(date.today().year)
        end_current_year = '{}-12-31'.format(date.today().year)

        unpaid_day_type = self.env['hr.leave.type'].search([('validity_start', '<=', date.today()),
                                                            ('validity_stop', '>=', date.today()),
                                                            ('code', '=', 'unpaid')])
        unpaid_day = False
        if unpaid_day_type:
            for unpaid in unpaid_day_type:
                if unpaid.unpaid is True:
                    unpaid_day = unpaid
        else:
            unpaid_day_type = self.env['hr.leave.type'].search([('validity_stop', '=', False), ('code', '=', 'unpaid')])
            for unpaid in unpaid_day_type:
                if unpaid.unpaid is True:
                    unpaid_day = unpaid
        if not unpaid_day:
            return

        unpaid_domain = [('holiday_status_id', '=', unpaid_day.id),
                         ('holiday_type', '=', 'employee'),
                         ('state', '=', 'validate'),
                         ('employee_id', 'in', employee_ids)]

        field_list = ['number_of_days_display', 'employee_id']

        unpaid_dict = self.get_data_dict(model_name='hr.leave.allocation',
                                         domain=unpaid_domain, field_list=field_list)
        unpaid_domain.append(('date_from', '>=', begin_current_year))
        unpaid_domain.append(('date_to', '<=', end_current_year))
        unpaid_leave_dict = self.get_data_dict(model_name='hr.leave',
                                               domain=unpaid_domain, field_list=field_list)

        for employee in self:
            unpaid = unpaid_dict.get(employee.id, 0)
            unpaid_leave = unpaid_leave_dict.get(employee.id, 0)
            employee.remaining_unpaid_leaves = unpaid - unpaid_leave

    def get_identification_date_report(self):
        date = self.env['change.datetime'].get_date_report(self.identification_date, '%d/%m/%Y')
        return date

    def get_birth_day_report(self):
        date = self.env['change.datetime'].get_date_report(self.birthday, '%d/%m/%Y')
        return date

    @api.depends('contract_id.type_id', 'contract_id')
    def cp_contract_type(self):
        for s in self:
            if not s.contract_id:
                s.contract_type = False
                continue
            s.contract_type = s.contract_id.type_id.code

    @api.depends('contract_ids')
    def _compute_latest_contract(self):
        """ get the lastest contract """
        contract = self.env['hr.contract']
        for employee in self:
            employee.latest_contract = contract.search([('employee_id', '=', employee.id)], order='date_start desc',
                                                       limit=1)

    @api.depends('birthday')
    def _compute_birthday_str(self):
        for rec in self:
            if rec.birthday:
                rec.birthday_str = '{}-{}'.format(str(rec.birthday.month), str(rec.birthday.day))

    def send_reminder_birthday_employee(self):
        today = date.today()
        days_config = self.env['res.config.settings'].sudo().get_days()
        if int(days_config) > 0:
            time_delta = today + timedelta(days=int(days_config))
            time_delta_str = '{}-{}'.format(str(time_delta.month), str(time_delta.day))
            employees = self.search([('birthday_str', '=', time_delta_str)])
            for emp in employees:
                if emp.department_id.manager_id.work_email:
                    manager_email = emp.department_id.manager_id.work_email
                    self.remind_birthday(emp, manager_email)
        else:
            raise UserError(_("You need config parameter days before birthday sending reminder mail in setting."))

    def remind_birthday(self, emp, manager_email):
        template_obj = self.sudo().env.ref('bnk_employee.remind_birthday_employee_template')
        body = template_obj.body_html
        body = body.replace('--receiver name--', str(emp.department_id.manager_id.name))
        body = body.replace('--birthday--', str(emp.birthday))
        body = body.replace('--employee name--', str(emp.name))

        mail_values = {
            'subject': '[{}] {}'.format(emp.name, template_obj.subject),
            'body_html': body,
            'email_to': manager_email,
            'email_from': 'system@bnksolution.com',
            'auto_delete': True
        }
        create_email = self.env['mail.mail'].create(mail_values)


class HrSite(models.Model):
    _name = 'hr.site'

    name = fields.Char()
    description = fields.Char()
    active = fields.Boolean(default=True)

