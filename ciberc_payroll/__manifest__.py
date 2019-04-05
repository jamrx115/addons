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
    'depends': ['base','hr','hr_payroll', 'mail', 'multi_payslip'],

    # always loaded
    'data': [
        'security/ciberc_payroll_security.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/qweb.xml',
        'views/report_salary_book.xml',
        'views/report_salary_book_current.xml',
        'views/report_payed_paysliprun.xml',
        'views/report_menu.xml',
    ]
}