# -*- coding: utf-8 -*-
{
    'name': "CIBERC - Employee custom module",

    'summary': """
        Campos adicionales al modelo de empleados""",

    'description': """
        Campos adicionales al modelo de empleados
    """,

    'author': "Alltic SAS",
    'website': "https://www.alltic.co",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'hr',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','hr','hr_employee_updation', 'ciberc'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'data/data.xml',
    ]
}