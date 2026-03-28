/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ListController } from "@web/views/list/list_controller";

/**
 * Autosave antes de ejecutar botones type="object" en list (one2many inline).
 * Se activa únicamente si el botón tiene data-autosave="1".
 */
patch(ListController.prototype, {
    async onButtonClicked(ev) {
        const dataset = ev?.target?.dataset || {};
        const autosave = dataset.autosave === "1";

        if (autosave) {
            try {
                // Guardar cambios pendientes antes de ejecutar el botón
                await this.model.root.save({ stayInEdition: true, reload: false });
            } catch (e) {
                // Si falla el guardado, dejamos que el flujo normal de Odoo maneje el error
            }
        }
        return super.onButtonClicked(ev);
    },
});

