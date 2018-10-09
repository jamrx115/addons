# -*- coding: utf-8 -*-
{
    'name': "CIBERC - Employee performance custom module",

    'summary': """
        Modulo creado para las evaluaciones de desempeño""",

    'description': """
        Modulo creado para las evaluaciones de desempeño
    """,

    'author': "Alltic SAS",
    'website': "https://www.alltic.co",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'hr',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','hr','web_widget_timepicker'],

    # always loaded
    'data': [
        'security/ciberc_performance_security.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        #'data/data.xml',
    ]
}
