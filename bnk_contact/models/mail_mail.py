# -*- coding: utf-8 -*-
from odoo import api, fields, models


class MailMail(models.Model):
    _inherit = 'mail.mail'

    @api.model
    def create(self, val):
        check_mail_server = self.env['ir.mail_server'].search([], order='sequence', limit=1)
        mail = super(MailMail, self).create(val)
        if not check_mail_server:
            return mail
        host = check_mail_server.smtp_host.split('.')
        if 'outlook' in host or 'office365' in host:
            mail.reply_to = mail.email_from
            mail.email_from = check_mail_server.smtp_user
        return mail
