
import datetime
from odoo import api, fields, models
import random, math


class QuickAppraisal(models.Model):
    _name = 'quick.appraisal'
    _rec_name = 'code'

    code = fields.Char()
    department_id = fields.Many2one('hr.department', string="Department")

    emp_ids = fields.Many2many('hr.employee', string="Employees", required=True)
    appraisal_deadline = fields.Date(string="Appraisal Deadline", required=True)

    hr_manager = fields.Boolean(string="Manager", default=False)
    hr_emp = fields.Boolean(string="Employee", default=False)
    hr_colleague = fields.Boolean(string="Colleague", default=False)
    hr_collaborator = fields.Boolean(string="Collaborators", default=False)

    hr_manager_id = fields.Many2many('hr.employee', 'manager_quick_appraisal_rel', string="Select Appraisal Reviewer")
    hr_colleague_id = fields.Many2many('hr.employee', 'colleagues_quick_appraisal_rel',
                                       string="Select Appraisal Reviewer")
    hr_collaborator_id = fields.Many2many('hr.employee', 'collaborators_quick_appraisal_rel',
                                          string="Select Appraisal Reviewer")

    manager_survey_id = fields.Many2one('survey.survey', string="Select Opinion Form")
    emp_survey_id = fields.Many2one('survey.survey', string="Select Appraisal Form")
    colleague_survey_id = fields.Many2one('survey.survey', string="Select Opinion Form")
    collaborator_survey_id = fields.Many2one('survey.survey', string="Select Opinion Form")

    state = fields.Selection([('draft', 'Draft'), ('sent', 'Sent')], default='draft', compute='_compute_state',
                             store=True)

    check_sent = fields.Boolean(string="Check Sent Mail", default=False, copy=False)
    check_draft = fields.Boolean(string="Check Draft", default=True, copy=False)

    type_review = fields.Selection([('partial', 'Partial'), ('full', 'Full')], default='full', required=1)

    partial_number = fields.Integer(default=4, help='Number of employees participated to one appraisal')

    @api.model
    def create(self, vals):
        vals['code'] = self.env['ir.sequence'].next_by_code('quick.appraisal') or 'New'
        res = super(QuickAppraisal, self).create(vals)
        return res

    @api.depends('check_sent', 'check_draft')
    def _compute_state(self):
        for appr in self:
            appr.state = 'draft' if appr.check_draft else 'sent'

    # @api.multi
    def start_quick_appraisal_fully(self):
        for emp in self.emp_ids:
            colleague_ids = self.hr_colleague_id
            collaborator_ids = self.hr_collaborator_id

            if emp in self.hr_colleague_id:
                colleague_ids = self.hr_colleague_id - emp
            if emp in self.hr_collaborator_id:
                collaborator_ids = self.hr_collaborator_id - emp

            vals = {
                'emp_id': emp.id,
                'appraisal_deadline': self.appraisal_deadline,
                'hr_manager': self.hr_manager,
                'hr_colleague': self.hr_colleague,
                'hr_collaborator': self.hr_collaborator,
                'hr_emp': self.hr_emp,
                'hr_manager_id': [(6, 0, self.hr_manager_id.ids)],
                'hr_colleague_id': [(6, 0, colleague_ids.ids)],
                'hr_collaborator_id': [(6, 0, collaborator_ids.ids)],
                'manager_survey_id': self.manager_survey_id.id,
                'emp_survey_id': self.emp_survey_id,
                'colleague_survey_id': self.colleague_survey_id.id,
                'collaborator_survey_id': self.collaborator_survey_id.id,
            }
            appraisal = self.env['hr.appraisal'].create(vals)
            appraisal.action_start_appraisal()
            self.check_sent = True
            self.check_draft = False

    def suggest_list_random(self, dict_v, m):
        lowest_key = m + 3
        suggest_list_rand = []
        for key in dict_v:
            if not dict_v.get(key, False):
                lowest_key = 0
            else:
                if len(dict_v[key]) <= lowest_key:
                    lowest_key = len(dict_v[key])

        for key in dict_v:
            if len(dict_v[key]) == lowest_key:
                suggest_list_rand.append(key)

        if lowest_key == m:
            return []
        return suggest_list_rand

    def gen_emp_pack(self, total_emp_id, n):
        result = []
        dict_count = {}
        list_total_index = [i for i in range(1, len(total_emp_id) + 1)]
        for i in list_total_index:
            dict_count[i] = []
        n_pack_index = []
        m = len(total_emp_id)
        suggest_list_rand = self.suggest_list_random(dict_count, m).copy()

        for appraisal_count in range(0, m):
            while 1:
                if appraisal_count + 2 in suggest_list_rand and appraisal_count + 2 not in n_pack_index:
                    gen_emp = appraisal_count + 2
                else:
                    gen_emp = random.choice(suggest_list_rand)
                if appraisal_count == len(list_total_index) - 1:
                    n_pack_index.append(gen_emp)
                    if not dict_count.get(gen_emp, False):
                        dict_count[gen_emp] = [gen_emp]
                    else:
                        dict_count[gen_emp].append(gen_emp)
                    suggest_list_rand = self.suggest_list_random(dict_count, m).copy()
                    if len(n_pack_index) == n:
                        # print(n_pack_index)
                        result.append(n_pack_index)
                        n_pack_index = []
                        break
                else:
                    # check duplicate number
                    if gen_emp in n_pack_index:
                        continue
                    # check emp tu danh gia emp
                    if gen_emp == list_total_index[appraisal_count]:
                        continue

                    n_pack_index.append(gen_emp)
                    if not dict_count.get(gen_emp, False):
                        dict_count[gen_emp] = [gen_emp]
                    else:
                        dict_count[gen_emp].append(gen_emp)

                    suggest_list_rand = self.suggest_list_random(dict_count, m).copy()

                    if len(n_pack_index) == n:
                        # print(n_pack_index)
                        result.append(n_pack_index)
                        n_pack_index = []
                        break

                if len(suggest_list_rand) == 0:
                    break
            if len(result) == m:
                break
        over_times = []
        under_times = []
        for key in dict_count:
            if len(dict_count[key]) > m:
                over_times.append(key)
            if len(dict_count[key]) < m:
                under_times.append(key)
        if m in result[m-1]:
            return False
        return result

    def convert_index_to_id(self, list_arr_index, emp_id):
        list_emp_id = []
        list_emp_id_inner = []
        for i in list_arr_index:
            for j in i:
                list_emp_id_inner.append(emp_id[j-1])
            list_emp_id.append(list_emp_id_inner)
            list_emp_id_inner = []

        return list_emp_id

    def start_quick_appraisal_partially(self):
        total_emp_id = self.emp_ids.ids
        n = self.partial_number
        while 1:
            colleague_list_index = self.gen_emp_pack(total_emp_id, n)
            if colleague_list_index != False:
                break
        colleague_list_id = self.convert_index_to_id(colleague_list_index, total_emp_id)
        for k in range(0, len(self.emp_ids)):
            emp = self.emp_ids[k]
            # tao appraisal
            collaborator_ids = self.hr_collaborator_id

            if emp in self.hr_collaborator_id:
                collaborator_ids = self.hr_collaborator_id - emp
            vals = {
                'emp_id': emp.id,
                'appraisal_deadline': self.appraisal_deadline,
                'hr_manager': self.hr_manager,
                'hr_colleague': self.hr_colleague,
                'hr_collaborator': self.hr_collaborator,
                'hr_emp': self.hr_emp,
                'hr_manager_id': [(6, 0, self.hr_manager_id.ids)],
                'hr_colleague_id': [(6, 0, colleague_list_id[k])],
                'hr_collaborator_id': [(6, 0, collaborator_ids.ids)],
                'manager_survey_id': self.manager_survey_id.id,
                'emp_survey_id': self.emp_survey_id,
                'colleague_survey_id': self.colleague_survey_id.id,
                'collaborator_survey_id': self.collaborator_survey_id.id,
            }
            appraisal = self.env['hr.appraisal'].create(vals)
            appraisal.action_start_appraisal()
            self.check_sent = True
            self.check_draft = False

    @api.onchange('department_id')
    def _onchange_employee_department(self):
        self.emp_ids = self.department_id.member_ids
        if self.department_id:
            if self.department_id.member_ids:
                self.hr_colleague = True
                self.hr_colleague_id = self.department_id.member_ids
            if self.department_id.manager_id:
                self.hr_manager = True
                self.hr_manager_id = self.department_id.manager_id
        else:
            self.emp_ids = False
            self.hr_colleague = False
            self.hr_colleague_id = False
            self.hr_manager = False
            self.hr_manager_id = False

    @api.onchange('type_review')
    def _onchange_type_review(self):

        warning_message = {
            'title': 'Be careful',
            'message': 'Number of employees involved in appraisal should be greater than 4',
        }
        if self.type_review == 'partial' and len(self.emp_ids) <= 4:
            self.type_review = 'full'
            return {
                'warning': warning_message
            }
        else:
            self.partial_number = len(self.emp_ids) - 1
            self.hr_colleague_id = self.emp_ids

    @api.onchange('partial_number')
    def _onchange_partial_number(self):
        warning_message = {
            'title': 'Be careful',
            'message': 'Invalid Partial Number',
        }
        if self.type_review == 'partial':
            self.hr_colleague = True
        if self.partial_number >= len(self.emp_ids):

            self.partial_number = len(self.emp_ids) - 1
            return {
                'warning': warning_message
            }
        if self.partial_number < 2 and self.partial_number >= 0:
            self.partial_number = 2
            return {
                'warning': warning_message
            }


    @api.onchange('emp_ids')
    def _onchange_emp_ids(self):
        if len(self.emp_ids) <= 4:
            self.type_review = 'full'

        if self.type_review == 'partial':
            if not self.partial_number:
                self.partial_number = len(self.emp_ids) - 1
            self.hr_colleague = True
            self.hr_colleague_id = self.emp_ids

    def start_quick_appraisal(self):
        if self.type_review == 'full':
            self.start_quick_appraisal_fully()
        if self.type_review == 'partial':
            self.start_quick_appraisal_partially()


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    emp_attachment_ids = fields.Many2many('ir.attachment', string='Employee Files')
    appraisal_count = fields.Integer(compute='_compute_apprasail_count', string="Appraisal Computation Details")
    appraisal_ids = fields.One2many('hr.appraisal', 'emp_id')

    @api.depends('appraisal_ids')
    def _compute_apprasail_count(self):
        domain_list_appraisal = [('emp_id', '=', self.id)]
        list_appraisal = self.env['hr.appraisal'].search(domain_list_appraisal)
        self.appraisal_count = len(list_appraisal)


