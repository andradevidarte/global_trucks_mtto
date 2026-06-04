from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError
from odoo.tools.float_utils import float_compare

NEW_REQUEST_NAME = 'Nuevo'


class MaintenanceSpareRequest(models.Model):
    _name = 'maintenance.spare.request'
    _description = 'Solicitud de Repuestos para Mantenimiento'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Consecutivo', default=NEW_REQUEST_NAME, readonly=True, copy=False, tracking=True)
    order_id = fields.Many2one(
        'maintenance.order',
        string='Orden de Mantenimiento',
        required=True,
        index=True,
        ondelete='cascade',
        tracking=True,
    )
    requester_id = fields.Many2one(
        'res.users',
        string='Técnico solicitante',
        default=lambda self: self.env.user,
        required=True,
        readonly=True,
        tracking=True,
    )
    storekeeper_id = fields.Many2one('res.users', string='Responsable de almacén', readonly=True, tracking=True)

    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Almacén',
        required=True,
        default=lambda self: self._default_warehouse(),
        tracking=True,
    )
    source_location_id = fields.Many2one(
        'stock.location',
        string='Ubicación de origen',
        required=True,
        domain="[('usage','=','internal')]",
        default=lambda self: self._default_source_location(),
    )
    destination_location_id = fields.Many2one(
        'stock.location',
        string='Ubicación de destino',
        required=True,
        domain="[('usage','=','internal')]",
        default=lambda self: self._default_destination_location(),
    )

    line_ids = fields.One2many('maintenance.spare.request.line', 'request_id', string='Líneas de repuestos', copy=True)

    request_date = fields.Datetime(string='Fecha de solicitud', readonly=True, tracking=True)
    approved_date = fields.Datetime(string='Fecha de aprobación', readonly=True, tracking=True)
    rejected_date = fields.Datetime(string='Fecha de rechazo', readonly=True, tracking=True)
    delivered_date = fields.Datetime(string='Fecha de entrega', readonly=True, tracking=True)

    approved_by_id = fields.Many2one('res.users', string='Aprobado por', readonly=True, tracking=True)
    rejected_by_id = fields.Many2one('res.users', string='Rechazado por', readonly=True, tracking=True)
    delivered_by_id = fields.Many2one('res.users', string='Entregado por', readonly=True, tracking=True)

    rejection_reason = fields.Text(string='Motivo de rechazo', tracking=True)
    notes = fields.Text(string='Notas', tracking=True)

    state = fields.Selection(
        [
            ('draft', 'Borrador'),
            ('requested', 'Solicitado'),
            ('approved', 'Aprobado'),
            ('rejected', 'Rechazado'),
            ('partially_delivered', 'Entregado parcial'),
            ('delivered', 'Entregado total'),
            ('cancelled', 'Cancelado'),
        ],
        string='Estado',
        default='draft',
        tracking=True,
    )

    line_count = fields.Integer(string='Líneas', compute='_compute_line_count')

    @api.depends('line_ids')
    def _compute_line_count(self):
        for rec in self:
            rec.line_count = len(rec.line_ids)

    def _default_warehouse(self):
        return self.env['stock.warehouse'].search([('company_id', '=', self.env.company.id)], limit=1)

    def _default_source_location(self):
        warehouse = self._default_warehouse()
        return warehouse.lot_stock_id if warehouse else False

    def _default_destination_location(self):
        warehouse = self._default_warehouse()
        return (warehouse.wh_output_stock_loc_id or warehouse.lot_stock_id) if warehouse else False

    @api.onchange('warehouse_id')
    def _onchange_warehouse_id(self):
        if self.warehouse_id:
            self.source_location_id = self.warehouse_id.lot_stock_id
            self.destination_location_id = self.warehouse_id.wh_output_stock_loc_id or self.warehouse_id.lot_stock_id

    def _ensure_can_submit(self):
        allowed = (
            self.env.user.has_group('global_trucks_mtto_spare_request.group_spare_technician')
            or self.env.user.has_group('global_trucks_mtto.group_mtto_admin')
            or self.env.user.has_group('global_trucks_mtto.group_mtto_supervisor')
        )
        if not allowed:
            raise AccessError(_('No tienes permisos para solicitar repuestos.'))

    def _ensure_can_manage_warehouse(self):
        allowed = (
            self.env.user.has_group('global_trucks_mtto_spare_request.group_spare_storekeeper')
            or self.env.user.has_group('global_trucks_mtto.group_mtto_admin')
            or self.env.user.has_group('global_trucks_mtto.group_mtto_supervisor')
        )
        if not allowed:
            raise AccessError(_('No tienes permisos de almacén para aprobar o entregar repuestos.'))

    def _notify_users(self, partner_ids, body):
        if not partner_ids:
            return
        self.message_post(
            body=body,
            partner_ids=partner_ids,
            subtype_xmlid='mail.mt_note',
        )

    def _warehouse_partner_ids(self):
        group = self.env.ref('global_trucks_mtto_spare_request.group_spare_storekeeper', raise_if_not_found=False)
        if not group:
            return []
        return group.users.mapped('partner_id').ids

    def _sync_state_from_lines(self):
        for rec in self:
            if not rec.line_ids:
                rec.state = 'draft'
                continue

            line_states = set(rec.line_ids.mapped('state'))
            if rec.state == 'cancelled':
                continue
            if line_states == {'rejected'}:
                rec.state = 'rejected'
                continue
            if all(state == 'delivered' for state in line_states):
                rec.state = 'delivered'
                continue
            if any(state in ('partially_delivered', 'delivered') for state in line_states):
                rec.state = 'partially_delivered'
                continue
            if any(state == 'approved' for state in line_states):
                rec.state = 'approved'
                continue
            if any(state == 'requested' for state in line_states):
                rec.state = 'requested'
                continue
            rec.state = 'draft'

    def action_submit(self):
        self._ensure_can_submit()
        for rec in self:
            if not rec.line_ids:
                raise UserError(_('Debe agregar al menos una línea de repuesto antes de solicitar.'))
            for line in rec.line_ids:
                if line.qty_requested <= 0:
                    raise UserError(_('La cantidad solicitada debe ser mayor a cero para todos los repuestos.'))
                line.write({'state': 'requested'})

            rec.write({
                'state': 'requested',
                'request_date': fields.Datetime.now(),
                'rejection_reason': False,
            })

            rec.message_post(body=_('Solicitud enviada a almacén para aprobación.'), subtype_xmlid='mail.mt_note')
            rec.order_id.message_post(
                body=_('Se solicitó reposición de repuestos: %s') % rec.name,
                subtype_xmlid='mail.mt_note',
            )
            rec._notify_users(
                rec._warehouse_partner_ids(),
                _('Nueva solicitud de repuestos %s pendiente de aprobación.') % rec.name,
            )

    def action_approve(self):
        self._ensure_can_manage_warehouse()
        for rec in self:
            if rec.state not in ('requested', 'approved', 'partially_delivered'):
                raise UserError(_('Solo se pueden aprobar solicitudes en estado solicitado/aprobado/parcial.'))

            for line in rec.line_ids:
                qty_approved = line.qty_approved if line.qty_approved > 0 else line.qty_requested
                if qty_approved < 0 or qty_approved > line.qty_requested:
                    raise UserError(_('La cantidad aprobada debe estar entre 0 y la solicitada.'))
                if qty_approved == 0:
                    line.write({'state': 'rejected', 'qty_approved': 0.0})
                    continue
                line._check_available_qty(qty_approved, rec.source_location_id)
                line.write({'qty_approved': qty_approved, 'state': 'approved'})

            rec.write({
                'approved_date': fields.Datetime.now(),
                'approved_by_id': self.env.user.id,
                'storekeeper_id': self.env.user.id,
                'rejected_date': False,
                'rejected_by_id': False,
                'rejection_reason': False,
            })
            rec._sync_state_from_lines()

            rec.message_post(body=_('Solicitud aprobada por almacén.'), subtype_xmlid='mail.mt_note')
            rec.order_id.message_post(
                body=_('Almacén aprobó la solicitud de repuestos: %s') % rec.name,
                subtype_xmlid='mail.mt_note',
            )
            rec._notify_users(
                [rec.requester_id.partner_id.id],
                _('Tu solicitud de repuestos %s fue aprobada.') % rec.name,
            )

    def action_reject(self):
        self._ensure_can_manage_warehouse()
        for rec in self:
            if rec.state not in ('requested', 'approved', 'partially_delivered'):
                raise UserError(_('Solo se pueden rechazar solicitudes en estado solicitado/aprobado/parcial.'))
            if not rec.rejection_reason:
                raise UserError(_('Debe indicar el motivo del rechazo.'))

            rec.line_ids.write({'state': 'rejected', 'qty_approved': 0.0})
            rec.write({
                'state': 'rejected',
                'rejected_date': fields.Datetime.now(),
                'rejected_by_id': self.env.user.id,
                'storekeeper_id': self.env.user.id,
            })

            rec.message_post(body=_('Solicitud rechazada por almacén.'), subtype_xmlid='mail.mt_note')
            rec.order_id.message_post(
                body=_('Almacén rechazó la solicitud de repuestos: %s') % rec.name,
                subtype_xmlid='mail.mt_note',
            )
            rec._notify_users(
                [rec.requester_id.partner_id.id],
                _('Tu solicitud %s fue rechazada. Motivo: %s') % (rec.name, rec.rejection_reason),
            )

    def action_deliver(self):
        self._ensure_can_manage_warehouse()
        Move = self.env['stock.move']
        Picking = self.env['stock.picking']

        for rec in self:
            lines_to_deliver = rec.line_ids.filtered(
                lambda line: line.state in ('approved', 'partially_delivered') and line.qty_approved > line.qty_delivered
            )
            if not lines_to_deliver:
                raise UserError(_('No hay líneas aprobadas pendientes por entregar.'))
            if not rec.warehouse_id.int_type_id:
                raise UserError(_('El almacén no tiene tipo de operación interna configurado.'))

            picking = Picking.create({
                'picking_type_id': rec.warehouse_id.int_type_id.id,
                'location_id': rec.source_location_id.id,
                'location_dest_id': rec.destination_location_id.id,
                'origin': rec.name,
            })

            move_pending_qty = []
            for line in lines_to_deliver:
                pending_qty = line.qty_approved - line.qty_delivered
                line._check_available_qty(pending_qty, rec.source_location_id)
                move = Move.create({
                    'name': line.product_id.display_name,
                    'picking_id': picking.id,
                    'product_id': line.product_id.id,
                    'product_uom_qty': pending_qty,
                    'product_uom': line.uom_id.id,
                    'location_id': rec.source_location_id.id,
                    'location_dest_id': rec.destination_location_id.id,
                })
                move_pending_qty.append((move, pending_qty))

                new_delivered = line.qty_delivered + pending_qty
                line.write({
                    'qty_delivered': new_delivered,
                    'state': 'delivered' if new_delivered >= line.qty_approved else 'partially_delivered',
                })

            picking.action_confirm()
            picking.action_assign()
            for move, pending_qty in move_pending_qty:
                if hasattr(move, '_set_quantity_done'):
                    move._set_quantity_done(pending_qty)
                else:
                    move.quantity_done = pending_qty
            picking.button_validate()

            rec.write({
                'delivered_date': fields.Datetime.now(),
                'delivered_by_id': self.env.user.id,
                'storekeeper_id': self.env.user.id,
            })
            rec._sync_state_from_lines()

            rec.message_post(body=_('Entrega de repuestos registrada desde almacén.'), subtype_xmlid='mail.mt_note')
            rec.order_id.message_post(
                body=_('Se registró entrega de repuestos para la solicitud: %s') % rec.name,
                subtype_xmlid='mail.mt_note',
            )
            rec._notify_users(
                [rec.requester_id.partner_id.id],
                _('Tu solicitud %s recibió entrega de repuestos.') % rec.name,
            )

    def action_cancel(self):
        for rec in self:
            if rec.state == 'delivered':
                raise UserError(_('No se puede cancelar una solicitud totalmente entregada.'))
            rec.write({'state': 'cancelled'})
            rec.message_post(body=_('Solicitud cancelada.'), subtype_xmlid='mail.mt_note')

    def action_set_draft(self):
        for rec in self:
            if rec.state not in ('draft', 'requested', 'rejected', 'cancelled'):
                raise UserError(_('Solo se puede regresar a borrador desde solicitado/rechazado/cancelado.'))
            rec.line_ids.write({'state': 'draft'})
            rec.write({'state': 'draft'})

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', NEW_REQUEST_NAME) == NEW_REQUEST_NAME:
                vals['name'] = self.env['ir.sequence'].next_by_code('maintenance.spare.request') or NEW_REQUEST_NAME
        records = super().create(vals_list)
        for rec in records:
            rec.order_id.message_post(
                body=_('Se creó la solicitud de repuestos: %s') % rec.name,
                subtype_xmlid='mail.mt_note',
            )
        return records


