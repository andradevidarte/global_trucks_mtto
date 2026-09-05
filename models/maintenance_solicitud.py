# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class MaintenanceSolicitud(models.Model):
    _name = 'maintenance.solicitud'
    _description = 'Solicitud de Mantenimiento'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, id desc'

    # Campos Básicos
    name = fields.Char(
        string='Consecutivo',
        required=True,
        copy=False,
        readonly=True,
        default='Nuevo',
        tracking=True
    )

    client_id = fields.Many2one(
        'res.partner',
        string='Cliente',
        required=True,
        tracking=True
    )

    vehicle_id = fields.Many2one(
        'maintenance.vehicle',
        string='Vehículo',
        required=True,
        tracking=True
    )

    description = fields.Text(
        string='Descripción del Problema',
        required=True,
        tracking=True
    )

    # Estados
    state = fields.Selection(
        [
            ('draft', 'Borrador'),
            ('pending_approval', 'Pendiente Aprobación'),
            ('approved', 'Aprobada'),
            ('assigned', 'Asignada'),
            ('converted', 'Convertida en Orden'),
            ('rejected', 'Rechazada'),
        ],
        string='Estado',
        default='draft',
        tracking=True
    )

    # Aprobación
    director_operaciones_id = fields.Many2one(
        'res.users',
        string='Director de Operaciones',
        tracking=True
    )

    rejection_reason = fields.Text(
        string='Motivo del Rechazo',
        tracking=True
    )

    # Asignación
    assigned_to_ids = fields.Many2many(
        'res.users',
        relation='maintenance_solicitud_assigned_user_rel',
        column1='solicitud_id',
        column2='user_id',
        string='Asignado a',
        tracking=True
    )

    # Relación con Orden
    order_id = fields.Many2one(
        'maintenance.order',
        string='Orden de Mantenimiento',
        ondelete='set null',
        tracking=True
    )

    diagnosis_id = fields.Many2one(
        'maintenance.diagnosis',
        string='Diagnóstico Creado',
        ondelete='set null',
        tracking=True
    )

    # Auditoría
    created_by_user = fields.Many2one(
        'res.users',
        string='Creado por',
        default=lambda self: self.env.user,
        readonly=True
    )

    create_date = fields.Datetime(string='Fecha de Creación', readonly=True)
    write_date = fields.Datetime(string='Última Modificación', readonly=True)

    @api.model
    def create(self, vals):
        if vals.get('name', 'Nuevo') == 'Nuevo':
            vals['name'] = self.env['ir.sequence'].next_by_code('maintenance.solicitud') or 'Nuevo'
        return super().create(vals)

    def action_submit(self):
        """Enviar solicitud para aprobación"""
        self.write({'state': 'pending_approval'})

    def action_approve(self):
        """Aprobar solicitud (Director de Operaciones)"""
        if not self.assigned_to_ids:
            raise UserError('Debe asignar al menos un usuario (Jefe de Ventas o Supervisor de Taller)')
        
        self.write({
            'state': 'assigned',
            'director_operaciones_id': self.env.user.id
        })

    def action_reject(self, reason):
        """Rechazar solicitud (Director de Operaciones)"""
        self.write({
            'state': 'rejected',
            'rejection_reason': reason,
            'director_operaciones_id': self.env.user.id
        })

    def action_assign_to_existing_order(self, order_id):
        """Asignar solicitud a una orden abierta"""
        if not order_id:
            raise UserError('Debe seleccionar una orden de mantenimiento')
        
        # Crear diagnóstico en la orden existente
        diagnosis = self.env['maintenance.diagnosis'].create({
            'order_id': order_id.id,
            'name': self.description,
            'created_from_solicitud': True,
        })
        
        self.write({
            'state': 'converted',
            'order_id': order_id.id,
            'diagnosis_id': diagnosis.id
        })

    def action_create_new_order(self):
        """Crear nueva orden desde la solicitud"""
        order = self.env['maintenance.order'].create({
            'customer_id': self.client_id.id,
            'vehicle_id': self.vehicle_id.id,
            'solicitud_id': self.id,
            'created_by_user': self.env.user.id,
        })
        
        # Crear diagnóstico inicial
        diagnosis = self.env['maintenance.diagnosis'].create({
            'order_id': order.id,
            'name': self.description,
            'created_from_solicitud': True,
        })
        
        self.write({
            'state': 'converted',
            'order_id': order.id,
            'diagnosis_id': diagnosis.id
        })
        
        return order

    def action_open_assign_wizard(self):
        """Abrir wizard para asignar a orden existente"""
        self.ensure_one()
        return {
            'name': 'Asignar a Orden',
            'type': 'ir.actions.act_window',
            'res_model': 'maintenance.solicitud.assign.order',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_solicitud_id': self.id}
        }

