# -*- coding: utf-8 -*-
{
    'name': "CIBERC - Holidays custom module",

    'summary': """
        Personalizaciones al modelo de ausencias""",

    'description': """
        Personalizaciones al modelo de ausencias
    """,

    'author': "Alltic SAS",
    'website': "https://www.alltic.co",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'hr',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','hr','hr_holidays', 'hr_payroll', 'mail'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/mail_templates.xml',
        'views/report_mintrab.xml',
        'views/report_salary_book.xml',
        'views/report_holiday_template.xml',
        'views/report_menu.xml',
        'views/hr_payroll_views.xml',
    ]
}