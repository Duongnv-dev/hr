# -*- coding: utf-8 -*-
# This file is part of Odoo. The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.
{
    'name': 'HR employee report',
    'version': '1.0',
    'author': 'ERP Team.',
    'category': 'HR',
    'sequence': 25,
    'website': 'https://www.bnksolution.com',
    'summary': 'Customizations for Hr Employee Report',
    'depends': [
        'bnk_hr', 'bnk_employee'
    ],
    'css': [

    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_employee_report.xml',
        'views/hr_emp_report_realtime.xml',
    ],
    'qweb': [

    ],
    'installable': True,
    'application': True,
    'auto_install': False,

}
