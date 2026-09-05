{
    'name': 'Global Trucks MC SAS - Mantenimiento',
    'version': '4.0',
    'summary': 'Gestión de Órdenes de Mantenimiento con Vehículos y Reportes',
    'description': """
        Módulo para gestionar órdenes de mantenimiento de vehículos.
        - Registro de vehículos
        - Órdenes de mantenimiento
        - Solicitudes de mantenimiento de clientes
        - Diagnósticos de fallas
        - Seguimientos de trabajo
        - Imágenes adjuntas
        - Sistema de firmas
        - Reportes PDF profesionales
    """,
    'author': 'Global Trucks MC SAS',
    'category': 'Services/Maintenance',
    'depends': ['base', 'web', 'mail', 'stock'],
    'data': [
        'data/ir_model_data.xml',

        'security/security.xml',
        'security/maintenance_solicitud_rules.xml',
        'security/ir.model.access.csv',
        "wizard/maintenance_order_new_wizard_views.xml",
        'data/ir_sequence_data.xml',
        'reports/paperformat.xml',
        'reports/maintenance_order_report.xml',
        'reports/maintenance_order_report_template.xml',
        'reports/maintenance_order_report_ldn_template.xml',
        'views/vehicle_views.xml',
        'views/maintenance_order_views.xml',
        'views/maintenance_solicitud_views.xml',
        'wizard/maintenance_solicitud_assign_order_views.xml',
        'views/diagnosis_kanban_views.xml',
        'views/menu_views.xml',
    
    ],
    'external_dependencies': {
        'python': [],
    },
    'assets': {
        'web.assets_backend': [
            'global_trucks_maintenance/static/src/css/custom_kanban_styles.css',
            'global_trucks_maintenance/static/src/css/floating_save_button.css',
            'global_trucks_maintenance/static/src/css/signature_enhanced.css',
            'global_trucks_maintenance/static/src/css/image_gallery.css',
            'global_trucks_maintenance/static/src/css/maintenance_kanban.css',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
