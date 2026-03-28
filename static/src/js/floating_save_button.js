/** @odoo-module **/

import { FormController } from "@web/views/form/form_controller";
import { patch } from "@web/core/utils/patch";
import { useEffect } from "@odoo/owl";

patch(FormController.prototype, {
    setup() {
        super.setup(...arguments);
        
        useEffect(() => {
            // Crear el botón flotante si no existe
            if (!this.floatingSaveButton) {
                this.createFloatingButton();
            }
            
            return () => {
                // Limpiar al desmontar
                if (this.floatingSaveButton) {
                    this.floatingSaveButton.remove();
                    this.floatingSaveButton = null;
                }
            };
        });
    },

    createFloatingButton() {
        // Verificar si estamos en un formulario relevante
        const isMaintenanceForm = ['maintenance.order', 'maintenance.diagnosis'].includes(
            this.props.resModel
        );
        
        if (!isMaintenanceForm) {
            return;
        }

        // Crear el botón
        const button = document.createElement('button');
        button.className = 'o_form_button_save_floating btn';
        button.type = 'button';
        button.innerHTML = '<i class="fa fa-save"></i>';
        button.title = 'Guardar cambios';
        
        // Agregar evento de click
        button.addEventListener('click', () => {
            this.saveButtonClick();
        });
        
        // Agregar al DOM
        document.body.appendChild(button);
        this.floatingSaveButton = button;
    },

    async saveButtonClick() {
        // Ejecutar la función de guardar del formulario
        await this.model.root.save();
        
        // Feedback visual
        if (this.floatingSaveButton) {
            const icon = this.floatingSaveButton.querySelector('i');
            icon.className = 'fa fa-check';
            
            setTimeout(() => {
                icon.className = 'fa fa-save';
            }, 2000);
        }
    }
});
