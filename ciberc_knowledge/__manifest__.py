# -*- coding: utf-8 -*-
{
    'name': "CIBERC - knowledge custom module",

    'summary': """
        Modulo creado para el flujo de aprobación de capacitaciones""",

    'description': """
        Modulo creado para el flujo de aprobación de capacitaciones
    """,

    'author': "Alltic SAS",
    'website': "https://www.alltic.co",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'hr',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','hr','ciberc_performance','mail'],

    # always loaded
    'data': [
        'data/report_paperformat_knowledge.xml',
        'security/ciberc_knowledge_security.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/report_knowledge_templates.xml',
        'views/ciberc_knowledge_report.xml',
        'data/knowledge_template_mail.xml',
        'data/reasons_data.xml',
        #'data/data.xml',
    ]
}
