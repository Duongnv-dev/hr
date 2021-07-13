# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'BnK Project',
    'version': '1.0',
    'author': 'BnKsolution',
    'category': 'Project',
    'sequence': 8,
    'summary': 'Customize project',
    'description': "BnK project",
    'depends': [
        'project',
        'bnk_hr'
    ],
    'data': [
        'data/project_data.xml',
        'security/groups.xml',
        'security/rules.xml',
        'security/ir.model.access.csv',
        'wizard/views/wizard_quick_allocate_view.xml',
        'views/project_view.xml',
        'wizard/views/wizard_lock_allocate_resource.xml',
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
