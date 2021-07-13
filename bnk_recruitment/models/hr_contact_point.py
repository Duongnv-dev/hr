from odoo import models, fields, api, _


class HrContactPoint(models.Model):
    _name = 'contact.point'
    _description = 'Contact Point'

    name = fields.Char(string='Contact Point')
    phone_number = fields.Char(string='Phone Number')
    mail_contact = fields.Char(string='Email')
