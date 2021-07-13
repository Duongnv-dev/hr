# -*- coding: utf-8 -*-
{
    'name': "bnk_assets",

    'summary': """
        BnK assets management""",

    'description': """
        BnK assets management
    """,

    'author': "BnK Solution",
    'website': "https://bnksolution.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Assets',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail', 'hr', 'account_asset', 'account_accountant', 'l10n_vn', 'maintenance', 'toolz'],

    # always loaded
    'data': [
        'data/sequence_request_code.xml',
        'security/security_bnk_assets.xml',
        'security/ir.model.access.csv',
        'data/setting_menu.xml',
        'views/bnk_location.xml',
        'views/bnk_asset.xml',
        'views/bnk_asset_category.xml',
        'views/asset_request_line.xml',
        'views/asset_request.xml',
        'views/maintenance_request.xml',
        'views/export_barcode.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