class HrAppraisalForm(models.Model):
    _inherit = 'hr.appraisal'

    response_ids = fields.One2many('survey.user_input', 'appraisal_id', "Response", ondelete="set null",
                                   oldname="response")

    @api.multi
    def action_send_remind_mail(self):
        # create email

        template_obj = self.sudo().env.ref('bnk_appraisal.email_remind_appraisal_template')
        mail_content = """Dear %s , \
                       <br>The survey related to %s will be expired in one day \
                       <br>Click here to access the survey.<br> %s \
                       <br>The deadline is: %s"""

        for response in self.response_ids:
            if response.state == 'new':
                url = response.survey_id.public_url + '/' + response.token
                mail_vals = {
                    'subject': template_obj.subject,
                    'email_to': response.answerer_id.work_email,
                    'body_html': str(mail_content % (response.answerer_id.name, self.emp_id.name, url, self.appraisal_deadline)),
                    'email_from': template_obj.email_from,
                    }
                create_email = self.env['mail.mail'].create(mail_vals)
                create_email.send()

    @api.multi
    def action_remind_appraisal(self):
        today = datetime.date.today()
        time_delta = datetime.timedelta(days=1)
        state_sent_id = self.env.ref('oh_appraisal.hr_appraisal_sent').id
        domain_appraisal = [('state.id', '=', state_sent_id),
                            ('appraisal_deadline', '=', today + time_delta)
                            ]
        list_appraisal = self.env['hr.appraisal'].search(domain_appraisal)

        for appraisal in list_appraisal:
            appraisal.action_send_remind_mail()

    @api.multi
    def action_start_appraisal(self):
        """ This function will start the appraisal by sending emails to the corresponding employees
            specified in the appraisal"""
        send_count = 0
        appraisal_reviewers_list = self.fetch_appraisal_reviewer()
        for appraisal_reviewers, survey_id in appraisal_reviewers_list:
            for reviewers in appraisal_reviewers:
                url = survey_id.public_url
                response = self.env['survey.user_input'].create(
                    {'survey_id': survey_id.id, 'partner_id': reviewers.user_id.partner_id.id,
                     'appraisal_id': self.ids[0], 'deadline': self.appraisal_deadline, 'email': reviewers.user_id.email,
                     'answerer_id': reviewers.id})
                token = response.token
                if token:
                    url = url + '/' + token
                    mail_content = "Dear " + reviewers.name + "," + "<br>Please fill out the following survey " \
                                                                    "related to " + self.emp_id.name + "<br>Click here to access the survey.<br>" + \
                                   str(url) + "<br>Post your response for the appraisal till : " + str(
                        self.appraisal_deadline)
                    values = {'model': 'hr.appraisal',
                              'res_id': self.ids[0],
                              'subject': survey_id.title,
                              'body_html': mail_content,
                              'parent_id': None,
                              'email_from': self.env.user.email or None,
                              'auto_delete': True,
                              }
                    values['email_to'] = reviewers.work_email
                    result = self.env['mail.mail'].create(values)._send()
                    if result is True:
                        send_count += 1
                        self.write({'tot_sent_survey': send_count})
                        rec = self.env['hr.appraisal.stages'].search([('sequence', '=', 2)])
                        self.state = rec.id
                        self.check_sent = True
                        self.check_draft = False

        if self.hr_emp and self.emp_survey_id:
            self.ensure_one()
            if not self.response_id:
                response = self.env['survey.user_input'].create(
                    {'survey_id': self.emp_survey_id.id, 'partner_id': self.emp_id.user_id.partner_id.id,
                     'appraisal_id': self.ids[0], 'deadline': self.appraisal_deadline,
                     'email': reviewers.user_id.email})
                self.response_id = response.id
            else:
                response = self.response_id
            return self.emp_survey_id.with_context(survey_token=response.token).action_start_survey()
