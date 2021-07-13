
from odoo import api, fields, models, _, modules, tools


class Partner(models.Model):

    _inherit = 'res.partner'

    @api.model
    def default_get(self, fields_list):
        res = super(Partner, self).default_get(fields_list)
        res['user_id'] = self.env.user.id
        return res

    @api.model_cr
    def init(self):
        self.env.ref('base.res_partner_rule_private_employee').write({
            'domain_force':
                "[('type', '!=', 'private'), ('customer', '=', False)]"
        })