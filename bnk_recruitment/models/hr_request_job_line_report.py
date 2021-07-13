from odoo import api, models, fields, tools, _


class RequestJobLineReport(models.Model):
    _name = 'hr.request.job.report'
    _auto = False

    id = fields.Integer('ID')
    measure = fields.Integer(string=_('Measure Employees'))
    job_id = fields.Many2one('hr.job')
    site_id = fields.Many2one('hr.site', string=_('Location (Site)'))
    user_id = fields.Many2one('res.users', string=_('Request By'))
    creation_date = fields.Datetime()
    department_id = fields.Many2one('hr.department', string='Department')
    type = fields.Selection(selection=[
        ('count', _('Recruited Employees')),
        ('recruited', _('Expected Employees'))
    ], string=_('Expected/Recruited'))

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'hr_request_job_report')
        self.env.cr.execute('''
            CREATE OR REPLACE VIEW hr_request_job_report AS(
            SELECT jl.id as id,
                    'count' as type,
                    jl.employees_count as measure,
                    jl.job_id,
                    jl.user_id,
                    jl.site_id,
                    jl.department_id,
                    jl.creation_date
            FROM hr_request_job_line as jl
            UNION ALL
            SELECT jl.id + 999999 as id,
                    'recruited' as type,
                    jl.no_of_recruitment_report as measure,
                    jl.job_id,
                    jl.user_id,
                    jl.site_id,
                    jl.department_id,
                    jl.creation_date
            FROM hr_request_job_line as jl
            );
        ''')
