# -*- coding: utf-8 -*-
# This file is part of Odoo. The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.
{
    'name': 'HR payroll adjustment',
    'version': '14.0.0.0.1',
    'author': 'BnK Solution, Inc.',
    'category': 'HR',
    'sequence': 15,
    'website': 'https://www.bnksolution.com',
    'licence': 'AGPL-3',
    'summary': 'Customizations for HR Package',
    'depends': [
        'bnk_hr',
    ],
    'css': [

    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_payroll_adjustment.xml',
    ],
    'qweb': [

    ],
    'installable': True,
    'application': True,
    'auto_install': False,

}
