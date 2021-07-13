# -*- coding: utf-8 -*-
import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.multi
    def get_contractual_working_time(self):
        domain = [('employee_id', 'in', self._ids),
                  ('state', '=', 'open')]
        contracts = self.env['hr.contract'].sudo().search(domain)
        res = {}
        for contract in contracts:
            employee_id = contract.employee_id.id
            if not res.get(employee_id, False):
                res[employee_id] = []
            res[employee_id].append({'start': contract.date_start,
                                     'end': contract.date_end})
        return res

    @api.multi
    def check_contractual_working_time(self, working_time_dict, date_item):
        if self.id == 'Undefine':
            return True

        self.ensure_one()
        if isinstance(date_item, str):
            date_item = datetime.datetime.strptime(date_item, '%Y-%m-%d').date()

        employee_working_time = working_time_dict.get(self.id, [])
        for period in employee_working_time:
            if not period['end']:
                if period['start'] <= date_item:
                    return True
            elif period['start'] <= date_item <= period['end']:
                return True
        return False
