{
    'name': 'Global Trucks MC SAS - Mantenimiento',
    'version': '4.0',
    'summary': 'Gestión de Órdenes de Mantenimiento con Vehículos y Reportes',
    'description': """
        Módulo para gestionar órdenes de mantenimiento de vehículos.
        - Registro de vehículos
        - Órdenes de mantenimiento
        - Diagnósticos de fallas
        - Seguimientos de trabajo
        - Imágenes adjuntas
        - Sistema de firmas
        - Reportes PDF profesionales
    """,
    'author': 'Global Trucks MC SAS',
    'category': 'Services/Maintenance',
    'depends': ['base', 'web', 'mail'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
	"wizard/maintenance_order_new_wizard_views.xml",
        'data/ir_sequence_data.xml',
        'reports/paperformat.xml',
        'reports/maintenance_order_report.xml',
        'reports/maintenance_order_report_template.xml',
        'views/vehicle_views.xml',
        'views/maintenance_order_views.xml',
        'reports/maintenance_order_report_ldn_template.xml',
        'views/diagnosis_kanban_views.xml',
        'views/menu_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'global_trucks_mtto/static/src/css/custom_kanban_styles.css',
            'global_trucks_mtto/static/src/css/floating_save_button.css',
            'global_trucks_mtto/static/src/css/signature_enhanced.css',
            'global_trucks_mtto/static/src/css/image_gallery.css',
            'global_trucks_mtto/static/src/css/maintenance_kanban.css',
            'global_trucks_mtto/static/src/js/floating_save_button.js',
            'global_trucks_mtto/static/src/js/signature_canvas_fix.js',
            'global_trucks_mtto/static/src/js/image_compressor.js',
            'global_trucks_mtto/static/src/js/parts_autosave_buttons.js',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
