# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'BnK Website',
    'version': '1.0',
    'author': 'BnKsolution',
    'category': 'Project',
    'sequence': 8,
    'summary': 'Customize project',
    'description': "BnK project",
    'depends': [
        'website'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/homepage.xml',
        'views/homepage_slider_view.xml',
        'templates/homepage_slider.xml',
    ],
    'external_dependencies': {
    },
    'demo': [
    ],
    'qweb': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}