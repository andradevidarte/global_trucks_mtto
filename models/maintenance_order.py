# -*- coding: utf-8 -*-

import base64
import io
import math
import re
import zipfile

from odoo import models, fields, api
from odoo.exceptions import UserError, AccessError


class MaintenanceOrder(models.Model):
    _name = 'maintenance.order'
    _description = 'Órdenes de Mantenimiento'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_request desc, id desc'

    name = fields.Char(
        string='Consecutivo',
        required=True,
        copy=False,
        readonly=True,
        default='Nuevo',
        tracking=True
    )

    date_request = fields.Date(
        string='Fecha de Solicitud',
        required=True,
        default=fields.Date.context_today,
        tracking=True
    )

    date_start = fields.Datetime(string='Fecha de Inicio', tracking=True)
    date_end = fields.Datetime(string='Fecha de Finalización', tracking=True)

    customer_id = fields.Many2one('res.partner', string='Cliente', required=True, tracking=True)
    vehicle_id = fields.Many2one(
        'maintenance.vehicle',
        string='Vehículo',
        required=True,
        ondelete='restrict',
        tracking=True
    )

    is_invoiced = fields.Boolean(
        string="Facturada",
        default=False,
        tracking=True,
        help="Marcar si esta orden ya fue facturada."
    )

    # Badge para la vista lista: "Facturada" / "No facturada"
    invoice_state_badge = fields.Selection(
        selection=[("not_invoiced", "No facturada"), ("invoiced", "Facturada")],
        string="Facturada",
        compute="_compute_invoice_state_badge",
        store=False,
    )

    @api.depends("is_invoiced")
    def _compute_invoice_state_badge(self):
        for rec in self:
            rec.invoice_state_badge = "invoiced" if rec.is_invoiced else "not_invoiced"

    customer_short = fields.Char(string="Cliente", compute="_compute_customer_short", store=False)

    @api.depends("customer_id.display_name", "customer_id.name")
    def _compute_customer_short(self):
        for rec in self:
            name = rec.customer_id.display_name or rec.customer_id.name or ""
            rec.customer_short = (name[:20] + "…") if len(name) > 20 else name

    operator_name = fields.Char(
        string='Operador/Conductor',
        tracking=True,
        help='Nombre del operador en mayúsculas'
    )

    vehicle_type = fields.Char(string='Tipo de Vehículo', related='vehicle_id.vehicle_type', store=True, readonly=True)
    serie_plate = fields.Char(string='Serie/Placa', related='vehicle_id.serie_plate', store=True, readonly=True)

    km_hours = fields.Char(
        string='KM / Horas',
        tracking=True,
        help='Ingrese el kilometraje u horas del equipo. Ej: "125000 KM" o "320 H".'
    )

    vehicle_model = fields.Char(string='Modelo', related='vehicle_id.model', readonly=True)
    vehicle_year = fields.Char(string='Año', related='vehicle_id.year', readonly=True)
    vehicle_color = fields.Char(string='Color', related='vehicle_id.color', readonly=True)

    vehicle_owner_id = fields.Many2one('res.partner', string='Propietario', related='vehicle_id.owner_id', readonly=True)

    total_cost = fields.Float(string='Costo Total', tracking=True)
    observations = fields.Text(string='Observaciones', tracking=True)

    diagnosis_ids = fields.One2many('maintenance.diagnosis', 'order_id', string='Diagnósticos de Fallas')

    parts_line_ids = fields.One2many('maintenance.order.part.line', 'order_id', string='Repuestos')

    parts_image_ids = fields.Many2many(
        'ir.attachment',
        string='Imágenes de Repuestos',
        domain=[('mimetype', 'ilike', 'image')]
    )

    is_completed = fields.Boolean(
        string='Completado',
        compute='_compute_is_completed',
        store=True,
        readonly=True,
        help='Se marca automáticamente cuando todos los diagnósticos están completos'
    )

    maintenance_responsible_id = fields.Many2one(
        'res.users',
        string='Encargado del Mantenimiento',
        default=lambda self: self.env.user,
        tracking=True
    )

    maintenance_responsible_job = fields.Char(
        string='Cargo del Encargado',
        related='maintenance_responsible_id.partner_id.function',
        readonly=True
    )

    maintenance_signature = fields.Binary(string='Firma del Encargado', attachment=True)
    maintenance_signature_date = fields.Datetime(string='Fecha de Firma del Encargado', readonly=True)

    customer_representative_name = fields.Char(
        string='Representante del Cliente',
        compute='_compute_customer_representative_name',
        inverse='_inverse_customer_representative_name',
        store=True,
        tracking=True,
        help='Se sincroniza automáticamente con el operador. Convertido a MAYÚSCULAS.'
    )

    customer_representative_job = fields.Char(string='Cargo del Representante', default='Operador', tracking=True)

    customer_signature = fields.Binary(string='Firma del Representante', attachment=True)
    customer_signature_date = fields.Datetime(string='Fecha de Firma del Representante', readonly=True)

    @api.depends('diagnosis_ids.is_completed')
    def _compute_is_completed(self):
        for order in self:
            if order.diagnosis_ids:
                order.is_completed = all(d.is_completed for d in order.diagnosis_ids)
            else:
                order.is_completed = False

    @api.depends('operator_name')
    def _compute_customer_representative_name(self):
        for order in self:
            order.customer_representative_name = order.operator_name.upper() if order.operator_name else False

    def _inverse_customer_representative_name(self):
        for order in self:
            if order.customer_representative_name:
                order.customer_representative_name = order.customer_representative_name.upper()

    @api.onchange('operator_name')
    def _onchange_operator_name(self):
        if self.operator_name:
            self.operator_name = self.operator_name.upper()
            self.customer_representative_name = self.operator_name

    @api.onchange('maintenance_signature')
    def _onchange_maintenance_signature(self):
        if self.maintenance_signature and not self.maintenance_signature_date:
            self.maintenance_signature_date = fields.Datetime.now()

    @api.onchange('customer_signature')
    def _onchange_customer_signature(self):
        if self.customer_signature and not self.customer_signature_date:
            self.customer_signature_date = fields.Datetime.now()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code('maintenance.order') or 'Nuevo'

            if vals.get('operator_name'):
                vals['operator_name'] = vals['operator_name'].upper()

            if vals.get('customer_representative_name'):
                vals['customer_representative_name'] = vals['customer_representative_name'].upper()

        return super().create(vals_list)

    def write(self, vals):
        if vals.get('operator_name'):
            vals['operator_name'] = vals['operator_name'].upper()

        if vals.get('customer_representative_name'):
            vals['customer_representative_name'] = vals['customer_representative_name'].upper()

        return super().write(vals)

    # ============================================================
    # THUMBNAILS (para reportes PDF, evitar std::bad_alloc)
    # - No toca imágenes originales.
    # - Genera thumbnails JPEG 1024px lado mayor.
    # - Guarda thumbnails como ir.attachment ligados a maintenance.order
    #   con nombre: <orig_name>__thumb_1024.jpg
    # ============================================================
    def _get_report_image_attachments(self):
        """Attachments used in LDN report: diagnosis images + parts images."""
        self.ensure_one()
        atts = self.env["ir.attachment"].browse()

        for diag in self.diagnosis_ids:
            atts |= diag.image_ids

        atts |= self.parts_image_ids

        return atts.filtered(lambda a: a.datas and (a.mimetype or "").startswith("image"))

    def _thumb_name_for_attachment(self, attachment, max_side=1024):
           return f"att_{attachment.id}__thumb_{max_side}.jpg"

    def _ensure_thumbnail_attachment(self, attachment, max_side=1024, quality=75):
        """Create (or reuse) a thumbnail attachment for 'attachment'.

        Thumbnail is stored as ir.attachment linked to this maintenance.order record.
        """
        self.ensure_one()

        thumb_name = self._thumb_name_for_attachment(attachment, max_side=max_side)

        existing = self.env["ir.attachment"].search([
            ("res_model", "=", self._name),
            ("res_id", "=", self.id),
            ("name", "=", thumb_name),
            ("mimetype", "=", "image/jpeg"),
        ], limit=1)
        if existing:
            return existing

        try:
            from PIL import Image, ImageOps
        except Exception as e:
            raise UserError(
                "No se encontró Pillow (PIL). Instálalo en el entorno de Odoo para generar thumbnails."
            ) from e

        raw = base64.b64decode(attachment.datas)
        img = Image.open(io.BytesIO(raw))

        # Fix EXIF orientation (iphone, etc.)
        try:
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass

        if img.mode != "RGB":
            img = img.convert("RGB")

        w, h = img.size
        if not w or not h:
            raise UserError(f"Imagen inválida en adjunto {attachment.id}")

        scale = float(max_side) / float(max(w, h))
        if scale < 1.0:
            new_w = max(1, int(w * scale))
            new_h = max(1, int(h * scale))
            img = img.resize((new_w, new_h), Image.LANCZOS)

        out = io.BytesIO()
        img.save(out, format="JPEG", quality=int(quality), optimize=True)
        out.seek(0)
        thumb_b64 = base64.b64encode(out.read())

        return self.env["ir.attachment"].create({
            "name": thumb_name,
            "type": "binary",
            "datas": thumb_b64,
            "mimetype": "image/jpeg",
            "res_model": self._name,   # maintenance.order
            "res_id": self.id,
        })

    def action_generate_report_thumbnails(self, max_side=1024, quality=75):
        """Generate thumbnails for all report images in this order."""
        for order in self:
            for att in order._get_report_image_attachments():
                order._ensure_thumbnail_attachment(att, max_side=max_side, quality=quality)
        return True

    def _get_thumb_for_attachment(self, attachment, max_side=1024):
        """Return thumbnail attachment record (or False)."""
        self.ensure_one()
        thumb_name = self._thumb_name_for_attachment(attachment, max_side=max_side)
        return self.env["ir.attachment"].search([
            ("res_model", "=", self._name),
            ("res_id", "=", self.id),
            ("name", "=", thumb_name),
            ("mimetype", "=", "image/jpeg"),
        ], limit=1)

    def action_download_diagnosis_collages_zip(self):
        self.ensure_one()

        try:
            from PIL import Image
        except Exception as e:
            raise UserError(
                "No se encontró Pillow (PIL). Instálalo en el entorno de Odoo para generar los collages."
            ) from e

        def _sanitize_filename(name: str) -> str:
            name = name or "archivo"
            name = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("_")
            return name or "archivo"

        def _fit_cover(img: "Image.Image", target_w: int, target_h: int) -> "Image.Image":
            img = img.convert("RGB")
            src_w, src_h = img.size
            if not src_w or not src_h:
                return Image.new("RGB", (target_w, target_h), (255, 255, 255))

            scale = max(target_w / src_w, target_h / src_h)
            new_w = int(src_w * scale)
            new_h = int(src_h * scale)
            img = img.resize((new_w, new_h), Image.LANCZOS)

            left = (new_w - target_w) // 2
            top = (new_h - target_h) // 2
            right = left + target_w
            bottom = top + target_h
            return img.crop((left, top, right, bottom))

        max_cols = 3
        max_rows = 4
        per_page = max_cols * max_rows

        gap = 5
        bg = (255, 255, 255)
        cell_w = 600
        cell_h = 600

        vehicle_name = _sanitize_filename(self.vehicle_id.display_name if self.vehicle_id else self.name)

        all_images = self.env["ir.attachment"].browse()

        # Diagnósticos
        for diag in self.diagnosis_ids.sorted(key=lambda d: d.id):
            imgs = diag.image_ids.filtered(lambda a: a.datas and (a.mimetype or "").startswith("image")).sorted(key=lambda a: a.id)
            all_images |= imgs

        # Repuestos (orden)
        rep_imgs = self.parts_image_ids.filtered(lambda a: a.datas and (a.mimetype or "").startswith("image")).sorted(key=lambda a: a.id)
        all_images |= rep_imgs

        if not all_images:
            raise UserError("No hay imágenes en los diagnósticos ni en los repuestos de esta orden.")

        pages = int(math.ceil(len(all_images) / per_page))

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for page in range(pages):
                chunk = all_images[page * per_page:(page + 1) * per_page]
                n = len(chunk)

                if page < pages - 1:
                    cols = max_cols
                    rows = max_rows
                else:
                    cols = min(max_cols, n)
                    rows = int(math.ceil(n / cols))
                    rows = min(max_rows, rows)

                collage_w = cols * cell_w + (cols + 1) * gap
                collage_h = rows * cell_h + (rows + 1) * gap
                collage = Image.new("RGB", (collage_w, collage_h), bg)

                for i, att in enumerate(chunk):
                    raw = base64.b64decode(att.datas)
                    img = Image.open(io.BytesIO(raw))
                    tile = _fit_cover(img, cell_w, cell_h)

                    r = i // cols
                    c = i % cols
                    x0 = gap + c * (cell_w + gap)
                    y0 = gap + r * (cell_h + gap)
                    collage.paste(tile, (x0, y0))

                out = io.BytesIO()
                collage.save(out, format="JPEG", quality=90, optimize=True)
                out.seek(0)

                jpeg_name = f"{vehicle_name}__collage__p{page + 1}.jpeg"
                zf.writestr(jpeg_name, out.read())

        zip_buffer.seek(0)
        zip_b64 = base64.b64encode(zip_buffer.read())

        att = self.env["ir.attachment"].create({
            "name": f"{vehicle_name}.zip",
            "type": "binary",
            "datas": zip_b64,
            "mimetype": "application/zip",
            "res_model": "maintenance.order",
            "res_id": self.id,
        })

        return {"type": "ir.actions.act_url", "url": f"/web/content/{att.id}?download=true", "target": "self"}
    
    include_spares_ldn = fields.Boolean(
        string="Incluir repuestos en reporte LDN",
        default=False,
        help="Si está activado, el reporte LDN incluirá la lista de repuestos. "
            "Si no hay diagnósticos, los repuestos se incluyen por defecto."
    )


