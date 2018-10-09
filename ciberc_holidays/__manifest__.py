# -*- coding: utf-8 -*-
{
    'name': "CIBERC - Holidays custom module",

    'summary': """
        Campos adicionales al modelo de ausencias""",

    'description': """
        Campos adicionales al modelo de ausencias
    """,

    'author': "Alltic SAS",
    'website': "https://www.alltic.co",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'hr',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','hr','hr_holidays', 'hr_payroll', 'hr_contract'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
    ]
}