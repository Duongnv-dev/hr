# -*- coding: utf-8 -*-
import base64
import datetime
from datetime import date
from odoo import api, fields, models, _, modules, tools
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT


class AllocateResource(models.Model):
    _name = 'allocate.resource'
    _rec_name = 'employee_id'

    @api.depends('project_id.training')
    def _compute_training(self):
        for a in self:
            a.training = a.project_id.training

    @api.depends('project_id.available')
    def _compute_available(self):
        for a in self:
            a.available = a.project_id.available

    date = fields.Date(required=True)
    project_id = fields.Many2one('project.project', 'Project', required=True,
                                 ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', 'Employee', ondelete='cascade')
    percent = fields.Float(default=100)
    billable = fields.Selection([('none', 'None'), ('billable', 'Billable'),
                                 ('investment', 'Investment')], default='billable',
                                required=True)
    user_id = fields.Many2one('res.users', related='project_id.user_id',
                              store=True, readonly=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True,
                                 related='project_id.company_id', store=True)
    site_id = fields.Many2one('hr.site', 'Site', readonly=True,
                              related='employee_id.site_id', store=True)

    lock = fields.Boolean(default=False, readonly=True, compute='_compute_lock', store=True)
    active = fields.Boolean(default=True)
    editable = fields.Boolean(compute='_compute_editable')

    ot = fields.Boolean()
    ot_type = fields.Selection([('normal', 'Normal'),
                                ('weekend', 'Weekend'),
                                ('holiday', 'Holiday')], default='normal')
    training = fields.Boolean(compute='_compute_training', store=True)
    available = fields.Boolean(compute='_compute_available', store=True)

    @api.multi
    def save(self):
        # print('save {}'.format(self))
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    # @api.model
    # def create(self, vals):
    #     print(vals)
    #     print(self._context)
    #
    #     if self._context.get('default_project_id', False) \
    #             and not vals.get('project_id', False):
    #         vals['project_id'] = self._context.get('default_project_id', False)
    #
    #     return super(AllocateResource, self).create(vals)

    @api.depends('project_id.lock_date_ids.date')
    def _compute_lock(self):
        projects = self.mapped('project_id')
        lock_dict = projects.get_lock_dict()

        for allocate in self:
            if not allocate.date:
                continue
            allocate.lock = allocate.date.strftime(DEFAULT_SERVER_DATE_FORMAT) \
                            in lock_dict.get(allocate.project_id.id, [])

    _sql_constraints = [
        ('percent_check', 'check (percent >=0)',
         'The percent must be >= 0!'),
    ]

    @api.depends('lock')
    def _compute_editable(self):
        is_sm = self.env.user.has_group('bnk_project.group_allocate_resource_sm')
        for allocate in self:
            allocate.editable = not allocate.lock or is_sm

    @api.multi
    @api.constrains('employee_id', 'date')
    def _check_reconcile(self):
        leave_project = self.env.ref('bnk_project.project_leave_data')
        if leave_project:
            if self.project_id.id == leave_project.id:
                return

        def get_date(from_date, to_date, type='min'):
            if isinstance(from_date, str):
                from_date = datetime.datetime(from_date, '%Y-%m-%d')
            if isinstance(to_date, str):
                to_date = datetime.datetime(to_date, '%Y-%m-%d')

            if type == 'min':
                return min(from_date, to_date)

            if type == 'max':
                return max(from_date, to_date)

        from_date = False
        to_date = False
        employee_name_dict = {}
        employee_ids = []
        for allocate in self:
            employee_id = allocate.employee_id.id
            date = allocate.date
            employee_name_dict[str(employee_id)] = allocate.employee_id.name

            if employee_id not in employee_ids:
                employee_ids.append(employee_id)

            if not from_date:
                from_date = date
            else:
                from_date = get_date(from_date, date, 'min')
            if not to_date:
                to_date = date
            else:
                to_date = get_date(to_date, date, 'max')

        error_dict = {}

        domain = [
            ('state', 'in', ('validate', 'validate1')),
            ('request_unit_half', '=', False),
            ('holiday_type', '=', 'employee'),
            ('employee_id', 'in', employee_ids),
            '&', '|',
            ('request_date_from', '>=', from_date),
            ('request_date_to', '<=', from_date),
            '&',
            ('request_date_from', '>=', to_date),
            ('request_date_to', '<=', to_date)
        ]
        leaves = self.env['hr.leave'].search(domain)

        for leave in leaves:
            employee_id = leave.employee_id.id
            if employee_id not in employee_ids:
                continue

            if not error_dict.get(str(employee_id), False):
                error_dict[str(employee_id)] = []
            error_dict[str(employee_id)].append(leave)

        if not error_dict:
            return True

        message = _('Error: employee had leaves, detail:')
        for employee_id in error_dict.keys():
            employee_name = employee_name_dict[employee_id]
            message = message + '{}: '.format(employee_name)
            for leave in error_dict[employee_id]:
                message = message + _('{} to {},').format(leave.request_date_from, leave.request_date_to)
        raise ValidationError(message)


class ProjectLockDate(models.Model):
    _name = 'project.lock.date'

    project_id = fields.Many2one('project.project', required=True)
    date = fields.Date(required=True)


class ProjectMember(models.Model):
    _name = 'project.member'

    project_id = fields.Many2one('project.project')
    member_id = fields.Many2one('hr.employee')
    project_role_id = fields.Many2one('project.role')
    date_start = fields.Date(required=True)
    date_end = fields.Date(required=True)
    billable = fields.Float(compute='_compute_billable')

    def _compute_billable(self):
        if self[0]:
            proj_id = self[0].project_id.id
            domain_resouce = [
                ('project_id', '=', proj_id),
                ('billable', '=', 'billable'),
            ]
            emp_sum_resource = self.env['allocate.resource'].read_group(domain_resouce, ['employee_id', 'percent'], ['employee_id'])
            member_billable_dict = {}
            for rec in emp_sum_resource:
                if rec.get('employee_id', False):
                    member_billable_dict[rec['employee_id'][0]] = rec.get('percent')/100
                else:
                    member_billable_dict[0] = rec.get('percent') / 100

            for member in self:
                member.billable = member_billable_dict.get(member.member_id.id, False)

    @api.onchange('member_id')
    def _onchange_employee(self):
        res = {}
        list_emp = self.env['hr.employee'].search([])
        members_prj = self.project_id.employee_ids - self.project_id.employee_ids[-1]
        for rec in members_prj:
            list_emp -= rec.member_id

        res['domain'] = {'member_id': [('id', 'in', list_emp.ids)]}
        return res


class ProjectRole(models.Model):
    _name = 'project.role'

    name = fields.Char(required=True)
    project_id = fields.Many2one('project.project')
    cost = fields.Float(string='Cost', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=lambda self: self.env.user.company_id.currency_id)


class Project(models.Model):
    _name = 'project.project'
    _inherit = ['project.project', 'mail.thread', 'mail.activity.mixin']

    @api.multi
    def get_lock_dict(self):
        lock_date_ids = self.mapped('lock_date_ids')

        lock_dict = {}
        for lock_date in lock_date_ids:
            if not lock_dict.get(lock_date.project_id.id, False):
                lock_dict[lock_date.project_id.id] = []

            lock_dict[lock_date.project_id.id].append(
                lock_date.date.strftime(DEFAULT_SERVER_DATE_FORMAT)
            )
        return lock_dict

    billable_plan = fields.Float()
    update_billable = fields.Float(track_visibility='onchange')
    date_end = fields.Date()
    allocate_resource_ids = fields.One2many('allocate.resource', 'project_id', 'Allocate resources')
    allocate_resource_count = fields.Integer(compute='_compute_allocate_resource_count')
    is_sm_project_manager_project_user = fields.Boolean(
        compute='_compute_is_sm_project_manager_project_user')
    employee_ids = fields.One2many('project.member', 'project_id')

    uptodate_effort = fields.Float(compute='_compute_uptodate_effort')
    ee_uptodate = fields.Float(compute='_compute_ee_uptodate')

    forecast_effort = fields.Float(compute='_compute_forecast_effort')
    ee_forecast = fields.Float(compute='_compute_ee_forecast')
    exceeded_effort_image = fields.Binary("Dangerous Image", compute='_compute_exceeded_effort_image')
    forecast_billable = fields.Float(compute='_compute_forecast_billable')
    project_role_ids = fields.One2many('project.role', 'project_id')

    lock_date_ids = fields.One2many('project.lock.date', 'project_id', readony=True)
    remaining_billable = fields.Float(compute='cp_remaining_billable')
    uptodate_billable = fields.Float(compute='cp_uptodate_billable')
    training = fields.Boolean(default=False)
    available = fields.Boolean(default=False)

    @api.model
    def default_get(self, fields_list):
        res = super(Project, self).default_get(fields_list)
        res['privacy_visibility'] = 'followers'
        res['is_sm_project_manager_project_user'] = True
        return res

    @api.depends('allocate_resource_ids.billable')
    def _compute_forecast_billable(self):
        query = """
            select project_id, sum(percent)
            from allocate_resource
            where project_id in ({})
             and billable = 'billable'
            group by project_id
        """.format(','.join([str(project_id) for project_id in self._ids]))
        self.env.cr.execute(query)
        result = self.env.cr.fetchall()
        result_dict = dict((row[0], row[1] or 0) for row in result)

        for project in self:
            project.forecast_billable = result_dict.get(project.id, 0) / 100

    def _compute_is_sm_project_manager_project_user(self):
        res = self.env.user.has_group('project.group_project_manager') \
              or self.env.user.has_group('project.group_project_user') \
              or self.env.user.has_group('bnk_project.group_allocate_resource_sm')
        for project in self:
            project.is_sm_project_manager_project_user = res

    @api.depends('allocate_resource_ids.active')
    def _compute_allocate_resource_count(self):
        for project in self:
            project.allocate_resource_count = \
                len(project.allocate_resource_ids)

    @api.onchange('billable_plan')
    def change_billable_plan(self):
        if not self.update_billable:
            self.update_billable = self.billable_plan

    @api.multi
    @api.depends('allocate_resource_ids')
    def _compute_uptodate_effort(self):
        if self.id:
            self.uptodate_effort = (self.get_uptodate_effort() or 0.0) / 100

    @api.multi
    @api.depends('uptodate_effort')
    def _compute_ee_uptodate(self):
        if self.id:
            uptodate_effort_billable = (self.get_uptodate_effort_billable() or 0.0) / 100
            if not self.uptodate_effort:
                self.ee_uptodate = 0.0
            else:
                self.ee_uptodate = (uptodate_effort_billable / self.uptodate_effort) * 100

    def get_uptodate_effort(self):
        today = date.today()
        today = today.strftime('%Y-%m-%d')
        query = """select sum(percent)
                            from allocate_resource
                            where project_id = {} and date <= '{}'""".format(self.id, today)
        self.env.cr.execute(query)
        data = self.env.cr.fetchone()
        return data[0]

    def get_uptodate_effort_billable(self):
        today = date.today()
        today = today.strftime('%Y-%m-%d')
        query = """
                    select sum(percent)
                    from allocate_resource
                    where project_id = {} and billable= 'billable' and date <= '{}'
                    """.format(self.id, today)
        self.env.cr.execute(query)
        data = self.env.cr.fetchone()
        return data[0]

    @api.multi
    @api.depends('allocate_resource_ids')
    def _compute_forecast_effort(self):
        if self.id:
            self.forecast_effort = (self.get_forecast_effort() or 0.0) / 100

    @api.multi
    @api.depends('forecast_effort')
    def _compute_ee_forecast(self):
        if self.id:
            forecast_effort_billable = (self.get_forecast_effort_billable() or 0.0) / 100
            if not self.forecast_effort:
                self.ee_forecast = 0.0
            else:
                self.ee_forecast = (forecast_effort_billable / self.forecast_effort) * 100

    def get_forecast_effort(self):
        query = """select sum(percent)
                            from allocate_resource
                            where project_id = {}""".format(self.id)
        self.env.cr.execute(query)
        data = self.env.cr.fetchone()
        return data[0]

    def get_forecast_effort_billable(self):
        query = """
                    select sum(percent)
                    from allocate_resource
                    where project_id = {} and billable= 'billable'
                    """.format(self.id)
        self.env.cr.execute(query)
        data = self.env.cr.fetchone()
        return data[0]

    @api.multi
    @api.depends('update_billable', 'forecast_effort')
    def _compute_exceeded_effort_image(self):
        if self.forecast_effort > self.update_billable:
            image_path = modules.get_module_resource('bnk_project', 'static/src/img', 'dangerous.png')
            self.exceeded_effort_image = tools.image_resize_image_small(base64.b64encode(open(image_path, 'rb').read()))
        else:
            self.exceeded_effort_image = False

    def quick_allocate(self):
        action_obj = self.env.ref('bnk_project.action_wizard_quick_allocate')
        action = action_obj.read([])[0]
        alocate_line_ids = []
        for memb in self.employee_ids:
            val = {'percent': 100, 'billable': 'billable'}
            if memb.member_id:
                val['employee_id'] = memb.member_id.id
            if memb.date_start:
                val['from_date'] = memb.date_start
            if memb.date_end:
                val['to_date'] = memb.date_end
            alocate_line_ids.append((0, 0, val))
        if alocate_line_ids:
            action['context'] = {'default_project_id': self.id, 'default_allocate_line_ids': alocate_line_ids}
        return action

    @api.depends()
    def cp_remaining_billable(self):
        for s in self:
            if not s.allocate_resource_ids:
                continue
            query = '''SELECT sum(percent) AS percent FROM allocate_resource WHERE date <= '{}' AND project_id = {} 
            AND billable = '{}';'''.format(datetime.datetime.today().date(), s.id, 'billable')
            s.env.cr.execute(query)
            value = s.env.cr.dictfetchall()[0]
            if not value['percent']:
                s.remaining_billable = 0
                continue
            total_allocate = value['percent']/100
            remaining = s.update_billable - total_allocate
            s.remaining_billable = remaining

    @api.depends()
    def cp_uptodate_billable(self):
        for s in self:
            if not s.allocate_resource_ids:
                continue
            query = '''SELECT sum(percent) AS percent FROM allocate_resource WHERE date <= '{}' AND project_id = {} 
            AND billable = '{}';'''.format(datetime.datetime.today().date(), s.id, 'billable')
            s.env.cr.execute(query)
            value = s.env.cr.dictfetchall()[0]
            if not value['percent']:
                s.uptodate_billable = 0
                continue
            uptodate_billable = value['percent']/100
            s.uptodate_billable = uptodate_billable
