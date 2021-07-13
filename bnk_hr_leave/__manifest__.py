# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Extend Leaves',
    'version': '12.0',
    'author': 'SKY Team',
    'category': 'HR',
    'sequence': 7,
    'summary': 'Customize leave',
    'description': "",
    'depends': [
        'bnk_hr',
    ],
    'data': [
        # 'data/leave_type.xml',
        # 'data/auto_gen_leave.xml',
        # 'security/ir.model.access.csv',
        # 'views/contract_leave.xml',
        'views/resource_views.xml',
        'views/hr_leave_views.xml',
    ],
    'demo': [
    ],
    'qweb': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
