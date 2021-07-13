from odoo import api, models, fields
from odoo.exceptions import ValidationError
from odoo import http, _
from datetime import datetime


class RecruitmentRequest(models.Model):
    _name = 'hr.recruitment.request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'HR Recruitment Request'

    name = fields.Char(string=_('Job Position'), required=True)
    company_id = fields.Many2one('res.company', string=_('Company'))
    department_id = fields.Many2one('hr.department', string=_('Department'), required=True)
    request_job_line_ids = fields.One2many('hr.request.job.line', 'recruitment_request_id')
    job_ids = fields.Many2many('hr.job', relation='hr_recruitment_request_job_rel', column1='request_id',
                               column2='job_id', string=_('Requested Position'), required=True,
                               compute='_compute_job_ids', store=True)
    request_date = fields.Date(string=_('Request Date'), default=lambda self: fields.datetime.now().date(), required=True)
    end_date = fields.Date(required=True)
    user_id = fields.Many2one('res.users', string=_('Request By'), default=lambda self: self.env.user)
    applicant_ids = fields.One2many('hr.applicant', 'recruitment_request_id')
    employee_ids = fields.One2many('hr.employee', 'recruitment_request_id')
    state = fields.Selection([
        ('draft', _('Draft')), ('refused', _('Cancelled')), ('confirmed', _('Waiting for approval')),
        ('accepted', _('Approved')), ('done', _('Closed'))
    ], string=_('Status'), index=True, default='draft', track_visibility="onchange")

    @api.model
    def default_get(self, fields):
        res = super(RecruitmentRequest, self).default_get(fields)
        user = self.env['res.users'].browse(self.env.uid)
        employees = user.employee_ids
        department_list = self.env['hr.department'].search([('manager_id', 'in', employees.ids)])
        if not department_list:
            return res
        res['department_id'] = department_list[0].id
        return res

    @api.constrains('request_date', 'end_date')
    def _check_expected_date(self):
        today = datetime.now().date()
        for rec in self:
            if rec.request_date < today:
                raise ValidationError(_("Please select a date that does not fall on the past"))
            if rec.request_date >= rec.end_date:
                raise ValidationError(_("The end date must be than request date"))

    @api.constrains('request_job_line_ids')
    def check_overlap_job_line(self):
        for rec in self:
            job_location_list = []
            for line in rec.request_job_line_ids:
                job_location_list.append((line.job_id, line.site_id))
            if len(job_location_list) != len(set(job_location_list)):
                raise ValidationError(_("Duplicate job position"))

    @api.depends('request_job_line_ids')
    def _compute_job_ids(self):
        for rec in self:
            for request_job_line in rec.request_job_line_ids:
                rec.job_ids = [(4, request_job_line.job_id.id, 0)]

    @api.constrains('request_job_line_ids', 'request_date', 'end_date')
    def _check_exist_request(self):
        for rec in self:
            request_job_lines = rec.mapped('request_job_line_ids')
            for request_job_line in request_job_lines:
                if request_job_line.check_overlap_date_request(self):
                    raise ValidationError(_("Recruitment request is already exist for this job position"))

    def action_confirm(self):
        for rec in self:
            if rec.request_job_line_ids:
                job_location_list = []
                for line in rec.request_job_line_ids:
                    job_location_list.append((line.job_id, line.site_id))
                exist_requests = []
                domain = [('job_ids', 'in', rec.job_ids.ids), ('state', 'in', ('draft', 'confirmed')),
                          ('id', '!=', rec.id)]
                exist_requests_1 = self.search(domain + [('request_date', '>=', rec.request_date),
                                                         ('end_date', '<=', rec.end_date)])
                if exist_requests_1:
                    exist_requests.extend(exist_requests_1)
                exist_requests_2 = self.search(domain + [('request_date', '>=', rec.request_date),
                                                         ('request_date', '<=', rec.end_date),
                                                         ('end_date', '>=', rec.end_date)])
                if exist_requests_2:
                    exist_requests.extend(exist_requests_2)
                exist_requests_3 = self.search(domain + [('request_date', '<=', rec.request_date),
                                                         ('end_date', '>=', rec.request_date),
                                                         ('end_date', '<=', rec.end_date)])
                if exist_requests_3:
                    exist_requests.extend(exist_requests_3)
                exist_requests_4 = self.search(domain + [('request_date', '<=', rec.request_date),
                                                         ('end_date', '>=', rec.end_date)])
                if exist_requests_4:
                    exist_requests.extend(exist_requests_4)
                exist_job_location_list = []
                for req in exist_requests:
                    for line in req.request_job_line_ids:
                        exist_job_location_list.append((line.job_id, line.site_id))
                for i in job_location_list:
                    if i in exist_job_location_list:
                        raise ValidationError(_("Job(s) has/have been existed in another request"))
                rec.state = 'confirmed'
            else:
                raise ValidationError(_("The job line must be required"))

    def action_accept(self):
        for rec in self:
            rec.state = 'accepted'
            for job in rec.job_ids:
                job._compute_no_of_recruitment_total()

    def action_refuse(self):
        for rec in self:
            rec.state = 'refused'

    def action_draft(self):
        for rec in self:
            rec.state = 'draft'

    def action_done(self):
        for rec in self:
            rec.state = 'done'
            for job in rec.job_ids:
                job._compute_no_of_recruitment_total()

    @api.multi
    def write(self, vals):
        res = super(RecruitmentRequest, self).write(vals)
        if 'request_job_line_ids' in vals and self.state == 'accepted':
            self.write({'state': 'confirmed'})
        return res