class MaintenanceOrderPartLine(models.Model):
    _name = 'maintenance.order.part.line'
    _description = 'Repuestos de Orden de Mantenimiento'
    _order = 'id asc'

    order_id = fields.Many2one(
        'maintenance.order',
        string='Orden de Mantenimiento',
        required=True,
        ondelete='cascade',
        index=True
    )

    product_name = fields.Char(
        string='Repuesto',
        required=True,
        tracking=True,
        help='Nombre del repuesto (texto libre).'
    )
    qty_requested = fields.Float(string='Cant. Solicitada', default=0.0, tracking=True)
    qty_delivered = fields.Float(string='Cant. Entregada', default=0.0, tracking=True)
    notes = fields.Char(string='Notas', tracking=True)

    requested_by = fields.Many2one('res.users', string='Solicitado por', readonly=True)
    requested_date = fields.Datetime(string='Fecha solicitud', readonly=True)
    delivered_by = fields.Many2one('res.users', string='Entregado por', readonly=True)
    delivered_date = fields.Datetime(string='Fecha entrega', readonly=True)

    state = fields.Selection(
        [('draft', 'Borrador'), ('requested', 'Solicitado'), ('delivered', 'Entregado')],
        string='Estado',
        default='draft',
        tracking=True
    )

    def action_request(self):
        for line in self:
            line.write({
                'state': 'requested',
                'requested_by': self.env.user.id,
                'requested_date': fields.Datetime.now(),
            })

            if line.order_id:
                msg = "\n".join([
                    "Repuesto solicitado",
                    f"Usuario: {self.env.user.display_name}",
                    f"Repuesto: {line.product_name or ''}",
                    f"Cantidad solicitada: {line.qty_requested}",
                ])
                line.order_id.message_post(body=msg, subtype_xmlid="mail.mt_note")

    def action_deliver(self):
        allowed = (
            self.env.user.has_group("global_trucks_mtto.group_mtto_admin")
            or self.env.user.has_group("global_trucks_mtto.group_mtto_supervisor")
            or self.env.user.has_group("global_trucks_mtto.group_mtto_sales")
        )
        if not allowed:
            raise AccessError(
                "No tienes permisos para entregar repuestos. Solo Ventas/Supervisor/Administración pueden entregar."
            )

        for line in self:
            qty_delivered = line.qty_delivered
            auto_qty = False
            if not qty_delivered and line.qty_requested:
                qty_delivered = line.qty_requested
                auto_qty = True

            line.write({
                'qty_delivered': qty_delivered,
                'state': 'delivered',
                'delivered_by': self.env.user.id,
                'delivered_date': fields.Datetime.now(),
            })

            if line.order_id:
                lines = [
                    "Repuesto entregado",
                    f"Usuario: {self.env.user.display_name}",
                    f"Repuesto: {line.product_name or ''}",
                    f"Cantidad entregada: {qty_delivered}",
                ]
                if auto_qty:
                    lines.append("Nota: Cantidad entregada tomada automáticamente de la cantidad solicitada.")
                line.order_id.message_post(body="\n".join(lines), subtype_xmlid="mail.mt_note")

    @api.model_create_multi
    def create(self, vals_list):
        now = fields.Datetime.now()
        uid = self.env.user.id
        for vals in vals_list:
            st = vals.get('state') or 'draft'
            if st == 'requested':
                vals.setdefault('requested_by', uid)
                vals.setdefault('requested_date', now)
            elif st == 'delivered':
                vals.setdefault('delivered_by', uid)
                vals.setdefault('delivered_date', now)
                if not vals.get('qty_delivered') and vals.get('qty_requested'):
                    vals['qty_delivered'] = vals['qty_requested']
        return super().create(vals_list)


