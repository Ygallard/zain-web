/* ============================================
   COLABORACION: Notificaciones y Observaciones Tecnicas (PRODESAL)
   ============================================ */

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return decodeURIComponent(parts.pop().split(';').shift());
    return null;
}

function getCsrfToken() {
    return (window.ZAINO_CTX && window.ZAINO_CTX.csrfToken) || getCookie('csrftoken') || '';
}

const MODULO_DETAIL_ENDPOINTS = {
    predio: (id) => `/predios/${id}/`,
    cuartel: (id) => `/cuarteles/${id}/`,
    riego: (id) => `/riegos/${id}/`,
    fertilizacion: (id) => `/fertilizaciones/${id}/`,
    cosecha: (id) => `/cosechas/${id}/`,
    aplicacion_quimica: (id) => `/aplicaciones-quimicas/${id}/`,
    labor_agricola: (id) => `/labores-agricolas/${id}/`,
};

const MODULO_RESPONSE_KEY = {
    predio: 'predio',
    cuartel: 'cuartel',
    riego: 'riego',
    fertilizacion: 'fertilizacion',
    cosecha: 'cosecha',
    aplicacion_quimica: 'aplicacion',
    labor_agricola: 'labor',
};

const MODULO_TITULOS = {
    predio: 'Predio',
    cuartel: 'Cuartel',
    riego: 'Riego',
    fertilizacion: 'Fertilización',
    cosecha: 'Cosecha',
    aplicacion_quimica: 'Aplicación Química',
    labor_agricola: 'Labor Agrícola',
};

const MODULO_CAMPOS = {
    predio: [
        ['nombre_predio', 'Nombre del predio'],
        ['superficie_hectareas', 'Superficie (ha)'],
        ['inscripcion_cbr', 'Inscripción CBR'],
        ['inscripcion_agua', 'Inscripción de agua'],
        ['descripcion', 'Descripción'],
    ],
    cuartel: [
        ['nombre_cuartel', 'Nombre del cuartel'],
        ['predio_nombre', 'Predio'],
        ['tipo_cultivo_label', 'Tipo de cultivo'],
        ['variedad', 'Variedad'],
        ['forma_riego_label', 'Forma de riego'],
        ['anio_plantacion', 'Año de plantación'],
        ['superficie', 'Superficie'],
        ['descripcion', 'Descripción'],
    ],
    riego: [
        ['predio_nombre', 'Predio'],
        ['cuartel_nombre', 'Cuartel'],
        ['fecha_riego', 'Fecha de riego'],
        ['tipo_riego_label', 'Tipo de riego'],
        ['minutos_riego', 'Minutos de riego'],
        ['caudal', 'Caudal'],
        ['litros', 'Litros estimados'],
        ['observaciones', 'Observaciones'],
    ],
    fertilizacion: [
        ['predio_nombre', 'Predio'],
        ['cuartel_nombre', 'Cuartel'],
        ['fecha_aplicacion', 'Fecha de aplicación'],
        ['producto_label', 'Producto'],
        ['dosis', 'Dosis'],
        ['unidad', 'Unidad'],
        ['metodo_aplicacion', 'Método de aplicación'],
        ['observaciones', 'Observaciones'],
    ],
    cosecha: [
        ['predio_nombre', 'Predio'],
        ['cuartel_nombre', 'Cuartel'],
        ['fecha_cosecha', 'Fecha de cosecha'],
        ['tipo_cosecha', 'Tipo de cosecha'],
        ['cantidad_kg', 'Cantidad (kg)'],
        ['cantidad_bins', 'Cantidad (bins)'],
        ['calidad_label', 'Calidad'],
        ['destino_label', 'Destino'],
        ['observaciones', 'Observaciones'],
    ],
    aplicacion_quimica: [
        ['predio_nombre', 'Predio'],
        ['cuartel_nombre', 'Cuartel'],
        ['fecha_aplicacion', 'Fecha de aplicación'],
        ['producto', 'Producto'],
        ['tipo_producto', 'Tipo de producto'],
        ['dosis', 'Dosis'],
        ['unidad', 'Unidad'],
        ['metodo_aplicacion', 'Método de aplicación'],
        ['responsable', 'Aplicado por'],
        ['observaciones', 'Observaciones'],
    ],
    labor_agricola: [
        ['predio_nombre', 'Predio'],
        ['cuartel_nombre', 'Cuartel'],
        ['fecha', 'Fecha'],
        ['tipo_labor_label', 'Tipo de labor'],
        ['subtipo', 'Subtipo'],
        ['responsable', 'Registrado por'],
        ['descripcion', 'Descripción'],
        ['observaciones', 'Observaciones'],
    ],
};

