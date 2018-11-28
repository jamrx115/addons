# -*- coding: utf-8 -*-
{
    'name': "CIBERC - General custom module",

    'summary': """
        Campos adicionales a varios modelos (bi_view_editor, task projects and timesheet)""",

    'description': """
        Campos adicionales a varios modelos (bi_view_editor, task projects and timesheet)
    """,

    'author': "Alltic SAS",
    'website': "https://www.alltic.co",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'hr',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','bi_view_editor', 'mail', 'hr', 'project','hr_timesheet', 'analytic', 'ohrms_loan'],

    # always loaded
    'data': [
        'views/views.xml',
        'security/ciberc_security.xml',
    ]
}
