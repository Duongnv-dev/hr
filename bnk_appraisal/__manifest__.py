# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'BnK Appraisal',
    'version': '1.0',
    'author': 'BnK Team',
    'category': '',
    'sequence': 10,
    'summary': 'Customize Appraisal',
    'description': "",
    'depends': [
        'base', 'mail', 'survey', 'oh_appraisal', 'hr',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/bnk_appraisal_data.xml',
        'views/quick_appraisal_view.xml',
        'views/hr_appraisal_views.xml',
        'views/hr_employee.xml',
        'views/appraisal_answer_view.xml',

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
