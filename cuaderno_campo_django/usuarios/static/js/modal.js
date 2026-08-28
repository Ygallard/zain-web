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

function escapeDetailHTML(value) {
    return String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function normalizeDetailValue(value) {
    if (value === null || value === undefined || value === '') {
        return '-';
    }

    if (Array.isArray(value)) {
        return value.length ? value.join(', ') : '-';
    }

    if (typeof value === 'boolean') {
        return value ? 'Si' : 'No';
    }

    return value;
}

function inferDetailTheme(title) {
    const text = String(title || '').toLowerCase();
    if (text.includes('riego')) return { icon: 'bi-droplet-half', theme: 'detail-theme-water' };
    if (text.includes('cosecha')) return { icon: 'bi-basket2-fill', theme: 'detail-theme-harvest' };
    if (text.includes('fertiliz')) return { icon: 'bi-flower2', theme: 'detail-theme-fertilizer' };
    if (text.includes('quimic')) return { icon: 'bi-bezier2', theme: 'detail-theme-chem' };
    if (text.includes('predio')) return { icon: 'bi-geo-alt-fill', theme: 'detail-theme-land' };
    if (text.includes('cuartel')) return { icon: 'bi-grid-3x3-gap-fill', theme: 'detail-theme-land' };
    if (text.includes('labor') || text.includes('poda') || text.includes('brote')) return { icon: 'bi-tools', theme: 'detail-theme-agro' };
    if (text.includes('usuario')) return { icon: 'bi-person-badge-fill', theme: 'detail-theme-user' };
    if (text.includes('auditor')) return { icon: 'bi-shield-check', theme: 'detail-theme-audit' };
    return { icon: 'bi-card-list', theme: 'detail-theme-agro' };
}

function inferSectionIcon(sectionTitle) {
    const text = String(sectionTitle || '').toLowerCase();
    if (text.includes('general')) return 'bi-info-circle-fill';
    if (text.includes('agric')) return 'bi-tree-fill';
    if (text.includes('observ')) return 'bi-chat-left-text-fill';
    if (text.includes('fecha') || text.includes('trazabilidad') || text.includes('auditor')) return 'bi-clock-history';
    if (text.includes('ident')) return 'bi-patch-check-fill';
    if (text.includes('aplic')) return 'bi-droplet-fill';
    return 'bi-dot';
}

function getStatusBadge(value) {
    const text = String(value || '').trim();
    const normalized = text.toLowerCase();
    let badgeClass = '';

    if (['activo', 'activa', 'si', 'sí', 'habilitado', 'vigente'].includes(normalized)) {
        badgeClass = 'detail-badge-success';
    } else if (['inactivo', 'inactiva', 'no', 'deshabilitado', 'eliminado'].includes(normalized)) {
        badgeClass = 'detail-badge-danger';
    } else if (['pendiente', 'en proceso', 'borrador', 'regular'].includes(normalized)) {
        badgeClass = 'detail-badge-warning';
    }

    if (!badgeClass) {
        return '';
    }

    return `<span class="detail-badge ${badgeClass}">${escapeDetailHTML(text)}</span>`;
}

function ensureRecordDetailModal() {
    let modal = document.getElementById('recordDetailModal');
    if (modal) {
        return modal;
    }

    modal = document.createElement('div');
    modal.id = 'recordDetailModal';
    modal.className = 'modal-overlay detail-modal-overlay';
    modal.innerHTML = `
        <div class="modal detail-modal detail-theme-agro" role="dialog" aria-modal="true" aria-labelledby="recordDetailTitle">
            <div class="modal-header detail-modal-header">
                <div class="detail-modal-title-wrap">
                    <div class="detail-modal-title-line">
                        <span class="detail-modal-icon" id="recordDetailIcon"><i class="bi bi-card-list"></i></span>
                        <h2 class="modal-title" id="recordDetailTitle">Detalle del registro</h2>
                    </div>
                    <p class="detail-modal-subtitle">Información completa del registro seleccionado.</p>
                </div>
                <button class="modal-close" type="button" aria-label="Cerrar detalle">
                    <i class="bi bi-x-lg"></i>
                </button>
            </div>
            <div class="modal-body detail-modal-body" id="recordDetailContent"></div>
            <div class="modal-footer">
                <button class="btn btn-secondary" type="button" id="recordDetailCloseBtn">
                    <i class="bi bi-x-circle"></i> Cerrar
                </button>
            </div>
        </div>
    `;

    const close = () => closeModal('recordDetailModal');
    modal.querySelector('.modal-close').addEventListener('click', close);
    modal.querySelector('#recordDetailCloseBtn').addEventListener('click', close);
    modal.addEventListener('click', (event) => {
        if (event.target === modal) {
            close();
        }
    });

    document.body.appendChild(modal);
    return modal;
}

function openRecordDetailModal(title, sections) {
    ensureRecordDetailModal();

    const titleEl = document.getElementById('recordDetailTitle');
    const iconEl = document.getElementById('recordDetailIcon');
    const subtitleEl = document.querySelector('#recordDetailModal .detail-modal-subtitle');
    const contentEl = document.getElementById('recordDetailContent');
    if (!titleEl || !contentEl) {
        return;
    }

    const resolvedTitle = title || 'Detalle del registro';
    const inferredTheme = inferDetailTheme(resolvedTitle);
    const modalEl = document.querySelector('#recordDetailModal .detail-modal');
    if (modalEl) {
        modalEl.className = `modal detail-modal ${inferredTheme.theme}`;
    }

    titleEl.textContent = resolvedTitle;
    if (iconEl) {
        iconEl.innerHTML = `<i class="bi ${inferredTheme.icon}"></i>`;
    }
    if (subtitleEl) {
        subtitleEl.textContent = 'Información completa del registro seleccionado.';
    }

    const sectionsMarkup = (sections || []).map((section) => {
        const sectionIcon = section.icon || inferSectionIcon(section.title);
        const fields = (section.fields || []).map((field) => {
            const normalized = normalizeDetailValue(field.value);
            const value = escapeDetailHTML(normalized);
            const isEmptyValue = normalized === '-';
            const isWide = String(normalized).length > 70;
            const badge = getStatusBadge(normalized);
            return `
                <div class="detail-row ${isWide ? 'detail-row-full' : ''}">
                    <div class="detail-cell detail-cell-label">${escapeDetailHTML(field.label)}</div>
                    <div class="detail-cell detail-cell-value">
                        <span class="detail-value ${isEmptyValue ? 'detail-value-empty' : ''}">${badge || value}</span>
                    </div>
                </div>
            `;
        }).join('');

        return `
            <section class="detail-section-card">
                <h3 class="detail-section-title">
                    <i class="bi ${sectionIcon}"></i>
                    <span>${escapeDetailHTML(section.title || 'Información')}</span>
                </h3>
                <div class="detail-rows">${fields}</div>
            </section>
        `;
    }).join('');

    contentEl.innerHTML = sectionsMarkup || '<p class="detail-empty">Sin información disponible para este registro.</p>';
    openModal('recordDetailModal');
}

function initRecordRowDetails(config) {
    const {
        containerSelector,
        rowSelector = 'tr[data-id]',
        fetchUrl,
        parseResponse,
        title,
        buildSections,
    } = config || {};

    if (!containerSelector || typeof fetchUrl !== 'function' || typeof parseResponse !== 'function' || typeof buildSections !== 'function') {
        return;
    }

    const container = document.querySelector(containerSelector);
    if (!container || container.dataset.detailsBound === 'true') {
        return;
    }

    if (container.querySelector('[onclick*="openRegistroDetalle"]')) {
        return;
    }

    const refreshRows = () => {
        container.querySelectorAll(rowSelector).forEach((row) => {
            if (row.dataset.id) {
                row.classList.add('js-row-detail');
            }
        });
    };

    refreshRows();

    const observer = new MutationObserver(refreshRows);
    observer.observe(container, { childList: true, subtree: true });

    container.addEventListener('click', async (event) => {
        const row = event.target.closest(rowSelector);
        if (!row || !container.contains(row)) {
            return;
        }

        if (event.target.closest('button, a, input, select, textarea, label, .actions-cell, [data-no-row-detail]')) {
            return;
        }

        const id = row.dataset.id;
        if (!id) {
            return;
        }

        row.classList.add('row-detail-loading');

        try {
            const response = await fetch(fetchUrl(id));
            const payload = await response.json();
            if (!payload.success) {
                throw new Error(payload.error || 'No fue posible cargar el detalle.');
            }

            const record = parseResponse(payload);
            const sections = buildSections(record || {});
            openRecordDetailModal(typeof title === 'function' ? title(record || {}) : title, sections);
        } catch (error) {
            showToast(error.message || 'No fue posible abrir el detalle del registro.', 'error');
        } finally {
            row.classList.remove('row-detail-loading');
        }
    });

    container.dataset.detailsBound = 'true';
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
