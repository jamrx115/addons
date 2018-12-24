# -*- coding: utf-8 -*-
{
    'name': "CIBERC - Payroll custom module",

    'summary': """
        Personalizaciones al módulo de nómina""",

    'description': """
        Personalizaciones al módulo de nómina
    """,

    'author': "Alltic SAS",
    'website': "https://www.alltic.co",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'hr',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','hr','hr_payroll', 'mail'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/report_mintrab.xml',
        'views/report_salary_book.xml',
        'views/report_menu.xml',
    ]
}