let currentDetalleModulo = null;
let currentDetalleId = null;
let currentDetalleResponsableId = null;
let currentDetalleResponsableNombre = null;

function renderUbicacion(registro) {
    const box = document.getElementById('registroDetalleUbicacion');
    if (!box) return;

    if (!registro.ubicacion_disponible) {
        box.innerHTML = '<p style="color:#7f8c8d;">Ubicación no disponible</p>';
        return;
    }

    const filas = [
        ['Nombre del predio', registro.ubicacion_predio_nombre],
        ['Sector', registro.ubicacion_sector],
        ['Cuartel', registro.ubicacion_cuartel],
        ['Dirección', registro.ubicacion_direccion],
    ].filter(([, value]) => !!value);

    let html = '<table class="table registro-detalle-table">' +
        filas.map(([label, value]) => `<tr><td>${label}</td><td>${value}</td></tr>`).join('') +
        '</table>';

    const lat = parseFloat(registro.ubicacion_lat);
    const lng = parseFloat(registro.ubicacion_lng);
    if (!isNaN(lat) && !isNaN(lng)) {
        const delta = 0.01;
        const bbox = `${lng - delta},${lat - delta},${lng + delta},${lat + delta}`;
        html += `
            <div style="margin-top:0.75rem; border-radius:8px; overflow:hidden; border:1px solid #e8edf2;">
                <iframe title="Ubicación del registro" width="100%" height="220" frameborder="0" scrolling="no"
                    src="https://www.openstreetmap.org/export/embed.html?bbox=${bbox}&layer=mapnik&marker=${lat},${lng}"></iframe>
            </div>
        `;
    }

    box.innerHTML = html;
}

