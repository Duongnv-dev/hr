from odoo import api, models, fields, _
from odoo.tools import config
import os
from datetime import datetime, timedelta, date
import base64
from odoo.exceptions import ValidationError, UserError
from odoo.modules.module import get_module_resource

AVAILABLE_PRIORITIES = [
    ('0', ''),
    ('1', 'Bad'),
    ('2', 'Medium'),
    ('3', 'Good'),
    ('4', 'Very Good'),
    ('5', 'Excellent'),
]


class InheritApplicant(models.Model):
    _inherit = 'hr.applicant'

    @api.model
    def _default_image(self):
        image_path = get_module_resource('hr', 'static/src/img', 'default_image.png')
        return base64.b64encode(open(image_path, 'rb').read())

    recruitment_request_id = fields.Many2one('hr.recruitment.request')
    apply_date = fields.Date(default=datetime.now().date(), string=_('Applied Date'), required=True)
    dob = fields.Date(string=_('DOB'))
    age = fields.Integer(string=_('Age'), compute='_compute_applicant_age', store=True)
    gender = fields.Selection([
        ('female', _('Female')), ('male', _('Male'))
    ])
    cv_path = fields.Char(compute='_compute_cv_data', inverse='_inverse_cv_data')
    cv_data = fields.Binary(string=_('CV'), compute='_compute_cv_data', inverse='_inverse_cv_data', readonly=False)
    cv_file_name = fields.Char()
    time_interview_schedule = fields.Datetime(string=_('Interview Schedule'))
    interview_schedule_confirmed = fields.Boolean(string=_('Confirm'), default=False)
    site_id = fields.Many2one('hr.site', string=_('Location (Site)'))
    partner_name = fields.Char(required=True)
    categ_ids = fields.Many2many('hr.applicant.category', string="Skills")
    level_id = fields.Many2one('hr.applicant.level', string=_('Level'))
    hr_applicant_evaluate_ids = fields.One2many('hr.applicant.evaluate', 'hr_applicant_id')
    image_medium = fields.Binary(
        "Medium-sized photo", default=_default_image)
    public = fields.Boolean(default=False)
    salary_final = fields.Float("Final Salary", group_operator="avg")
    salary_final_extra = fields.Char("Final Salary Extra")
    interview_date = fields.Datetime(string='Interview Date')
    onboard_date = fields.Date(string='Onboard Date')
    notify_date_onboard = fields.Date(string='Onboard Date String', compute='_compute_get_days', store=True)
    is_send_mail_interview = fields.Boolean(default=False)
    contact_point = fields.Many2one('contact.point', string='Contact Point')
    contact_phone = fields.Char(string='Phone Number Contact', related='contact_point.phone_number')
    contact_email = fields.Char(string='Email Contact', related='contact_point.mail_contact')
    refuse_reason_id = fields.Many2one('hr.applicant.refuse.reason', string='Refuse Reason', track_visibility='onchange')
    priority = fields.Selection(AVAILABLE_PRIORITIES, "Appreciation", default='0')
    hide_reason = fields.Boolean(default=True, compute='_compute_hide_reason', store=True)
    has_send_mail_offer = fields.Boolean()
    has_send_mail_thankyou_refuse = fields.Boolean()
    hide_interview_button = fields.Boolean(compute='_compute_hide_reason')
    hide_offer_button = fields.Boolean(compute='_compute_hide_reason')
    offer_date = fields.Date(string='Offer Date')
    targeted_additional_pay = fields.Float(string='Targeted Additional Pay', compute='_compute_targeted_additional_pay')

    @api.depends('salary_final')
    def _compute_targeted_additional_pay(self):
        for rec in self:
            if rec.salary_final:
                rec.targeted_additional_pay = rec.salary_final - 4729400

    @api.constrains('age')
    def _constrains_age(self):
        for rec in self:
            if rec.age and rec.age <= 0:
                raise ValidationError(_('The age must be greater than 0'))

    @api.depends('dob')
    def _compute_applicant_age(self):
        for rec in self:
            if rec.dob is not False:
                rec.age = (datetime.today().date() - rec.dob) // timedelta(days=365)
            else:
                rec.age = 0

    @api.onchange('partner_name')
    def get_applicant_name(self):
        for rec in self:
            if rec.partner_name:
                rec.name = rec.partner_name

    def get_local_cv_path(self):
        home_path = os.getenv("HOME")
        local_path = home_path + '/cv_data/'
        if not os.path.exists(local_path):
            os.makedirs(local_path)
        return local_path

    @api.depends('stage_id')
    def _compute_hide_reason(self):
        ref = self.env.ref
        if ref('bnk_recruitment.stage_job6', raise_if_not_found=False):
            stage_job2, stage_job4 = ref('hr_recruitment.stage_job2'), ref('hr_recruitment.stage_job4')
            stage_job5, stage_job6 = ref('hr_recruitment.stage_job5'), ref('bnk_recruitment.stage_job6')
            for rec in self:
                stage = rec.stage_id
                rec.hide_interview_button = not (stage == stage_job2)
                rec.hide_reason = not (stage == stage_job4)
                rec.hide_offer_button = not (stage == stage_job5)
                rec.hide_onboard_button = not (stage == stage_job6)

    @api.depends('cv_file_name')
    def _compute_cv_data(self):
        """ Store cv of applications to server folder """
        # TODO: fix bug many files have same name
        for rec in self:
            if rec.cv_file_name:
                path = config.get("applicant_cv_path")
                if not path:
                    path = self.get_local_cv_path()
                rec.cv_path = os.path.join(path, rec.cv_file_name)
                try:
                    rec.cv_data = base64.b64encode(open(rec.cv_path, 'rb').read())
                except:
                    rec.cv_data = False
            else:
                rec.cv_path = False
                rec.cv_data = False

    def _inverse_cv_data(self):
        path = config.get("applicant_cv_path")
        if not path:
            path = self.get_local_cv_path()
        if self.cv_file_name:
            with open(os.path.join(path, self.cv_file_name), 'wb') as f:
                f.write(base64.b64decode(self.cv_data))

    def insert_applicant_in_recruitment_request(self, applicant_id, apply_date, job_id, site_id):
        requests = self.env['hr.recruitment.request'].search([
                                                ('request_date', '<=', apply_date), ('end_date', '>=', apply_date),
                                                ('state', 'not in', ('refused', 'done'))])
        if requests:
            for req in requests:
                work_location_job_list = []
                for req_job_line in req.request_job_line_ids:
                    work_location_job_list.append((req_job_line.site_id.id, req_job_line.job_id.id))
                if (site_id, job_id) in work_location_job_list:
                    req.applicant_ids = [(4, applicant_id, 0)]

    def remove_applicant_in_recruitment_request(self, applicant_id, apply_date, job_id):
        request = self.browse([applicant_id]).recruitment_request_id
        if request:
            if apply_date < request.request_date or apply_date > request.end_date or job_id not in request.job_ids.ids:
                request.applicant_ids = [(3, applicant_id, 0)]

    @api.model
    def create(self, vals):
        res = super(InheritApplicant, self).create(vals)
        applicant_id = res.id
        apply_date = res.apply_date
        job_id = res.job_id.id
        site_id = res.site_id.id
        self.insert_applicant_in_recruitment_request(applicant_id, apply_date, job_id, site_id)
        return res

    @api.depends('onboard_date')
    def _compute_get_days(self):
        for rec in self:
            if rec.onboard_date:
                rec.notify_date_onboard = rec.onboard_date - timedelta(days=1)

    def action_send_by_email_cron_onboard_date(self):
        applicants = self.env['hr.applicant'].search([('notify_date_onboard', '=', datetime.today())])
        for rec in applicants:
            rec.action_send_by_email_onboard_date()

    def action_send_by_email_cron_interview(self):
        applicants = self.search([('interview_date', '!=', False)])
        for rec in applicants:
            if rec.is_send_mail_interview:
                return False
            elif rec.interview_date < datetime.today().now():
                return False
            duration = rec.interview_date - datetime.today().now()
            if timedelta(days=0, hours=1, minutes=0) <= duration <= timedelta(days=0, hours=1, minutes=30):
                rec.action_send_by_email_interview()
                rec.is_send_mail_interview = True

    def action_send_by_email_interview(self):
        if self.interview_date == False:
            raise ValidationError(_('Please enter interview time information'))
        template = self.env.ref('bnk_recruitment.email_template_job_interview')
        template.send_mail(self.id, force_send=True)
        self.interview_schedule_confirmed = True
        message = self.message_post(body='Interview invitation has been sent', subject='Interview invitation has been sent')
        return message

    def action_send_by_email_offer(self):
        report_template_id = self.env.ref('bnk_recruitment.offer_letter_attach_pdf_send_mail_offer').render_qweb_pdf(self.id)
        data_record = base64.b64encode(report_template_id[0])
        name = "Offer Letter Attachment"
        ir_values = {
            'name': name,
            'type': 'binary',
            'datas': data_record,
            'store_fname': name,
            'datas_fname': name,
            'res_model': self._inherit,
            'res_id': self.id,
            'mimetype': 'application/x-pdf',
        }
        data_id = self.env['ir.attachment'].create(ir_values)
        template = self.env.ref('bnk_recruitment.email_template_offer')
        template.attachment_ids = [(6, 0, [data_id.id])]
        email_values = {'email_from': 'noreply@bnksolution.com',
                        'email_to': self.email_from}
        template.attachment_ids = [(3, data_id.id)]
        if self.onboard_date == False:
            raise ValidationError(_('Please enter onboard date and offer time information'))
        message = self.message_post(body='Offer letter send', subject='Offer letter send')
        template.send_mail(self.id, email_values=email_values, force_send=True)
        self.has_send_mail_offer = True
        return message, True

    def action_send_by_email_thankyou_refuse(self):
        template = self.env.ref('bnk_recruitment.template_send_by_email_thanks_refuse')
        template.send_mail(self.id, force_send=True)
        self.has_send_mail_thankyou_refuse = True
        message = self.message_post(body='Thank you email has been sent', subject='Thank you email has been sent')
        return message

    def action_send_by_email_onboard_date(self):
        template = self.env.ref('bnk_recruitment.email_template_job_onboard_date')
        template.send_mail(self.id, force_send=True)

    def toggle_interview_schedule_confirmed(self):
        for rec in self:
            rec.interview_schedule_confirmed = not rec.interview_schedule_confirmed

    def public_cv(self):
        for rec in self:
            rec.public = not rec.public

    @api.multi
    def create_employee_from_applicant(self):
        """ Create an hr.employee from the hr.applicants """
        employee = False
        for applicant in self:
            if applicant._context.get('recruitment_request_id'):
                recruitment_request = self.env['hr.recruitment.request'].browse(
                    applicant._context.get('recruitment_request_id'))
                if recruitment_request.state != 'accepted':
                    raise ValidationError(_("Please approve the request before create employee"))
            contact_name = False
            if applicant.partner_id:
                address_id = applicant.partner_id.address_get(['contact'])['contact']
                contact_name = applicant.partner_id.name_get()[0][1]
            else:
                new_partner_id = self.env['res.partner'].create({
                    'is_company': False,
                    'name': applicant.partner_name,
                    'email': applicant.email_from,
                    'phone': applicant.partner_phone,
                    'mobile': applicant.partner_mobile,
                    'customer': False
                })
                address_id = new_partner_id.address_get(['contact'])['contact']
            if applicant.job_id and (applicant.partner_name or contact_name):
                applicant.job_id.write({'no_of_hired_employee': applicant.job_id.no_of_hired_employee + 1})
                employee = self.env['hr.employee'].create({
                    'name': applicant.partner_name or contact_name,
                    'job_id': applicant.job_id.id,
                    'address_home_id': address_id,
                    'department_id': applicant.department_id.id or False,
                    'address_id': applicant.company_id and applicant.company_id.partner_id
                                  and applicant.company_id.partner_id.id or False,
                    'work_email': applicant.department_id and applicant.department_id.company_id
                                  and applicant.department_id.company_id.email or False,
                    'work_phone': applicant.department_id and applicant.department_id.company_id
                                  and applicant.department_id.company_id.phone or False})
                applicant.write({'emp_id': employee.id})
                applicant.job_id.message_post(
                    body=_(
                        'New Employee %s Hired') % applicant.partner_name if applicant.partner_name else applicant.name,
                    subtype="hr_recruitment.mt_job_applicant_hired")
            else:
                raise UserError(_('You must define an Applied Job and a Contact Name for this applicant.'))

        employee_action = self.env.ref('hr.open_view_employee_list')
        dict_act_window = employee_action.read([])[0]
        dict_act_window['context'] = {'form_view_initial_mode': 'edit'}
        dict_act_window['res_id'] = employee.id
        return dict_act_window

    @api.multi
    def write(self, vals):
        res = super(InheritApplicant, self).write(vals)
        if 'apply_date' in vals or 'job_id' in vals:
            for rec in self:
                applicant_id = rec.id
                apply_date = rec.apply_date
                job_id = rec.job_id.id
                site_id = rec.site_id.id
                rec.insert_applicant_in_recruitment_request(applicant_id, apply_date, job_id, site_id)
                rec.remove_applicant_in_recruitment_request(applicant_id, apply_date, job_id)
        return res

    @api.multi
    def archive_applicant(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Refuse Reason'),
            'res_model': 'applicant.get.refuse.reason',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_applicant_ids': self.ids, 'active_test': False},
            'views': [[False, 'form']]
        }


class HrApplicantLevel(models.Model):
    _name = 'hr.applicant.level'
    _description = 'Hr Applicant Level'

    name = fields.Char()
    _sql_constraints = [
        ('unique_name', 'unique (name)', 'Level already exists!')
    ]


class HrRecruitmentStateInherit(models.Model):
    _inherit = "hr.recruitment.stage"
    _description = "Recruitment Stages"


class ApplicantRefuseReason(models.Model):
    _name = "hr.applicant.refuse.reason"
    _description = 'Refuse Reason of Applicant'

    name = fields.Char('Description', required=True, translate=True)
    active = fields.Boolean('Active', default=True)

