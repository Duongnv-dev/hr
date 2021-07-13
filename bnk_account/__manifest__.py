# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'BnK Account',
    'version': '1.0',
    'author': 'SKY Team',
    'category': 'SALES',
    'sequence': 8,
    'summary': 'Customize Account',
    'description': "ttf-wqy-microhei",
    'depends': [
        'account', 'base', 'mail', 'sale', 'report_xlsx'
    ],
    'data': [
        'views/report_invoice.xml',
        'data/mail_invoice_template_data.xml',
        'wizard/views/wizard_add_account_analytic.xml',
        'views/view_inherit_invoice_form.xml',
        'views/export_invoice_excel.xml',
    ],
    'external_dependencies': {
        'python': ['num2words'],
    },
    'demo': [
    ],
    'qweb': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
