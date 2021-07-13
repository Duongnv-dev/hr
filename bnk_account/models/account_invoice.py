
from odoo import api, fields, models
from num2words import num2words


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    contract_no = fields.Text()
    contract_date = fields.Date()
    description_of_goods = fields.Text()

    def num_to_words(self, number, lang_code, currency_name):
        lang_code = str(lang_code)
        currency_symbol = self.env['res.currency'].search([('name', '=', currency_name)]).symbol
        in_words = num2words(number, lang=lang_code).capitalize() + ' ' + currency_symbol
        return in_words

    def check_japan(self, lang_code):
        if str(lang_code) == 'ja_JP':
            return True
        else:
            return False

    def validate_address(self, address):
        address.strip(address)
        address_new = list(address)
        for i in range(0, len(address_new)):
            if address_new[0].isalpha() or address_new[0].isdigit():
                break
            else:
                del(address_new[0])
        s = "".join(address_new)

        return s

    def convert_name(self, name):
        converted_name = self.env['process.string'].no_accent(name)
        return converted_name

    @api.multi
    def action_invoice_sent(self):
        """ Open a window to compose an email, with the edi invoice template
            message loaded by default
        """
        self.ensure_one()
        # noi dung mail
        template = self.env.ref('bnk_account.email_template_edit_invoice', False)
        # noi dung wizard form
        compose_form = self.env.ref('account.account_invoice_send_wizard_form', False)
        ctx = dict(
            default_model='account.invoice',
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template and template.id or False,
            default_composition_mode='comment',
            mark_invoice_as_sent=True,
            custom_layout="mail.mail_notification_paynow",
            force_email=True
        )
        return {
            'name': 'Send Invoice',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.invoice.send',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    swift_code = fields.Char()
