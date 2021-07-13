# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'BnK Recruitment',
    'version': '1.0',
    'author': 'Erp Team',
    'category': 'HR',
    'sequence': 8,
    'summary': 'Customize recruitment',
    'description': "",
    'depends': [
        'hr', 'hr_recruitment', 'bnk_employee', 'bnk_hr',
    ],
    'data': [
        'data/mail_data.xml',
        'data/ir_cron.xml',
        'data/mail_interview.xml',
        'data/mail_onboard.xml',
        'data/mail_thankyou_and_refuse.xml',
        'data/hr_recruitment_data.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/hr_job.xml',
        'views/company.xml',
        'views/contact_point.xml',
        'views/export_jd_action.xml',
        'views/hr_recruitment_request.xml',
        'views/hr_applicant.xml',
        'views/hr_employee.xml',
        'views/hr_job_line_report_view.xml',
        'report/template_offer.xml',
        'data/mail_offer.xml',
        'wizard/applicant_refuse_reason_views.xml',
    ],
    'css': [
        # 'static/src/css/list_style_type_property.css'
    ],
    'demo': [
    ],
    'qweb': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
