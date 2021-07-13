from odoo import api, models, fields, _
from datetime import datetime


class InheritEmployee(models.Model):
    _inherit = 'hr.employee'

    recruitment_request_id = fields.Many2one('hr.recruitment.request')
    join_date = fields.Date(copy=False, required=True, default=datetime.today().date(), track_visibility='onchange')
    no_of_cv = fields.Integer(compute='_compute_no_of_cv', type='integer')
    applicant_ids = fields.One2many('hr.applicant', 'emp_id')

    def insert_employee_in_recruitment_request(self, employee_id, join_date, job_id, site_id):
        requests = self.env['hr.recruitment.request'].search(
            [('request_date', '<=', join_date), ('end_date', '>=', join_date), ('state', '=', 'accepted')])
        if requests:
            for req in requests:
                site_job_list = []
                for req_job_line in req.request_job_line_ids:
                    site_job_list.append((req_job_line.site_id.id, req_job_line.job_id.id))
                if (site_id, job_id) in site_job_list:
                    req.employee_ids = [(4, employee_id, 0)]

    def remove_employee_in_recruitment_request(self, employee_id, join_date, job_id, site_id):
        request = self.browse([employee_id]).recruitment_request_id
        if request:
            site_job_list = []
            for req_job_line in request.request_job_line_ids:
                site_job_list.append((req_job_line.site_id.id, req_job_line.job_id.id))
                if join_date < request.request_date or join_date > request.end_date or (site_id, job_id) not in site_job_list:
                    request.employee_ids = [(3, employee_id, 0)]

    def auto_close_request_from_employees_count(self, job_id):
        requests = self.env['hr.recruitment.request'].search([('job_ids', 'in', job_id)])
        for request in requests:
            done_count = 0
            for job_line in request.request_job_line_ids:
                if job_line.no_of_recruitment == job_line.employees_count:
                    done_count += 1
            if len(request.request_job_line_ids) == done_count:
                request.state = 'done'

    @api.model
    def create(self, vals):
        res = super(InheritEmployee, self).create(vals)
        employee_id = res.id
        join_date = res.join_date
        job_id = res.job_id.id
        site_id = res.site_id.id
        if job_id and site_id:
            self.insert_employee_in_recruitment_request(employee_id, join_date, job_id, site_id)
            self.auto_close_request_from_employees_count(job_id)
        return res

    @api.multi
    def write(self, vals):
        res = super(InheritEmployee, self).write(vals)
        if 'join_date' in vals or 'site_id' in vals or 'job_id' in vals:
            for rec in self:
                employee_id = rec.id
                join_date = rec.join_date
                job_id = rec.job_id.id
                site_id = rec.site_id.id
                rec.insert_employee_in_recruitment_request(employee_id, join_date, job_id, site_id)
                rec.remove_employee_in_recruitment_request(employee_id, join_date, job_id, site_id)
                rec.auto_close_request_from_employees_count(job_id)
        return res

    def _compute_no_of_cv(self):
        for rec in self:
            rec.no_of_cv = len(rec.applicant_ids)
