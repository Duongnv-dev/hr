from odoo import models, fields, api, tools
from odoo.exceptions import ValidationError
import datetime

class AssetRequestLine(models.Model):
    _name = 'request.line'
    _description = "Asset Request Line"

    asset_request_id = fields.Many2one('asset.request', "Asset Request")
    asset_id = fields.Many2one('account.asset.asset', "Asset")
    note = fields.Text(max=255)
    from_location = fields.Many2one('bnk.location', "From Location", related='asset_id.location_id')
    to_location = fields.Many2one('bnk.location', "To Location")
    start_date = fields.Date(string="Start Date", default=datetime.date.today())
    end_date = fields.Date(string="End Date")
    type = fields.Selection([('request', 'Request Asset'), ('return', 'Return Asset')], related='asset_request_id.type')

    @api.onchange('asset_id', 'asset_id.location_id')
    def _onchange_request_type(self):
        if self.asset_id:
            self.from_location = self.asset_id.location_id

    @api.model
    def create(self, vals):
        res = super(AssetRequestLine, self).create(vals)
        res.asset_id.check_duplicate_asset = True
        return res


class AssetRequest(models.Model):
    _name = 'asset.request'
    _description = "Asset Request"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def get_default_user(self):
        return self.env.user.id

    def get_default_employee(self):
        empl = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)])
        if not empl:
            return
        return empl[0].id

    def default_manager(self):
        return self.env.ref('bnk_asset.group_by_assets_manager').id

    name = fields.Char(track_visibility='onchange', compute='_compute_name')
    code = fields.Char()
    description = fields.Text(string="Description", track_visibility='onchange')
    user_id = fields.Many2one('res.users', string='Requester', default=get_default_user, track_visibility='onchange')
    employee_id = fields.Many2one('hr.employee', 'Employee Used', required=True, default=get_default_employee, track_visibility='onchange')
    asset_request_line_ids = fields.One2many('request.line', 'asset_request_id', "Asset list",
                                             track_visibility='onchange')
    type = fields.Selection([('request', 'Request Asset'), ('return', 'Return Asset')],
                            default='request', track_visibility='onchange', required = True)
    state = fields.Selection([('draft', 'Draft'), ('waiting', 'Waiting'), ('confirm', 'Confirm'),
                              ('approve', 'Approve'), ('reject', 'Reject'), ('done', 'Done'),('cancel','Cancel')], default='draft',
                             track_visibility='onchange')
    receiver = fields.Many2one('res.users', 'Approvers', required=True)
    manager_group_id = fields.Many2one('res.groups', compute="_compute_get_manager", default=default_manager)

    @api.model
    def create(self, vals):
        res = super(AssetRequest, self).create(vals)
        res.code = self.env['ir.sequence'].next_by_code('line.code') or '/'
        return res

    @api.multi
    def _compute_get_manager(self):
        for request in self:
            request.manager_group_id = self.env.ref('bnk_asset.group_by_assets_manager').id

    @api.depends('type')
    def _compute_name(self):
        for rec in self:
            if rec.code:
                if rec.type == 'request':
                    rec.name = 'RQ/' + str(rec.code)
                else:
                    rec.name = 'RT/' + str(rec.code)

    @api.onchange('asset_request_line_ids')
    def check_request_line_unique(self):
        current_list = []
        current_ids = self.asset_request_line_ids
        for crr in current_ids:
            current_list.append(crr.asset_id.id)
        if len(current_list) != len(list(set(current_list))):
            raise ValidationError(
                "Each product only allowed to choose once")

    @api.multi
    def action_confirm(self):
        vals = {
            'res_id': self.id,
            'activity_type_id': self.env['mail.activity.type'].search([('name', '=', 'To Do')]).id,
            'summary': 'Confirm Request Asset',
            'note': 'Your request has been confirmed successfully',
            'user_id': self.user_id.id,
            'res_model_id': self.env['ir.model'].search([('model', '=', self._name)]).id,
        }
        self.env['mail.activity'].create(vals)
        self.write({'state': 'confirm'})

    @api.multi
    def action_cancel(self):
        vals = {
            'res_id': self.id,
            'activity_type_id': self.env['mail.activity.type'].search([('name', '=', 'To Do')]).id,
            'summary': 'Cancel Request Asset',
            'note': 'Your request has been canceled',
            'user_id': self.user_id.id,
            'res_model_id': self.env['ir.model'].search([('model', '=', self._name)]).id,
        }
        self.env['mail.activity'].create(vals)
        self.write({'state': 'cancel'})

    @api.multi
    def action_approve(self):
        if self.asset_request_line_ids:
            if self.type == 'request':
                for line in self.asset_request_line_ids:
                    line.asset_id.user = self.user_id
                    line.asset_id.employee_id = self.employee_id
                    if line.to_location:
                        line.asset_id.location_id = line.to_location
                    else:
                        line.asset_id.location_id = line.from_location
                vals = {
                    'res_id': self.id,
                    'activity_type_id': self.env['mail.activity.type'].search([('name', '=', 'To Do')]).id,
                    'summary': 'Approved Request',
                    'note': 'Manager have just accepted your request asset',
                    'user_id': self.user_id.id,
                    'res_model_id': self.env['ir.model'].search([('model', '=', self._name)]).id,
                }
                self.env['mail.activity'].create(vals)
                self.write({'state': 'approve'})
            elif self.type == 'return':
                for line in self.asset_request_line_ids:
                    line.asset_id.employee_id = False
                    if line.to_location:
                        line.asset_id.location_id = line.to_location
                    else:
                        line.asset_id.location_id = line.from_location
                vals = {
                    'res_id': self.id,
                    'activity_type_id': self.env['mail.activity.type'].search([('name', '=', 'To Do')]).id,
                    'summary': 'Approved Request',
                    'note': 'Manager have just accepted your return asset',
                    'user_id': self.user_id.id,
                    'res_model_id': self.env['ir.model'].search([('model', '=', self._name)]).id,
                }
                self.env['mail.activity'].create(vals)
                self.write({'state': 'approve'})
        else:
            raise ValidationError("Please select asset")

    @api.multi
    def action_submit(self):
        vals = {
            'res_id': self.id,
            'activity_type_id': self.env['mail.activity.type'].search([('name', '=', 'To Do')]).id,
            'summary': 'Submit request asset',
            'note': 'You have a new request asset',
            'user_id': self.receiver.id,
            'res_model_id': self.env['ir.model'].search([('model', '=', self._name)]).id,
        }
        self.env['mail.activity'].create(vals)
        self.write({'state': 'waiting'})

    @api.multi
    def action_reject(self):
        if self.type:
            vals = {
                'res_id': self.id,
                'activity_type_id': self.env['mail.activity.type'].search([('name', '=', 'To Do')]).id,
                'summary': 'Rejected request asset',
                'note': 'Manager have just rejected your request asset',
                'user_id': self.user_id.id,
                'res_model_id': self.env['ir.model'].search([('model', '=', self._name)]).id,
            }
            self.env['mail.activity'].create(vals)
            self.write({'state': 'reject'})
        else:
            pass

    @api.multi
    def action_get_asset(self):
        val1 = {
            'res_id': self.id,
            'activity_type_id': self.env['mail.activity.type'].search([('name', '=', 'To Do')]).id,
            'summary': 'Done Request Asset',
            'note': 'The employee have been received Assets',
            'user_id': self.receiver.id,
            'res_model_id': self.env['ir.model'].search([('model', '=', self._name)]).id,
        }
        self.env['mail.activity'].create(val1)
        val2 = {
            'res_id': self.id,
            'activity_type_id': self.env['mail.activity.type'].search([('name', '=', 'To Do')]).id,
            'summary': 'Done Request Asset',
            'note': 'The employee have been received Assets',
            'user_id': self.user_id.id,
            'res_model_id': self.env['ir.model'].search([('model', '=', self._name)]).id,
        }
        self.env['mail.activity'].create(val2)
        self.write({'state': 'done'})