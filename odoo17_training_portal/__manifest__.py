# -*- coding: utf-8 -*-
{
    'name': 'Student Training Registration Portal',
    'version': '17.0.1.0.0',
    'category': 'Website',
    'summary': 'Public-facing portal for student training registration with dynamic AJAX-driven form',
    'description': """
Student Training Registration Portal
=====================================
A fully dynamic public-facing portal built on Odoo 17 that allows university students
to register for industrial training programs.

Features:
---------
- Student lookup by university ID with auto-fill
- Dynamic company → program → week selection via AJAX
- Live seat capacity tracking per training week
- Automatic op.student record creation on registration
- Year-level based program filtering
- Week card UI with real-time availability
- Backend confirmation workflow
    """,
    'author': 'Ahmed Farouk',
    'depends': [
        'base',
        'mail',
        'website',
        'openeducat_core',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/training_portal_registration_views.xml',
        'website/training_registration_template.xml',
    ],
    'assets': {
        'web.assets_frontend': [],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
