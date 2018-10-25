# -*- coding: utf-8 -*-

{
    'name': 'Views to pdf',
    'version': '10.0.1.0',
    'author': 'Abderrahmen Khalledi',
    'category': 'web',
    'summary': 'Views to PDF',
    'description': """
Generate PDF from Views
=========================

This module will allow you to generate a pdf report from any views (FORM, TREE, KANBAN, PIVOT, GRAPH, Galendar).

    """,
    'author': 'abderrahmen.khalledi@gmail.com',
    'license': 'AGPL-3',
    'depends': ['base', 'web'],
    'data': [
        'views/assets.xml',
    ],
    'qweb': ['static/src/xml/view.xml'],
    'auto_install': False,
    'installable': True,
    'application': False,

}
