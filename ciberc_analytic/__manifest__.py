# -*- coding: utf-8 -*-
{
    'name': "CIBERC - Partes de horas",

    'summary': """
        Personalizaciones al modelo de proyectos - partes de horas.""",

    'description': """
        Personalizaciones al modelo de proyectos - partes de horas
    """,

    'author': "Alltic SAS",
    'website': "https://www.alltic.co",

    # Categories can be used to filter modules in modules listing
    'category': 'Hidden/Dependency',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','hr','analytic', 'hr_timesheet', 'resource', 'hr_payroll'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
    ]
}