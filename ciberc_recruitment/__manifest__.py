# -*- coding: utf-8 -*-
{
    'name': "CIBERC - Recruitment custom module",

    'summary': """
        Campos adicionales al modelo de candidatos""",

    'description': """
        Campos adicionales al modelo de candidatos
    """,

    'author': "Alltic SAS",
    'website': "https://www.alltic.co",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'hr',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','hr', 'hr_recruitment'],

    # always loaded
    'data': [
        'security/hr_recruitment_security.xml',
        'views/views.xml',
        'views/qweb_templates.xml',
    ]
}