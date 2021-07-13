# -*- coding: utf-8 -*-
# This file is part of Odoo. The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.
{
    'name': 'BnK recruitment website',
    'version': '1.0',
    'author': 'BnK Solution, Inc.',
    'category': 'HR',
    'sequence': 12,
    'website': 'https://www.bnksolution.com',
    'licence': '',
    'summary': 'Customizations for BnK ERP',
    'depends': [
        'website_hr_recruitment',
    ],
    'css': [

    ],
    'data': [
        'data/website_recruitment_data.xml',
        'views/resources.xml',
        'views/website_hr_recruitment_templates.xml'

    ],
    'qweb': [

    ],
    'installable': True,
    'application': True,
    'auto_install': False,

}
