from odoo import models, fields


class MaintenanceOrderConfirmDuplicate(models.TransientModel):
    _name = "maintenance.order.confirm.duplicate"
    _description = "Confirmación: Orden no facturada existente"

    vehicle_id = fields.Many2one("maintenance.vehicle", string="Vehículo", required=True, readonly=True)
    existing_order_id = fields.Many2one("maintenance.order", string="Orden existente", readonly=True)
    message = fields.Text(string="Mensaje", readonly=True)

    def action_continue(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Nueva Orden de Mantenimiento",
            "res_model": "maintenance.order",
            "view_mode": "form",
            "target": "current",
            "context": {
                "default_vehicle_id": self.vehicle_id.id,
                "default_customer_id": self.vehicle_id.owner_id.id if self.vehicle_id.owner_id else False,
            },
        }
