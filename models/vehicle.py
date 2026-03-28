from odoo import models, fields, api

class Vehicle(models.Model):
    _name = 'maintenance.vehicle'
    _description = 'Vehículos'
    _rec_name = 'display_name'

    name = fields.Char(string='Nombre Interno', compute='_compute_display_name', store=True)
    display_name = fields.Char(string='Vehículo', compute='_compute_display_name', store=True)

    # NUEVO: Categoría del vehículo
    category = fields.Selection(
        selection=[
            ('vehicular', 'Vehicular'),
            ('machinery', 'Maquinaria'),
        ],
        string='Categoría',
        required=True,
        default='vehicular',
        index=True
    )

    vehicle_type = fields.Char(string='Tipo de Vehículo', required=True)
    serie_plate = fields.Char(string='Serie/Placa', required=True)
    model = fields.Char(string='Modelo')
    year = fields.Char(string='Año')
    color = fields.Char(string='Color')
    owner_id = fields.Many2one('res.partner', string='Propietario', required=True)

    maintenance_order_ids = fields.One2many('maintenance.order', 'vehicle_id', string='Órdenes de Mantenimiento')
    maintenance_count = fields.Integer(string='Cantidad de Mantenimientos', compute='_compute_maintenance_count')

    @api.depends('vehicle_type', 'serie_plate')
    def _compute_display_name(self):
        """Genera el nombre de visualización del vehículo."""
        for vehicle in self:
            if vehicle.vehicle_type and vehicle.serie_plate:
                vehicle.display_name = f"{vehicle.vehicle_type} - {vehicle.serie_plate}"
                vehicle.name = vehicle.display_name
            else:
                vehicle.display_name = 'Nuevo Vehículo'
                vehicle.name = 'Nuevo Vehículo'

    @api.depends('maintenance_order_ids')
    def _compute_maintenance_count(self):
        """Cuenta las órdenes de mantenimiento asociadas."""
        for vehicle in self:
            vehicle.maintenance_count = len(vehicle.maintenance_order_ids)

    _sql_constraints = [
        ('serie_plate_unique', 'unique(serie_plate)', 'La Serie/Placa debe ser única!')
    ]
