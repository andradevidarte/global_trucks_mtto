# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class MaintenanceSolicitudAssignOrder(models.TransientModel):
    _name = 'maintenance.solicitud.assign.order'
    _description = 'Asignar Solicitud a Orden'

    solicitud_id = fields.Many2one(
        'maintenance.solicitud',
        string='Solicitud',
        required=True,
        readonly=True
    )

    order_id = fields.Many2one(
        'maintenance.order',
        string='Orden de Mantenimiento',
        required=True,
        domain="[('state', 'in', ['approved', 'diagnosed', 'in_progress']), ('vehicle_id', '=', vehicle_id)]"
    )

    vehicle_id = fields.Many2one(
        'maintenance.vehicle',
        related='solicitud_id.vehicle_id',
        readonly=True
    )

    def action_assign(self):
        """Asignar la solicitud a la orden seleccionada"""
        self.solicitud_id.action_assign_to_existing_order(self.order_id)
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'maintenance.solicitud',
            'res_id': self.solicitud_id.id,
            'view_mode': 'form',
            'target': 'current'
        }
