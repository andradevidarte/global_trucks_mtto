/** global_trucks_mtto/static/src/js/mobile_detection.js **/

odoo.define('global_trucks_mtto.mobile_detection', function (require) {
    'use strict';

    const core = require('web.core');
    const session = require('web.session');
    const ActionManager = require('web.ActionManager');

    const MOBILE_BREAKPOINT = 768;  // Ancho máximo en píxeles para dispositivos móviles.

    ActionManager.include({
        _executeWindowAction: function (action, options) {
            if (action.res_model === 'maintenance.order') {
                // Detecta el ancho de la pantalla.
                const isMobile = window.innerWidth <= MOBILE_BREAKPOINT;

                // Vista predeterminada: Kanban para dispositivos móviles o List para equipos grandes.
                if (isMobile) {
                    action.views = [[false, 'kanban'], [false, 'list']]; // Móvil: Kanban primero.
                } else {
                    action.views = [[false, 'list'], [false, 'kanban']]; // PC: Lista primero.
                }
            }

            return this._super(action, options);
        },
    });
});
