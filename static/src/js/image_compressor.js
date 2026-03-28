/** @odoo-module **/

import { FileInput } from "@web/core/file_input/file_input";
import { patch } from "@web/core/utils/patch";

patch(FileInput.prototype, {
    async uploadFiles(files) {
        const MAX_SIZE = 5 * 1024 * 1024; // Solo comprimir si > 5MB
        const processedFiles = [];
        
        for (const file of files) {
            if (file.type.startsWith('image/') && file.size > MAX_SIZE) {
                try {
                    const compressed = await this.quickCompress(file);
                    processedFiles.push(compressed);
                } catch (error) {
                    processedFiles.push(file); // Si falla, usar original
                }
            } else {
                processedFiles.push(file); // No comprimir
            }
        }
        
        return await this._super(processedFiles);
    },

    async quickCompress(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                const img = new Image();
                img.onload = () => {
                    const canvas = document.createElement('canvas');
                    const MAX = 1400;
                    let w = img.width, h = img.height;
                    
                    if (w > MAX || h > MAX) {
                        const r = Math.min(MAX / w, MAX / h);
                        w = Math.round(w * r);
                        h = Math.round(h * r);
                    }
                    
                    canvas.width = w;
                    canvas.height = h;
                    canvas.getContext('2d').drawImage(img, 0, 0, w, h);
                    
                    canvas.toBlob(
                        (blob) => resolve(new File([blob], file.name.replace(/\.[^/.]+$/, '.jpg'), {type: 'image/jpeg'})),
                        'image/jpeg',
                        0.7
                    );
                };
                img.src = e.target.result;
            };
            reader.readAsDataURL(file);
        });
    },
});
