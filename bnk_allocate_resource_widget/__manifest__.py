# -*- coding: utf-8 -*-
{
    'name': 'BnK allocate resource widget',
    'version': '1.0',
    'author': 'BnKsolution',
    'category': 'Project',
    'sequence': 8,
    'summary': 'BnK allocate resource widget',
    'description': "BnK allocate resource widget",
    'depends': [
        'bnk_project',
        'report_xlsx',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/allocate_resource.xml',
        'views/report_allocate_resource.xml',
        'views/report_allocate_resource_line_chart.xml',
        'views/report_delivery_allocate_resource.xml',
    ],
    'external_dependencies': {
    },
    'demo': [
    ],
    'qweb': [
        "static/src/xml/allocate_resource_widget.xml",
        "static/src/xml/allocate_resource_group_widget.xml",
        "static/src/xml/allocate_resource_line_chart_widget.xml",
        'static/src/xml/general_delivery_report_widget.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