class MaintenanceSpareRequestLine(models.Model):
    _name = 'maintenance.spare.request.line'
    _description = 'Línea de Solicitud de Repuesto'
    _order = 'id asc'

    request_id = fields.Many2one(
        'maintenance.spare.request',
        string='Solicitud',
        required=True,
        ondelete='cascade',
        index=True,
    )
    order_id = fields.Many2one(related='request_id.order_id', store=True, readonly=True)
    product_id = fields.Many2one(
        'product.product',
        string='Repuesto',
        required=True,
        domain="[('detailed_type', '!=', 'service')]",
    )
    uom_id = fields.Many2one(related='product_id.uom_id', string='Unidad de medida', store=True, readonly=True)

    qty_requested = fields.Float(string='Cant. solicitada', required=True, default=1.0, tracking=True)
    qty_approved = fields.Float(string='Cant. aprobada', default=0.0, tracking=True)
    qty_delivered = fields.Float(string='Cant. entregada', default=0.0, tracking=True)
    qty_available = fields.Float(string='Disponible en almacén', compute='_compute_qty_available')

    notes = fields.Char(string='Notas')
    state = fields.Selection(
        [
            ('draft', 'Borrador'),
            ('requested', 'Solicitado'),
            ('approved', 'Aprobado'),
            ('rejected', 'Rechazado'),
            ('partially_delivered', 'Entregado parcial'),
            ('delivered', 'Entregado total'),
        ],
        string='Estado',
        default='draft',
        tracking=True,
    )

    @api.depends('product_id', 'request_id.source_location_id')
    def _compute_qty_available(self):
        quant_model = self.env['stock.quant']
        for line in self:
            if not line.product_id or not line.request_id.source_location_id:
                line.qty_available = 0.0
                continue
            line.qty_available = quant_model._get_available_quantity(
                line.product_id,
                line.request_id.source_location_id,
                strict=True,
            )

    @api.constrains('qty_requested', 'qty_approved', 'qty_delivered')
    def _check_quantities(self):
        for line in self:
            if line.qty_requested < 0 or line.qty_approved < 0 or line.qty_delivered < 0:
                raise UserError(_('Las cantidades no pueden ser negativas.'))
            if line.qty_approved > line.qty_requested:
                raise UserError(_('La cantidad aprobada no puede superar la solicitada.'))
            if line.qty_delivered > line.qty_approved:
                raise UserError(_('La cantidad entregada no puede superar la aprobada.'))

    def _check_available_qty(self, qty, location):
        self.ensure_one()
        if qty <= 0:
            return
        available = self.env['stock.quant']._get_available_quantity(self.product_id, location, strict=True)
        precision_rounding = self.uom_id.rounding or self.product_id.uom_id.rounding
        if float_compare(available, qty, precision_rounding=precision_rounding) < 0:
            raise UserError(
                _(
                    'No hay stock suficiente para %s. Solicitado/aprobado: %.2f, disponible: %.2f.'
                )
                % (self.product_id.display_name, qty, available)
            )
