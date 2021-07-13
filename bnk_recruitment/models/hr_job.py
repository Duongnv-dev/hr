# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import base64


class JDTemplate(models.Model):
    _name = 'jd.template'

    name = fields.Char(required=True)
    description = fields.Text(string='Job description')
    job_qualifications = fields.Text('Qualifications')
    job_requirements = fields.Text('Requirements',
                                   default='''<ul><li><p>Need to have Self-Learning skill, Teamwork spirit and be able to work under pressure. </p></li>
                                   <li><p> Ability to communicate and solve good problems. Ability to read comprehension is required. </p></li>
                                   <li><p> Ability to work independently and teamwork. Ability to learn and learn new techniques. </p></li>
                                   <li><p> Skills to synthesize information and report. High responsibility, professional working style. </p></li>
                                   <li><p> Being able to communicate in English is an advantage. </p></li>
                                   <li><p> Other details exchange more when interviewing. </p></li></ul><p>    
                                   We are firm believers that highly-qualified devs can adapt to any syntax/ technology, 
                                   so feel free to apply even if you don't meet all the requirements. 
                                   We value the ability to learn just as much as proficiency in any particular technology.</p>''')

    job_benefits = fields.Text('What we offer?',
                               default='''<p>Attactive salary agreed upon capacity. </p>
                               <p> Working hours: 8:30 ~ 17:30, 5 days/week. </p>
                               <p> Enjoying good remuneration of company when becoming an employee: social insurance, annual company trip, 13th salary, End Year bonus,… </p>
                               <p> Review salary twice a year. </p>
                               <p> Recognition and rewards based on your performance. </p>
                               <p> Creative, modern and open working place. </p>
                               <p> Continuous and professional training to fully develop your potential. </p>
                               <p> Work hard, play hard and enjoy various activities. </p>''')


class SendJDLogs(models.Model):
    _name = 'send.jd.logs'

    date = fields.Datetime()
    mailing = fields.Char()
    job_id = fields.Many2one('hr.job')


