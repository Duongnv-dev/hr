# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'BnK Contact',
    'version': '1.0',
    'author': 'ERP Team',
    'category': 'Contact',
    'sequence': 8,
    'summary': 'Customize Contact',
    'description': "",
    'depends': [
        'contacts', 'calendar',
        'base'
    ],
    'data': [
        'data/hr_contact_data.xml',
        'views/contact_view.xml',
        'security/rules.xml',
    ],
    'demo': [
    ],
    'qweb': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
