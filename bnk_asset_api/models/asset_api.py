# -*- coding: utf-8 -*-
import json

from odoo import api, fields, models, _
from datetime import datetime
from calendar import monthrange
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class AccountAssetAsset(models.Model):
    _inherit = 'account.asset.asset'

    def _compute_json_message(self):
        domain = [
            ('res_id', 'in', self._ids),
            ('model', '=', 'account.asset.asset'),
        ]
        message_fields = [
            'body',
            'subject',
            'date',
            'author_id',
            'res_id',
        ]
        messages = self.env['mail.message'].search_read(domain, message_fields)

        message_dict = {}
        for message in messages:
            if isinstance(message['date'], datetime):
                message['date'] = message['date'].strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            asset_id = message['res_id']

            message.pop('res_id', None)

            if not message_dict.get(asset_id, False):
                message_dict[asset_id] = []

            message_dict[asset_id].append(message)

        for asset in self:
            asset_messages = message_dict.get(asset.id, [])

            asset.json_message = json.dumps(asset_messages)

    json_message = fields.Char(compute='_compute_json_message')

