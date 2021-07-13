# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class WizardAddAccountAnalytic(models.TransientModel):
    _name = 'wizard.add.account.analytic'

    invoice_line_id = fields.Many2one('account.invoice.line', required=True)
    account_analytic_id = fields.Many2one('account.analytic.account')

    @api.model
    def default_get(self, fields):
        res = super(WizardAddAccountAnalytic, self).default_get(fields)
        res['invoice_line_id'] = self._context.get('active_id')
        return res

    def confirm(self):
        if self.account_analytic_id:
            self.invoice_line_id.write({
                'account_analytic_id': self.account_analytic_id.id
            })
        return {'type': 'ir.actions.act_window_close'}
