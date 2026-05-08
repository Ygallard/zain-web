/* ============================================
   MODAL MANAGER - Sistema de modales unificado
   ============================================ */

/**
 * Abre un modal
 * @param {string} modalId - ID del elemento modal
 */
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
    }
}

/**
 * Cierra un modal
 * @param {string} modalId - ID del elemento modal
 */
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
    }
}

/**
 * Abre un modal de confirmación
 * @param {string} title - Título del modal
 * @param {string} message - Mensaje a mostrar
 * @param {function} onConfirm - Callback al confirmar
 * @param {string} confirmText - Texto del botón confirmar
 * @param {string} cancelText - Texto del botón cancelar
 */
function showConfirmModal(title, message, onConfirm, confirmText = 'Confirmar', cancelText = 'Cancelar') {
    const confirmModal = document.createElement('div');
    confirmModal.className = 'modal-overlay active';
    confirmModal.innerHTML = `
        <div class="modal" style="max-width: 400px;">
            <div class="modal-header">
                <h2 class="modal-title">
                    <i class="bi bi-exclamation-triangle-fill"></i> ${title}
                </h2>
                <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">
                    <i class="bi bi-x-lg"></i>
                </button>
            </div>
            <div class="modal-body">
                <p>${message}</p>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary" onclick="this.closest('.modal-overlay').remove()">
                    <i class="bi bi-x-circle"></i> ${cancelText}
                </button>
                <button class="btn btn-primary" onclick="handleConfirm()">
                    <i class="bi bi-check-circle"></i> ${confirmText}
                </button>
            </div>
        </div>
    `;
    
    window.handleConfirm = function() {
        onConfirm();
        confirmModal.remove();
    };
    
    // Cerrar al hacer clic fuera del modal
    confirmModal.addEventListener('click', function(e) {
        if (e.target === this) {
            this.remove();
        }
    });
    
    document.body.appendChild(confirmModal);
}

/**
 * Muestra una notificación toast
 * @param {string} message - Mensaje a mostrar
 * @param {string} type - Tipo: 'success', 'error', 'info', 'warning'
 * @param {number} duration - Duración en ms
 */
function showToast(message, type = 'info', duration = 3000) {
    const toastContainer = document.getElementById('toast-container') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <i class="bi bi-${getToastIcon(type)}"></i>
        <span>${message}</span>
    `;
    
    toastContainer.appendChild(toast);
    
    // Auto-remove after duration
    setTimeout(() => {
        toast.classList.add('fade-out');
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

/**
 * Obtiene el ícono según el tipo de toast
 */
function getToastIcon(type) {
    const icons = {
        success: 'check-circle-fill',
        error: 'exclamation-circle-fill',
        info: 'info-circle-fill',
        warning: 'exclamation-triangle-fill'
    };
    return icons[type] || icons.info;
}

/**
 * Crea el contenedor de toasts
 */
function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        display: flex;
        flex-direction: column;
        gap: 10px;
        pointer-events: none;
    `;
    document.body.appendChild(container);
    return container;
}

// Estilos para toasts
if (!document.getElementById('toast-styles')) {
    const style = document.createElement('style');
    style.id = 'toast-styles';
    style.textContent = `
        .toast {
            background: white;
            border-radius: 8px;
            padding: 1rem 1.5rem;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            display: flex;
            align-items: center;
            gap: 0.8rem;
            font-weight: 600;
            font-size: 0.95rem;
            animation: slideInRight 0.3s ease;
            pointer-events: auto;
            min-width: 300px;
        }

        .toast-success {
            border-left: 4px solid #2ecc71;
            color: #27ae60;
        }

        .toast-error {
            border-left: 4px solid #e74c3c;
            color: #c0392b;
        }

        .toast-info {
            border-left: 4px solid #3498db;
            color: #2980b9;
        }

        .toast-warning {
            border-left: 4px solid #f39c12;
            color: #d68910;
        }

        .toast.fade-out {
            animation: slideOutRight 0.3s ease;
        }

        @keyframes slideInRight {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }

        @keyframes slideOutRight {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(100%);
                opacity: 0;
            }
        }

        @media (max-width: 576px) {
            .toast {
                min-width: 90vw;
            }
        }
    `;
    document.head.appendChild(style);
}

/**
 * Valida un formulario
 * @param {string} formId - ID del formulario
 * @returns {boolean}
 */
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return false;
    
    const fields = form.querySelectorAll('[required]');
    let isValid = true;
    
    fields.forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('is-invalid');
            isValid = false;
        } else {
            field.classList.remove('is-invalid');
        }
    });
    
    return isValid;
}

/**
 * Habilita/deshabilita un botón
 * @param {string} buttonId - ID del botón
 * @param {boolean} disabled - Estado
 */
function setButtonDisabled(buttonId, disabled = true) {
    const btn = document.getElementById(buttonId);
    if (btn) {
        btn.disabled = disabled;
        btn.style.opacity = disabled ? '0.6' : '1';
    }
}

/**
 * Muestra un spinner de carga en un elemento
 * @param {string} elementId - ID del elemento
 * @param {boolean} show - Mostrar u ocultar
 */
function showSpinner(elementId, show = true) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    if (show) {
        element.innerHTML = `
            <div class="loading-spinner"></div>
            <span style="margin-left: 0.5rem;">Cargando...</span>
        `;
    }
}

/**
 * Hace una petición AJAX con manejo de errores
 * @param {string} url - URL a solicitar
 * @param {object} options - Opciones adicionales
 * @returns {Promise}
 */
async function makeRequest(url, options = {}) {
    const defaultOptions = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        }
    };
    
    const finalOptions = { ...defaultOptions, ...options };
    
    try {
        const response = await fetch(url, finalOptions);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        return { success: true, data };
    } catch (error) {
        console.error('Request error:', error);
        return { success: false, error: error.message };
    }
}

/**
 * Obtiene un cookie por nombre
 * @param {string} name - Nombre del cookie
 * @returns {string|null}
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/**
 * Formatea una fecha
 * @param {string|Date} date - Fecha a formatear
 * @param {string} format - Formato (ej: 'dd/mm/yyyy')
 * @returns {string}
 */
function formatDate(date, format = 'dd/mm/yyyy') {
    const d = new Date(date);
    const day = String(d.getDate()).padStart(2, '0');
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const year = d.getFullYear();
    
    return format
        .replace('dd', day)
        .replace('mm', month)
        .replace('yyyy', year);
}

/**
 * Valida un RUT chileno
 * @param {string} rut - RUT a validar
 * @returns {boolean}
 */
function validateRUT(rut) {
    const rutRegex = /^(\d{1,3}\.?\d{3}\.?\d{3}-)([0-9K])$/;
    return rutRegex.test(rut.toUpperCase());
}

/**
 * Valida un correo electrónico
 * @param {string} email - Email a validar
 * @returns {boolean}
 */
function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

/**
 * Valida un teléfono
 * @param {string} phone - Teléfono a validar
 * @returns {boolean}
 */
function validatePhone(phone) {
    const phoneRegex = /^(\+56)?[0-9]{8,9}$/;
    return phoneRegex.test(phone.replace(/[^\d+]/g, ''));
}

// Inicialización al cargar el documento
document.addEventListener('DOMContentLoaded', function() {
    // Cerrar modales al presionar ESC
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            const activeModals = document.querySelectorAll('.modal-overlay.active');
            activeModals.forEach(modal => {
                modal.classList.remove('active');
            });
        }
    });
});

console.log('✅ Modal Manager loaded');
