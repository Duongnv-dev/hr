# -*- coding: utf-8 -*-
# This file is part of Odoo. The COPYRIGHT file at the top level of
# this module contains the full copyright notices and license terms.
{
    'name': 'HR employee',
    'version': '14.0.0.0.1',
    'author': 'BnK Solution, Inc.',
    'category': 'HR',
    'sequence': 9,
    'website': 'https://www.bnksolution.com',
    'licence': 'AGPL-3',
    'summary': 'Customizations for HR Package',
    'depends': [
        'hr', 'hr_payroll', 'hr_contract', 'report_xlsx'
    ],
    'css': [

    ],
    'data': [
        'security/ir.model.access.csv',
        'data/hr_contract_data.xml',
        'data/ir_sequence_data.xml',
        'data/employee_security.xml',
        'data/remind_birthday_employee_template.xml',
        'views/hr.xml',
        'views/hr_employee.xml',
        'views/hr_employee_card.xml',
        'views/hr_employee_move.xml',
        'views/hr_employee_view.xml',
        'views/hr_employee_resigned.xml',
        'views/hr_contract_config.xml',
        'views/hr_contract_views.xml',
        'reports/employee_reports.xml',
        'views/res_partner_bank.xml',
        'views/hr_contract_template.xml',
        'views/setting.xml',
        'views/hr_department.xml',
    ],
    'qweb': [

    ],
    'installable': True,
    'application': True,
    'auto_install': False,

}
