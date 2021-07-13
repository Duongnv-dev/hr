from odoo import models, fields, api, tools
from odoo.exceptions import ValidationError
import datetime

class MaintenanceRequest(models.Model):
    _inherit ="maintenance.request"

    asset_id = fields.Many2one('account.asset.asset', track_visibility='onchange')
    asset_category_id = fields.Many2one('account.asset.category', track_visibility='onchange')
    asset_location = fields.Many2one('bnk.location', related="asset_id.location_id", track_visibility='onchange')