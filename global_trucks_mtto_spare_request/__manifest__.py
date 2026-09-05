{
    'name': 'Global Trucks MC SAS - Solicitud de Repuestos',
    'version': '1.0',
    'summary': 'Solicitudes de repuestos para órdenes de mantenimiento en ejecución',
    'description': """
        Módulo adicional para gestionar solicitudes de repuestos entre
        técnicos de mantenimiento y almacén.
    """,
    'author': 'Global Trucks MC SAS',
    'category': 'Services/Maintenance',
    'depends': ['mail', 'stock', 'global_trucks_maintenance'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/spare_request_views.xml',
        'views/maintenance_order_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