class BnkHrJob(models.Model):
    _inherit = 'hr.job'

    hr_email = fields.Char(related='hr_responsible_id.login')
    hr_mobile = fields.Char(related='hr_responsible_id.mobile')
    logs = fields.One2many('send.jd.logs', 'job_id')
    jd_template_id = fields.Many2one('jd.template')
    job_qualifications = fields.Text('Qualifications')
    job_requirements = fields.Text('Requirements',
                                   default='''<p>Need to have Self-Learning skill, Teamwork spirit and be able to work under pressure.</p><p>Ability to communicate and solve good problems.</p><p>Ability to read comprehension is required.</p><p>Ability to work independently and teamwork.</p><p>Ability to learn and learn new techniques.</p><p>Skills to synthesize information and report.</p><p>High responsibility, professional working style.</p><p>Being able to communicate in English is an advantage.</p><p>Other details exchange more when interviewing.</p><p>We are firm believers that highly-qualified devs can adapt to any syntax/ technology, so feel free to apply even if you don't meet all the requirements. We value the ability to learn just as much as proficiency in any particular technology.</p>''')
    job_benefits = fields.Text('What we offer?', default='''<p>Attactive salary agreed upon capacity.&nbsp;</p><p>Working hours: 8:30 ~ 17:30, 5 days/ week.</p><p>Enjoying good remuneration of company when becoming an employee: social insurance, annual company trip, 13th salary, End Year bonus,…&nbsp;</p><p>Review salary twice a year.</p>''')

    request_job_line_ids = fields.One2many('hr.request.job.line', 'job_id')
    recruitment_request_ids = fields.Many2many('hr.recruitment.request', relation='hr_recruitment_request_job_rel',
                                               column1='job_id', column2='request_id')
    skills = fields.Many2many('hr.applicant.category')
    years_experience_from = fields.Float(default=0, digits=(16, 1))
    years_experience_to = fields.Float(default=0, digits=(16, 1))
    cv_suggest_ids = fields.Many2many('hr.applicant', 'job_cv_suggest_rel', 'hr_job_id', 'hr_applicant_id')
    recruitment_request_count = fields.Integer(string='Requests', compute='_compute_recruitment_request')
    expected_new_employee = fields.Integer(compute='_compute_expected_new_employee', string=_('Expected New Employees'))
    recruitment_employee_count = fields.Integer(compute='_compute_recruitment_employee', string=_('Hired Employees'))
    no_of_recruitment_total = fields.Integer(compute='_compute_no_of_recruitment_total',
                                             string=_('Current Number of Employees'))
    priority = fields.Selection([
        ('1', 'Urgent'), ('2', 'High'), ('3', 'Normal')
    ], string=_('Priority'), default='3')
    color = fields.Integer("Color Index", compute="set_kanban_color")
    applicant_level_id = fields.Many2one('hr.applicant.level', string=_('Level'))
    file = fields.Binary(string=_('JD File'))
    file_name = fields.Char()
    new_application_count = fields.Integer(
        compute='_compute_new_application_count', string="New Application",
        help="Number of applications that are new in the flow (typically at first step of the flow)")

    @api.model
    def default_get(self, fields):
        res = super(BnkHrJob, self).default_get(fields)
        user = self.env['res.users'].browse(self.env.uid)
        employees = user.employee_ids
        department_list = self.env['hr.department'].search([('manager_id', 'in', employees.ids)])
        if not department_list:
            return res
        res['department_id'] = department_list[0].id
        return res

    @api.onchange('jd_template_id')
    def change_jd_template_id(self):
        if self.jd_template_id:
            self.description = self.jd_template_id.description
            self.job_qualifications = self.jd_template_id.job_qualifications
            self.job_requirements = self.jd_template_id.job_requirements
            self.job_benefits = self.jd_template_id.job_benefits

    def suggest_cv(self):
        action_obj = self.env.ref('bnk_hr.action_wizard_suggest_cv')
        action = action_obj.read([])[0]
        context = {'default_hr_jod_id': self.id}
        if self.skills:
            context['default_skills'] = [(6, 0, self.skills._ids)]
        if self.years_experience_from:
            context['default_years_experience_from'] = self.years_experience_from
        if self.years_experience_to:
            context['default_years_experience_to'] = self.years_experience_to
        action['context'] = context
        return action

    def send_jd_contact(self):
        if self.is_published is False:
            self.is_published = True

        link = self.env['ir.config_parameter'].sudo().get_param('web.base.url') + self.website_url
        pdf = self.env.ref('bnk_recruitment.action_export_jd_pdf').render_qweb_pdf(self.id)[0]
        attachment = self.env['ir.attachment'].create({
            'name': 'JD',
            'type': 'binary',
            'datas': base64.encodebytes(pdf),
            'res_model': 'hr.job',
            'res_id': self.id,
            'mimetype': 'application/x-pdf',
            'datas_fname': self.name + '_JD.pdf',
        })

        mail_body = '''
<p>Xin chào bạn {mem},</p>
<p>Mình là HR của Công ty Phần mềm B&amp;K.</p>

<p>Không biết hiên tại bạn có dự định tìm cho mình một môi trường làm việc mới không ạ?</p>

<p>B&amp;K hiện đang có job <b>{job}</b> và đang cần lắm sự hỗ trợ của các bạn. Về chi tiết công việc, bạn xem JD giúp mình ạ.</p>

<p><a href="{link}" data-original-title="" title="" aria-describedby="tooltip457772">{link}</a><br></p>
<p><br></p>

<p>Mình cũng xin giới thiệu một chút về lĩnh vực hoạt động của Công ty nhé:</p>
<p>Công ty cung cấp 3 service chính:</p>
<p>1. Giải pháp ERP solution cho doanh nghiệp vừa và nhỏ&nbsp;</p>
<p>2. Giải pháp Factory 4.0 cho nhà máy&nbsp;</p>
<p>3. Outsourcing cho thị trường Nhật Bản và Châu Âu&nbsp;</p>
<p><br></p>
<p>Đây là website của Công ty ạ, bạn tham khảo thêm thông tin nha: https://bnksolution.com/&nbsp;<span style="white-space:pre">	</span></p>

<p>Về mức lương, bên mình sẽ offer với mức hấp dẫn, tuỳ thuộc vào năng lực và kinh nghiệm của từng ứng viên.</p>
<p>&nbsp;<span style="white-space:pre">	</span></p>
<p>Về các chế độ phúc lợi:</p><p><span style="white-space:pre">	</span>*1 năm có 12 ngày phép</p>
<p><span style="white-space:pre">	</span>*Được review tăng lương 6 tháng/ 1 lần, tính cả thời gian thử việc</p>
<p><span style="white-space:pre">	</span>*Lương tháng 13</p>
<p><span style="white-space:pre">	</span>*Thưởng theo hiệu suất công việc</p>
<p><span style="white-space:pre">	</span>*Teambuilding thường niên</p>
<p><span style="white-space:pre">	</span>*Happy hour hàng tháng</p>
<p><span style="white-space:pre">	</span>*Được tham gia bảo hiểm xã hội</p>
<p><br></p><p>Mình rất hy vọng bạn sẽ dành thời gian để đọc hết mail này cũng như xem qua những thông tin công ty và quan tâm đến nhu cầu tuyển dụng của B&amp;K, B&amp;K mong rằng sẽ có cơ hội được làm việc lâu dài cùng bạn.</p>
<p>&nbsp;</p><p>Mình cám ơn bạn và hy vọng sẽ sớm nhận được phản hồi từ bạn ạ.</p>
<p>&nbsp;</p><p>Thank you &amp; Best regards,</p>
<p><b>{hr}</b>
</p><p><br></p>
<p><b>B&amp;K Software Co., Ltd,</b></p>
<p><b>Address:</b> Level 10th, 195 Dien Bien Phu Street, Binh Thanh Dist., HCMC.</p>
<p><b>Phone number:</b>{mobile}</p>'''
        email = []
        for cv in self.cv_suggest_ids:
            if cv.email_from:
                email.append(cv.email_from)
                send_email = self.env['mail.mail'].create({
                    'subject': 'Thư mời tuyển dụng {}'.format(self.name),
                    'body_html': mail_body.format(job=self.name, hr=self.hr_responsible_id.name,
                                                  link=link, mobile=self.hr_mobile or '', mem=cv.partner_name),
                    'email_from': self.hr_email or '',
                    'email_to': cv.email_from,
                    'reply_to': self.hr_email or '',
                    'auto_delete': True,
                    'attachment_ids': [(4, attachment.id)],
                    # 'body': mail_body,
                })
        log_val = {
            'date': datetime.now(),
            'mailing': email,
            'job_id': self.id,
        }
        log = self.env['send.jd.logs'].create(log_val)
        return True

    def export_jd(self):
        action = self.env.ref('bnk_recruitment.action_export_jd_pdf').report_action(self)
        return action

    def _get_first_stage(self):
        self.ensure_one()
        return self.env['hr.recruitment.stage'].search([
            '|',
            ('job_id', '=', False),
            ('job_id', '=', self.id)], order='sequence asc', limit=1)

    def _compute_new_application_count(self):
        for job in self:
            job.new_application_count = self.env["hr.applicant"].search_count(
                [("job_id", "=", job.id), ("stage_id", "=", job._get_first_stage().id)]
            )

    def set_kanban_color(self):
        for rec in self:
            if rec.priority == '1':
                rec.color = 9
            elif rec.priority == '2':
                rec.color = 10
            elif rec.priority == '3':
                rec.color = 2
            else:
                rec.color = 0

    def set_draft_to_recruit(self):
        for rec in self:
            rec.state = 'recruit'

    def auto_close_request_from_state(self):
        requests = self.recruitment_request_ids
        for request in requests:
            state_open_count = 0
            for rec in request.request_job_line_ids:
                if rec.job_id.state == 'open':
                    state_open_count += 1
            if len(request.request_job_line_ids) == state_open_count:
                request.state = 'done'

    def write(self, vals):
        res = super(BnkHrJob, self).write(vals)
        if 'state' in vals:
            self.auto_close_request_from_state()
        return res

    def open_recruitment_request(self):
        return {
            'name': _('Recruitment Request'),
            'domain': [('job_ids', 'in', self.id)],
            'view_type': 'form',
            'res_model': 'hr.recruitment.request',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }

    def _compute_recruitment_request(self):
        for rec in self:
            rec.recruitment_request_count = len(rec.recruitment_request_ids)

    @api.depends('recruitment_request_ids')
    def _compute_recruitment_employee(self):
        for rec in self:
            rec.recruitment_employee_count = 0
            requests = rec.recruitment_request_ids.filtered(lambda x: x.state in ('accepted', 'done'))
            for req in requests:
                recruitment_emp_count = req.request_job_line_ids.filtered(lambda x: x.job_id.id == rec.id).mapped(
                    'employees_count')
                recruitment_emp_count = sum(recruitment_emp_count)
                rec.recruitment_employee_count += recruitment_emp_count

    @api.depends('recruitment_request_ids')
    def _compute_no_of_recruitment_total(self):
        for rec in self:
            rec.no_of_recruitment_total = 0
            requests = rec.recruitment_request_ids.filtered(lambda x: x.state in ('accepted', 'done'))
            for req in requests:
                no_of_recruitment = req.request_job_line_ids.filtered(lambda x: x.job_id.id == rec.id).mapped(
                    'no_of_recruitment')
                no_of_recruitment = sum(no_of_recruitment)
                rec.no_of_recruitment_total += no_of_recruitment

    @api.depends('recruitment_request_ids')
    def _compute_expected_new_employee(self):
        for rec in self:
            rec.expected_new_employee = 0
            requests = rec.recruitment_request_ids.filtered(lambda x: x.state == 'accepted')
            for req in requests:
                no_of_recruitment = req.request_job_line_ids.filtered(lambda x: x.job_id.id == rec.id).mapped(
                    'no_of_recruitment')
                employees_count = req.request_job_line_ids.filtered(lambda x: x.job_id.id == rec.id).mapped(
                    'employees_count')
                if sum(employees_count) <= sum(no_of_recruitment):
                    expected_new_employee = sum(no_of_recruitment) - sum(employees_count)
                    rec.expected_new_employee += expected_new_employee
                else:
                    rec.expected_new_employee = 0
