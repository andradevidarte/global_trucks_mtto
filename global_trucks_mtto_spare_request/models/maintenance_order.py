from odoo import fields, models


class MaintenanceOrder(models.Model):
    _inherit = 'maintenance.order'

    spare_request_ids = fields.One2many(
        'maintenance.spare.request',
        'order_id',
        string='Solicitudes de Repuestos'
    )
    spare_request_count = fields.Integer(
        string='Solicitudes de Repuestos',
        compute='_compute_spare_request_count'
    )

    def _compute_spare_request_count(self):
        for order in self:
            order.spare_request_count = len(order.spare_request_ids)

    def action_view_spare_requests(self):
        self.ensure_one()
        action = self.env.ref('global_trucks_mtto_spare_request.action_maintenance_spare_request').read()[0]
        action['domain'] = [('order_id', '=', self.id)]
        action['context'] = {
            'default_order_id': self.id,
            'default_requester_id': self.env.user.id,
        }
        if self.spare_request_count == 1:
            action['views'] = [(self.env.ref('global_trucks_mtto_spare_request.view_maintenance_spare_request_form').id, 'form')]
            action['res_id'] = self.spare_request_ids.id
        return action
