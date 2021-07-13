from odoo import api, models, fields, _
from odoo.exceptions import ValidationError


class RequestJobLine(models.Model):
    _name = 'hr.request.job.line'
    _description = 'Request Job Line'

    recruitment_request_id = fields.Many2one('hr.recruitment.request')
    job_id = fields.Many2one('hr.job', required=True)
    no_of_recruitment = fields.Integer(required=True)
    no_of_recruitment_report = fields.Integer(compute='_compute_no_of_recruitment_report', store=True)
    reason = fields.Text(string=_('Reason'))
    site_id = fields.Many2one('hr.site', string=_('Location (Site)'), required=True)
    employees_count = fields.Integer(readonly=True, string=_('Employees Count'), compute='_compute_employee_count', store=True)
    user_id = fields.Many2one('res.users', string=_('Request By'), default=lambda self: self.env.user)
    creation_date = fields.Date(compute='_compute_creation_date', store=True)
    department_id = fields.Many2one('hr.department', string='Department', compute='_compute_recruit_department',
                                    store=True)
    applicant_level_id = fields.Many2one('hr.applicant.level', string=_('Level'))

    @api.depends('recruitment_request_id')
    def _compute_recruit_department(self):
        for rec in self:
            rec.department_id = rec.recruitment_request_id.department_id

    @api.depends('recruitment_request_id')
    def _compute_creation_date(self):
        for rec in self:
            rec.creation_date = rec.recruitment_request_id.request_date

    @api.depends('no_of_recruitment')
    def _compute_no_of_recruitment_report(self):
        for rec in self:
            if rec.recruitment_request_id.state in ('accepted', 'done'):
                rec.no_of_recruitment_report = rec.no_of_recruitment
            else:
                rec.no_of_recruitment_report = 0

    @api.depends('recruitment_request_id.employee_ids')
    def _compute_employee_count(self):
        for rec in self:
            rec.employees_count = 0
            for emp in rec.recruitment_request_id.employee_ids:
                if emp.job_id == rec.job_id and emp.site_id == rec.site_id:
                    rec.employees_count += 1

    @api.constrains('no_of_recruitment')
    def check_no_of_recruitment(self):
        for rec in self:
            if rec.no_of_recruitment <= 0:
                raise ValidationError(_("The no of expected employee must be than 0"))

    @api.onchange('job_id')
    def onchange_job_id(self):
        job_ids_list = []
        jobs_no_department = self.env['hr.job'].search([('department_id', '=', False), ('state', '=', 'recruit')])
        if self._context.get('department_id'):
            department_id = self.env['hr.department'].browse(self._context.get('department_id'))
            for job in department_id.jobs_ids:
                if job.state == 'recruit':
                    job_ids_list.append(job.id)
            job_ids_list.extend(jobs_no_department.ids)
        return {'domain': {'job_id': [('id', 'in', job_ids_list)]}}

    def change_expected_employees(self, vals, old_expected_employees):
        job_name = self.job_id.name
        new_expected_employees = str(vals.get('no_of_recruitment'))
        request = self.recruitment_request_id
        request.message_post(
            body='Expected employee has been change on job: {}: {} -> {}'.format(job_name, old_expected_employees,
                                                                                 new_expected_employees))

    def get_overlap_request_job_line(self, request_ss):
        line_ss = []
        for request_ss in request_ss:
            for line in request_ss.request_job_line_ids:
                if line.job_id.id == self.job_id.id and line.site_id == self.site_id:
                    line_ss.append(line)
                    break
        return line_ss

    def check_overlap_date_request(self, request):
        hr_recruitment_data = self.env['hr.recruitment.request']
        requests_ss1 = hr_recruitment_data.search([('job_ids', 'in', self.job_id.id),
                                                   ('request_date', '<=', request.request_date),
                                                   ('end_date', '>=', request.end_date),
                                                   ('state', '=', 'accepted'),
                                                   ('id', '!=', request.id)])
        line_ss1 = self.get_overlap_request_job_line(requests_ss1)
        requests_ss2 = hr_recruitment_data.search([('job_ids', 'in', self.id),
                                                   ('request_date', '<=', request.request_date),
                                                   ('end_date', '<=', request.end_date),
                                                   ('end_date', '>=', request.request_date),
                                                   ('state', '=', 'accepted'),
                                                   ('id', '!=', request.id)])
        line_ss2 = self.get_overlap_request_job_line(requests_ss2)
        requests_ss3 = hr_recruitment_data.search([('job_ids', 'in', self.id),
                                                   ('request_date', '>=', request.request_date),
                                                   ('request_date', '<=', request.end_date),
                                                   ('end_date', '>=', request.end_date),
                                                   ('state', '=', 'accepted'),
                                                   ('id', '!=', request.id)])
        line_ss3 = self.get_overlap_request_job_line(requests_ss3)
        requests_ss4 = hr_recruitment_data.search([('job_ids', 'in', self.id),
                                                   ('request_date', '>=', request.request_date),
                                                   ('end_date', '<=', request.end_date),
                                                   ('state', '=', 'accepted'),
                                                   ('id', '!=', request.id)])
        line_ss4 = self.get_overlap_request_job_line(requests_ss4)
        if (requests_ss1 and line_ss1) or (requests_ss2 and line_ss2) or (requests_ss3 and line_ss3) or (
                requests_ss4 and line_ss4):
            return True

    def write(self, vals):
        old_expected_employees = str(self.no_of_recruitment)
        res = super(RequestJobLine, self).write(vals)
        if 'no_of_recruitment' in vals and str(vals.get('no_of_recruitment')) != old_expected_employees:
            self.change_expected_employees(vals, old_expected_employees)
        return res
