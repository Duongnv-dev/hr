from odoo import models, fields, api, _


class HrContract(models.Model):
    _inherit = 'hr.contract'

    def get_default_eat_inc(self):
        config = self.env['hr.contract.config'].search([])
        eat_inc = 0
        if not config:
            return eat_inc
        eat_inc = config[-1].eat_inc
        return eat_inc

    def get_default_phone_inc(self):
        config = self.env['hr.contract.config'].search([])
        phone_inc = 0
        if not config:
            return phone_inc
        phone_inc = config[-1].phone_inc
        return phone_inc

    def get_default_work_allo_inc(self):
        config = self.env['hr.contract.config'].search([])
        work_allo_inc = 0
        if not config:
            return work_allo_inc
        work_allo_inc = config[-1].work_allo_inc
        return work_allo_inc

    def get_default_poison_inc(self):
        config = self.env['hr.contract.config'].search([])
        poison_inc = 0
        if not config:
            return poison_inc
        poison_inc = config[-1].poison_inc
        return poison_inc

    def get_default_ins_inc(self):
        config = self.env['hr.contract.config'].search([])
        ins_inc = 0
        if not config:
            return ins_inc
        ins_inc = config[-1].ins_inc
        return ins_inc

    def get_default_uni_inc(self):
        config = self.env['hr.contract.config'].search([])
        uni_inc = 0
        if not config:
            return uni_inc
        uni_inc = config[-1].uni_inc
        return uni_inc

    def get_default_is_eat_inc(self):
        config = self.env['hr.contract.config'].search([])
        is_eat_inc = False
        if not config:
            return is_eat_inc
        is_eat_inc = config[-1].is_eat_inc
        return is_eat_inc

    def get_default_is_phone_inc(self):
        config = self.env['hr.contract.config'].search([])
        is_phone_inc = False
        if not config:
            return is_phone_inc
        is_phone_inc = config[-1].is_phone_inc
        return is_phone_inc

    def get_default_is_work_allo_inc(self):
        config = self.env['hr.contract.config'].search([])
        is_work_allo_inc = False
        if not config:
            return is_work_allo_inc
        is_work_allo_inc = config[-1].is_work_allo_inc
        return is_work_allo_inc

    def get_default_is_poison_inc(self):
        config = self.env['hr.contract.config'].search([])
        is_poison_inc = False
        if not config:
            return is_poison_inc
        is_poison_inc = config[-1].is_poison_inc
        return is_poison_inc

    def get_default_is_ins_inc(self):
        config = self.env['hr.contract.config'].search([])
        is_ins_inc = False
        if not config:
            return is_ins_inc
        is_ins_inc = config[-1].is_ins_inc
        return is_ins_inc

    def get_default_is_uni_inc(self):
        config = self.env['hr.contract.config'].search([])
        is_uni_inc = False
        if not config:
            return is_uni_inc
        is_uni_inc = config[-1].is_uni_inc
        return is_uni_inc

    is_eat_inc = fields.Boolean(default=get_default_is_eat_inc)
    is_phone_inc = fields.Boolean(default=get_default_is_phone_inc)
    is_work_allo_inc = fields.Boolean(default=get_default_is_work_allo_inc)
    is_poison_inc = fields.Boolean(default=get_default_is_poison_inc)
    is_ins_inc = fields.Boolean(default=get_default_is_ins_inc)
    is_uni_inc = fields.Boolean(default=get_default_is_uni_inc)

    eat_inc = fields.Float(string='Meal', default=get_default_eat_inc)
    phone_inc = fields.Float(string='Telephone', default=get_default_phone_inc)
    work_allo_inc = fields.Float(string='Travel Allowance', default=get_default_work_allo_inc)
    poison_inc = fields.Float(string='Other Compensation', default=get_default_poison_inc)
    ins_inc = fields.Float(string='Insurance Benefits (Unemployment/Sick/Maternity)', default=get_default_ins_inc)
    uni_inc = fields.Float(string='Uniform Allowance', default=get_default_uni_inc)


class HrContractTemplate(models.Model):
    _inherit = 'hr.contract.config'

    # Allowance Information
    eat_inc = fields.Float(string='Meal')
    phone_inc = fields.Float(string='Telephone')
    work_allo_inc = fields.Float(string='Travel Allowance')
    poison_inc = fields.Float(string='Other Compensation')
    ins_inc = fields.Float(string='Insurance Benefits (Unemployment/Sick/Maternity)')
    uni_inc = fields.Float(string='Uniform Allowance')

    # Taxable Checking
    is_eat_inc = fields.Boolean(default=True)
    is_phone_inc = fields.Boolean(default=False)
    is_work_allo_inc = fields.Boolean(default=False)
    is_poison_inc = fields.Boolean(default=False)
    is_ins_inc = fields.Boolean(default=False)
    is_uni_inc = fields.Boolean(default=True)

