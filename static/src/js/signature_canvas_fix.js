/** @odoo-module **/

let isInitialized = false;

function initSignatureCanvasFix() {
    if (isInitialized) return;
    isInitialized = true;
    
    // Ejecutar al cargar
    setTimeout(fixSignatureCanvas, 500);
    
    // Ejecutar al cambiar orientación
    window.addEventListener('orientationchange', function() {
        setTimeout(fixSignatureCanvas, 500);
    });
    
    // Ejecutar al redimensionar
    let resizeTimeout;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(fixSignatureCanvas, 300);
    });
    
    // Observar cuando se abran modales
    setTimeout(function() {
        if (document.body) {
            const observer = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    mutation.addedNodes.forEach(function(node) {
                        if (node.nodeType === 1 && node.classList) {
                            if (node.classList.contains('modal') || 
                                node.classList.contains('o_web_sign_name_and_signature_modal')) {
                                setTimeout(fixSignatureCanvas, 300);
                            }
                        }
                    });
                });
            });
            
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        }
    }, 1000);
    
    // Observar clicks en campos de firma
    document.addEventListener('click', function(e) {
        const target = e.target;
        if (target && (
            target.classList.contains('o_field_signature') ||
            target.closest('.o_field_signature') ||
            target.classList.contains('o_web_sign_auto_button')
        )) {
            setTimeout(fixSignatureCanvas, 500);
        }
    }, true);
}

function fixSignatureCanvas() {
    // Buscar todos los canvas de firma
    const canvases = document.querySelectorAll(
        '.o_field_signature canvas, ' +
        '.o_web_sign_signature canvas, ' +
        '.o_web_sign_name_and_signature_modal canvas, ' +
        '.modal canvas'
    );
    
    if (canvases.length === 0) return;
    
    canvases.forEach(canvas => {
        try {
            if (!canvas || !canvas.getContext) return;
            
            // Evitar procesar el mismo canvas múltiples veces seguidas
            const now = Date.now();
            if (canvas.dataset.lastFixed && (now - parseInt(canvas.dataset.lastFixed)) < 500) {
                return;
            }
            canvas.dataset.lastFixed = now;
            
            // Obtener el contenedor
            const container = canvas.parentElement;
            if (!container) return;
            
            const rect = container.getBoundingClientRect();
            if (rect.width === 0) return; // El elemento no está visible
            
            const isModal = canvas.closest('.modal') !== null;
            const isMobile = window.innerWidth <= 768;
            const isPortrait = window.innerHeight > window.innerWidth;
            
            let desiredHeight = 250; // Default desktop
            
            // Determinar altura deseada según dispositivo y orientación
            if (isModal) {
                if (isMobile) {
                    if (isPortrait) {
                        desiredHeight = window.innerWidth <= 480 ? 350 : 400;
                    } else {
                        desiredHeight = 200;
                    }
                } else if (window.innerWidth <= 992) {
                    desiredHeight = 280;
                }
            }
            
            // Guardar los datos actuales del canvas si existen
            let imageData = null;
            try {
                imageData = canvas.toDataURL();
            } catch (e) {
                // Ignorar errores de seguridad
            }
            
            // Calcular el ancho basado en el contenedor
            const desiredWidth = rect.width > 0 ? rect.width : 800;
            
            // Configurar el tamaño REAL del canvas (resolución interna)
            canvas.width = desiredWidth;
            canvas.height = desiredHeight;
            
            // Configurar el tamaño CSS (visual)
            canvas.style.width = '100%';
            canvas.style.height = desiredHeight + 'px';
            
            // Restaurar el contexto de dibujo
            const ctx = canvas.getContext('2d');
            if (ctx) {
                ctx.strokeStyle = '#000080'; // Azul oscuro
                ctx.lineWidth = 2;
                ctx.lineCap = 'round';
                ctx.lineJoin = 'round';
                
                // Restaurar el contenido si existía
                if (imageData && !isEmptyCanvas(imageData)) {
                    const img = new Image();
                    img.onload = function() {
                        try {
                            ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                        } catch (e) {
                            console.warn('No se pudo restaurar la firma:', e);
                        }
                    };
                    img.onerror = function() {
                        console.warn('Error al cargar la imagen de firma');
                    };
                    img.src = imageData;
                }
            }
        } catch (error) {
            console.warn('Error al ajustar canvas de firma:', error);
        }
    });
}

function isEmptyCanvas(dataURL) {
    // Verificar si el canvas está vacío comparando con un canvas en blanco
    return dataURL === 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==';
}

// Inicializar cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initSignatureCanvasFix);
} else {
    // El DOM ya está listo
    initSignatureCanvasFix();
}

// Log para debugging
console.log('Signature Canvas Fix v2 loaded');