class MaintenanceDiagnosis(models.Model):
    _name = 'maintenance.diagnosis'
    _description = 'Diagnósticos de Fallas'

    order_id = fields.Many2one('maintenance.order', string='Orden de Mantenimiento', required=True, ondelete='cascade')
    name = fields.Text(string='Descripción de la Falla', required=True)

    image_ids = fields.Many2many('ir.attachment', string='Imágenes Adjuntas', domain=[('mimetype', 'ilike', 'image')])

    is_completed = fields.Boolean(string='Está Completado', default=False)

    followup_ids = fields.One2many('diagnosis.followup', 'diagnosis_id', string='Seguimientos')

    attachment_count = fields.Integer(string="Número de Adjuntos", compute="_compute_attachment_count")

    @api.depends('image_ids')
    def _compute_attachment_count(self):
        for record in self:
            record.attachment_count = len(record.image_ids)

    def action_view_images(self):
        self.ensure_one()
        return {
            'name': 'Galería de Imágenes',
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'kanban,list,form',
            'domain': [('id', 'in', self.image_ids.ids)],
            'context': {'default_res_model': 'maintenance.diagnosis', 'default_res_id': self.id}
        }


class DiagnosisFollowup(models.Model):
    _name = 'diagnosis.followup'
    _description = 'Seguimientos de Diagnósticos'

    diagnosis_id = fields.Many2one('maintenance.diagnosis', string='Diagnóstico', required=True, ondelete='cascade')
    name = fields.Text(string='Descripción del Trabajo o Actividad', required=True)