async function openRegistroDetalle(modulo, id) {
    currentDetalleModulo = modulo;
    currentDetalleId = id;
    currentDetalleResponsableId = null;
    currentDetalleResponsableNombre = null;

    const titulo = document.getElementById('registroDetalleTitulo');
    const tabla = document.getElementById('registroDetalleTabla');
    const responsableTabla = document.getElementById('registroDetalleResponsable');
    const ubicacionBox = document.getElementById('registroDetalleUbicacion');
    const comentariosBox = document.getElementById('registroDetalleComentarios');
    const comentarioForm = document.getElementById('registroDetalleComentarioForm');
    const notificarBtn = document.getElementById('registroDetalleNotificarBtn');

    titulo.textContent = `Detalle - ${MODULO_TITULOS[modulo] || modulo}`;
    tabla.innerHTML = '<tr><td>Cargando...</td></tr>';
    responsableTabla.innerHTML = '';
    ubicacionBox.innerHTML = '<p style="color:#7f8c8d;">Cargando ubicación...</p>';
    comentariosBox.innerHTML = '<p style="color:#7f8c8d;">Cargando observaciones...</p>';
    comentarioForm.style.display = 'none';
    if (notificarBtn) notificarBtn.style.display = 'none';

    openModal('registroDetalleModal');

    const endpointBuilder = MODULO_DETAIL_ENDPOINTS[modulo];
    if (!endpointBuilder) return;

    try {
        const response = await fetch(endpointBuilder(id), { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
        const payload = await response.json();
        if (!payload.success) {
            tabla.innerHTML = `<tr><td>${payload.error || 'No se pudo cargar el registro.'}</td></tr>`;
            ubicacionBox.innerHTML = '<p style="color:#7f8c8d;">Ubicación no disponible</p>';
            return;
        }

        const registro = payload[MODULO_RESPONSE_KEY[modulo]] || payload.data || {};
        const campos = MODULO_CAMPOS[modulo] || [];
        tabla.innerHTML = campos
            .map(([key, label]) => `<tr><td>${label}</td><td>${registro[key] ?? '-'}</td></tr>`)
            .join('');

        responsableTabla.innerHTML = `
            <tr><td>Responsable</td><td>${registro.responsable_nombre || '-'}</td></tr>
            <tr><td>Rol</td><td>${registro.responsable_rol || '-'}</td></tr>
            <tr><td>Fecha de registro</td><td>${registro.created_at || '-'}</td></tr>
        `;

        renderUbicacion(registro);

        currentDetalleResponsableId = registro.responsable_id || null;
        currentDetalleResponsableNombre = registro.responsable_nombre || null;

        if (notificarBtn && window.ZAINO_CTX && window.ZAINO_CTX.canSendNotifications && currentDetalleResponsableId) {
            notificarBtn.style.display = 'inline-flex';
        }
    } catch (error) {
        tabla.innerHTML = '<tr><td>Error al cargar el registro.</td></tr>';
        ubicacionBox.innerHTML = '<p style="color:#7f8c8d;">Ubicación no disponible</p>';
    }

    cargarComentariosRegistro(modulo, id);
}

function abrirNotificarSobreRegistro() {
    if (!currentDetalleResponsableId) return;
    document.getElementById('notificarRegistroProductorNombre').textContent = currentDetalleResponsableNombre || '';
    document.getElementById('notificarRegistroTitulo').value = '';
    document.getElementById('notificarRegistroMensaje').value = '';
    openModal('notificarRegistroModal');
}

async function enviarNotificacionSobreRegistro() {
    if (!currentDetalleModulo || !currentDetalleId) return;

    const titulo = document.getElementById('notificarRegistroTitulo').value.trim();
    const mensaje = document.getElementById('notificarRegistroMensaje').value.trim();

    if (!titulo || !mensaje) {
        if (typeof showToast === 'function') showToast('Completa título y mensaje antes de enviar.', 'warning');
        return;
    }

    const formData = new FormData();
    formData.append('modulo', currentDetalleModulo);
    formData.append('objeto_id', currentDetalleId);
    formData.append('titulo', titulo);
    formData.append('mensaje', mensaje);

    try {
        const response = await fetch('/notificaciones/crear/', {
            method: 'POST',
            headers: { 'X-CSRFToken': getCsrfToken(), 'X-Requested-With': 'XMLHttpRequest' },
            body: formData,
        });
        const payload = await response.json();
        if (payload.success) {
            if (typeof showToast === 'function') showToast('Notificación enviada correctamente.', 'success');
            closeModal('notificarRegistroModal');
        } else if (typeof showToast === 'function') {
            showToast(payload.error || 'No se pudo enviar la notificación.', 'error');
        }
    } catch (error) {
        if (typeof showToast === 'function') showToast('Error al enviar la notificación.', 'error');
    }
}

async function cargarComentariosRegistro(modulo, id) {
    const comentariosBox = document.getElementById('registroDetalleComentarios');
    const comentarioForm = document.getElementById('registroDetalleComentarioForm');

    try {
        const response = await fetch(`/comentarios/${modulo}/${id}/`, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
        const payload = await response.json();

        if (!payload.success) {
            comentariosBox.innerHTML = `<p style="color:#7f8c8d;">${payload.error || 'No hay observaciones disponibles.'}</p>`;
            return;
        }

        if (!payload.comentarios.length) {
            comentariosBox.innerHTML = '<p style="color:#7f8c8d;">Sin observaciones registradas.</p>';
        } else {
            comentariosBox.innerHTML = payload.comentarios
                .map((c) => `
                    <div class="comentario-item">
                        <div class="comentario-meta"><strong>${c.usuario_prodesal}</strong> (PRODESAL) &middot; ${c.fecha}</div>
                        <div>${c.comentario}</div>
                    </div>
                `)
                .join('');
        }

        if (window.ZAINO_CTX && window.ZAINO_CTX.canComment) {
            comentarioForm.style.display = 'block';
        }
    } catch (error) {
        comentariosBox.innerHTML = '<p style="color:#7f8c8d;">Error al cargar observaciones.</p>';
    }
}

async function enviarComentarioRegistro() {
    if (!currentDetalleModulo || !currentDetalleId) return;

    const texto = document.getElementById('registroDetalleComentarioTexto');
    const comentario = (texto.value || '').trim();
    if (!comentario) {
        if (typeof showToast === 'function') showToast('Escribe una observación antes de enviarla.', 'warning');
        return;
    }

    try {
        const formData = new FormData();
        formData.append('comentario', comentario);

        const response = await fetch(`/comentarios/${currentDetalleModulo}/${currentDetalleId}/crear/`, {
            method: 'POST',
            headers: { 'X-CSRFToken': getCsrfToken(), 'X-Requested-With': 'XMLHttpRequest' },
            body: formData,
        });
        const payload = await response.json();

        if (payload.success) {
            texto.value = '';
            if (typeof showToast === 'function') showToast('Observación registrada correctamente.', 'success');
            cargarComentariosRegistro(currentDetalleModulo, currentDetalleId);
        } else if (typeof showToast === 'function') {
            showToast(payload.error || 'No se pudo registrar la observación.', 'error');
        }
    } catch (error) {
        if (typeof showToast === 'function') showToast('Error al enviar la observación.', 'error');
    }
}

/* ============================================
   NOTIFICACIONES
   ============================================ */

async function loadNotificaciones() {
    const container = document.getElementById('notifListContainer');
    container.innerHTML = '<p style="text-align:center; color:#7f8c8d;">Cargando...</p>';

    try {
        const response = await fetch('/notificaciones/', { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
        const payload = await response.json();

        if (!payload.success || !payload.notificaciones.length) {
            container.innerHTML = '<p style="text-align:center; color:#7f8c8d;">No tienes notificaciones.</p>';
            updateNotifBadge(0);
            return;
        }

        container.innerHTML = payload.notificaciones
            .map((n) => `
                <div class="notif-panel-item ${n.leido ? '' : 'unread'}" onclick="marcarNotificacionLeida(${n.id}, this)">
                    <div class="notif-meta"><strong>Remitente:</strong> ${n.usuario_generador} (${n.usuario_generador_rol})</div>
                    <div class="notif-title">${n.titulo}</div>
                    <div>${n.mensaje}</div>
                    ${n.modulo_label ? `<div class="notif-meta"><strong>Registro relacionado:</strong> ${n.modulo_label} #${n.objeto_id}</div>` : ''}
                    <div class="notif-meta"><strong>Fecha:</strong> ${n.fecha} &middot; <strong>Hora:</strong> ${n.hora}</div>
                    <div class="notif-meta">${n.leido ? '<span class="badge badge-success">Leída</span>' : '<span class="badge badge-warning">No leída</span>'}</div>
                </div>
            `)
            .join('');

        updateNotifBadge(payload.no_leidas || 0);
    } catch (error) {
        container.innerHTML = '<p style="text-align:center; color:#7f8c8d;">Error al cargar notificaciones.</p>';
    }
}

function updateNotifBadge(count) {
    const badge = document.getElementById('notifBadge');
    if (!badge) return;
    if (count > 0) {
        badge.textContent = count;
        badge.style.display = 'flex';
    } else {
        badge.style.display = 'none';
    }
}

async function marcarNotificacionLeida(id, element) {
    if (element && !element.classList.contains('unread')) return;

    try {
        const response = await fetch(`/notificaciones/${id}/marcar-leida/`, {
            method: 'POST',
            headers: { 'X-CSRFToken': getCsrfToken(), 'X-Requested-With': 'XMLHttpRequest' },
        });
        const payload = await response.json();
        if (payload.success && element) {
            element.classList.remove('unread');
            const current = document.querySelectorAll('.notif-panel-item.unread').length;
            updateNotifBadge(current);
        }
    } catch (error) {
        /* silencioso */
    }
}

document.addEventListener('DOMContentLoaded', function () {
    const notifButton = document.getElementById('notifBellButton');
    if (notifButton) {
        notifButton.addEventListener('click', function () {
            openModal('notifModal');
            loadNotificaciones();
        });
    }
});
