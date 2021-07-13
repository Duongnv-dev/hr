# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, tools
from odoo.addons.website.controllers.main import QueryURL
from odoo.http import request
from odoo.addons.website_sale.controllers.main import TableCompute


class SliderConfig(models.Model):
    _name = 'slider.config'
    _order = 'priority'

    name = fields.Char()
    image = fields.Binary(required=True, attachment=True)
    image_url = fields.Char(compute='get_image_url')
    priority = fields.Integer(default=0)
    use = fields.Boolean(string='Active', default=True)

    def get_image_url(self):
        for slider in self:
            slider.image_url = '/web/image/slider.config/{}/image'.format(slider.id)


class Website(models.Model):
    _inherit = 'website'

    def get_homepage_slider_data(self):
        slides = self.env['slider.config'].search([('use', '=', True)])

        return slides
