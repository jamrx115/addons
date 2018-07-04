# -*- coding: utf-8 -*-
{
    'name': "AT Evaluation module",

    'summary': """
        Modulo que permite realizar evaluaciones de entrenamiento
        """,

    'description': """
        Modulo que permite realizar evaluaciones sobre algún tema
        en especifico, agregando el contenido y luego asignando su respectiva evaluación
    """,

    'author': "Alltic",
    'website': "https://www.alltic.co",
    'support' : "support@alltic.co",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'hr',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','website','hr'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/at_evaluation.xml',
        'views/at_evaluation_result.xml',
        'views/at_evaluation_templates.xml'
    ]
}