# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'BnK HR',
    'version': '1.0',
    'author': 'SKY Team',
    'category': 'HR',
    'sequence': 7,
    'summary': 'Customize hr',
    'description': "",
    'depends': [
        'hr', 'hr_contract', 'mail', 'hr_holidays', 'toolz', 'hr_recruitment', 'bnk_employee'
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/record_rule.xml',
        'security/hr_contract_security.xml',
        'data/ir_cron_data.xml',
        'data/remind_expired_contract_template.xml',
        'data/hr_holidays_datas.xml',
        'data/payroll_rule_data.xml',
        'data/payroll_structure.xml',
        'data/auto_create_period.xml',
        # 'data/email_template.xml',
        'report/contact_template.xml',
        'views/res_config_setting.xml',
        'views/public_holiday.xml',
        'report/contract_template_probationary.xml',
        'views/hr_payslip.xml',
        # 'views/hr_onboarding_checklist_line.xml',
        # 'views/hr_onboarding_checklist.xml',
        # 'views/item_checklist.xml',
        'views/hr_applicant_views.xml',
        'views/hr_allowance.xml',
        'views/hr_contributor_hour.xml',
        'views/hr_holidays.xml',
        'views/template_css.xml',
        'views/hr_leave_type.xml',
        'views/hr_payslip_employees.xml',
        'views/hr_payslip_run.xml',
        'views/hr_period.xml',
    ],
    'css': ['static/src/css/list_style_type_property.css'],
    'demo': [
    ],
    'qweb': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
