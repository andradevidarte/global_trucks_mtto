from odoo import models, fields
from odoo.exceptions import UserError


class MaintenanceOrderNewWizard(models.TransientModel):
    _name = "maintenance.order.new.wizard"
    _description = "Nueva Orden: Seleccionar Vehículo"

    vehicle_id = fields.Many2one("maintenance.vehicle", string="Vehículo", required=True)
    customer_id = fields.Many2one("res.partner", string="Cliente", readonly=True)

    def onchange_vehicle_id(self):
        for rec in self:
            rec.customer_id = rec.vehicle_id.owner_id if rec.vehicle_id else False

    def action_continue(self):
        self.ensure_one()
        if not self.vehicle_id:
            raise UserError("Debes seleccionar un vehículo.")

        existing = self.env["maintenance.order"].search([
            ("vehicle_id", "=", self.vehicle_id.id),
            ("is_invoiced", "=", False),
        ], order="id desc", limit=1)

        # Si existe una orden no facturada -> confirmar
        if existing:
            wiz = self.env["maintenance.order.confirm.duplicate"].create({
                "vehicle_id": self.vehicle_id.id,
                "existing_order_id": existing.id,
                "message": (
                    f"El vehículo ya tiene una orden sin facturar:\n"
                    f"- Orden: {existing.name}\n\n"
                    f"¿Deseas crear una nueva orden de todas formas?"
                ),
            })
            return {
                "type": "ir.actions.act_window",
                "name": "Confirmación",
                "res_model": "maintenance.order.confirm.duplicate",
                "view_mode": "form",
                "target": "new",
                "res_id": wiz.id,
            }

        # Si no existe -> abrir directamente el formulario real
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
