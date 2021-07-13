# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'BnK HR Report',
    'version': '12.0',
    'author': 'SKY Team',
    'category': 'HR',
    'sequence': 7,
    'summary': 'Customize hr report',
    'description': "",
    'depends': [
        'bnk_hr', 'report_xlsx'
    ],
    'data': [
        # 'security/ir.model.access.csv',
        'views/payslip_excel.xml',
        'views/payslip_graph.xml',
    ],
    'demo': [
    ],
    'qweb': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
