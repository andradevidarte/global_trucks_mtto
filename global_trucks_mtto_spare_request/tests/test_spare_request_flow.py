from odoo.tests.common import SavepointCase


class TestSpareRequestFlow(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Cliente Prueba'})
        cls.vehicle = cls.env['maintenance.vehicle'].create({
            'category': 'vehicular',
            'vehicle_type': 'Camión',
            'serie_plate': 'TEST-001',
            'owner_id': cls.partner.id,
        })
        cls.order = cls.env['maintenance.order'].create({
            'customer_id': cls.partner.id,
            'vehicle_id': cls.vehicle.id,
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Filtro de aceite prueba',
            'detailed_type': 'product',
        })

        cls.warehouse = cls.env['stock.warehouse'].search([('company_id', '=', cls.env.company.id)], limit=1)
        cls.location = cls.warehouse.lot_stock_id
        cls.env['stock.quant']._update_available_quantity(cls.product, cls.location, 10.0)

    def test_request_approve_deliver(self):
        request = self.env['maintenance.spare.request'].create({
            'order_id': self.order.id,
            'warehouse_id': self.warehouse.id,
            'source_location_id': self.location.id,
            'destination_location_id': (self.warehouse.wh_output_stock_loc_id or self.location).id,
            'line_ids': [
                (0, 0, {
                    'product_id': self.product.id,
                    'qty_requested': 4.0,
                })
            ],
        })

        request.action_submit()
        self.assertEqual(request.state, 'requested')
        self.assertEqual(request.line_ids[0].state, 'requested')

        request.action_approve()
        self.assertEqual(request.state, 'approved')
        self.assertEqual(request.line_ids[0].qty_approved, 4.0)

        request.action_deliver()
        self.assertEqual(request.state, 'delivered')
        self.assertEqual(request.line_ids[0].qty_delivered, 4.0)

        picking = self.env['stock.picking'].search([('origin', '=', request.name)], limit=1)
        self.assertTrue(picking, 'Debe crearse un movimiento de inventario para la entrega.')
        self.assertEqual(picking.state, 'done')

        available_qty = self.env['stock.quant']._get_available_quantity(self.product, self.location, strict=True)
        self.assertEqual(available_qty, 6.0)
