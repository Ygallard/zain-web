// Templates de los dashboards
const templates = {
    inicio: `
        <div id="dashboard-inicio" class="dashboard active-dashboard">
            <div id="loading-overlay" class="loading-overlay">
                <div class="loading-content">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Cargando...</span>
                    </div>
                    <p class="mt-3">Cargando datos por favor espere...</p>
                </div>
            </div>
            <div class="top-dashboard">
                <div class="card" id="flujometro">
                    <h3>Flujometro</h3>
                    <div class="card-content"></div>
                </div>
                <div class="card" id="tiempo">
                    <h3>Tiempo Actual</h3>
                    <div class="card-content"></div>
                </div>
                <div class="card" id="visitas">
                    <h3>Visitas Totales</h3>
                    <div class="card-content"></div>
                </div>
            </div>
            <div class="bottom-dashboard">
                <div class="card" id="realtime-flow">
                    <h3>Flujo en Tiempo Real</h3>
                    <div class="card-content"></div>
                </div>
            </div>
        </div>
    `,
    informes: `
        <div id="dashboard-informes" class="dashboard active-dashboard">
            <h2 class="dashboard-title">Lista de Informes</h2>
            <div class="card">
                <div class="table-responsive">
                    <table class="table table-hover">
                        <thead>
                            <tr>
                                <th>Nombre del Informe</th>
                                <th>Fecha</th>
                                <th>Opciones</th>
                            </tr>
                        </thead>
                        <tbody id="informes-list">
                            <!-- Se llenará dinámicamente -->
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `,
    cuaderno: `
        <div id="dashboard-cuaderno" class="dashboard active-dashboard">
            <div class="card cuaderno-card">
                <div class="d-flex justify-content-between align-items-center flex-wrap gap-2 mb-3">
                    <h2 class="dashboard-title mb-0">Cuaderno de Campo Digital</h2>
                    <a href="http://127.0.0.1:8000/dashboard/" target="_blank" rel="noopener" class="btn btn-sm btn-outline-primary">
                        <i class="bi bi-box-arrow-up-right"></i> Abrir en nueva pestaña
                    </a>
                </div>
                <div class="cuaderno-embed-wrap">
                    <iframe
                        class="cuaderno-iframe"
                        src="http://127.0.0.1:8000/dashboard/"
                        title="Cuaderno de Campo"
                        loading="lazy"
                    ></iframe>
                </div>
            </div>
        </div>
    `
};

// Estado de la aplicación
const appState = {
    currentView: 'inicio',
    authenticated: false,
    username: null,
    loadingStates: {
        weather: false,
        visits: false,
        flow: false
    },
    realtimeInterval: null,  // Para almacenar el intervalo de actualización
    flowHistory: [],  // Para almacenar el historial de datos
    lastFlowData: null,  // Cache del último dato recibido
    requestInProgress: false  // Flag para evitar peticiones simultáneas
};

function renderAuthRequiredView() {
    return `
        <div class="dashboard active-dashboard">
            <div class="card" style="max-width: 520px; margin: 2rem auto; text-align: center;">
                <h3><i class="bi bi-shield-lock-fill"></i> Acceso requerido</h3>
                <div class="card-content">
                    <p style="color: #6c757d; margin-bottom: 1rem;">Inicia sesión para ver el dashboard.</p>
                    <button id="btn-open-login-content" class="btn btn-primary">
                        <i class="bi bi-box-arrow-in-right"></i> Iniciar sesión
                    </button>
                </div>
            </div>
        </div>
    `;
}

function updateAuthUI() {
    const userLabel = document.querySelector('#auth-user-label span');
    const btnOpenLogin = document.getElementById('btn-open-login');
    const btnLogout = document.getElementById('btn-logout');

    if (!userLabel || !btnOpenLogin || !btnLogout) {
        return;
    }

    if (appState.authenticated) {
        userLabel.textContent = `Usuario: ${appState.username || 'admin'}`;
        btnOpenLogin.style.display = 'none';
        btnLogout.style.display = 'block';
    } else {
        userLabel.textContent = 'Sin sesión';
        btnOpenLogin.style.display = 'block';
        btnLogout.style.display = 'none';
    }
}

async function refreshAuthStatus() {
    try {
        const response = await fetch('/api/auth/status');
        const data = await response.json();

        appState.authenticated = !!data.authenticated;
        appState.username = data.username || null;
    } catch (error) {
        appState.authenticated = false;
        appState.username = null;
        console.error('No se pudo validar la sesión:', error);
    }

    updateAuthUI();
}

function showLoginModal() {
    const modalElement = document.getElementById('loginModal');
    if (!modalElement) return;

    const loginError = document.getElementById('login-error');
    if (loginError) {
        loginError.style.display = 'none';
        loginError.textContent = '';
    }

    const passwordInput = document.getElementById('login-password');
    const toggleBtn = document.getElementById('toggle-login-password');
    const showPassCheck = document.getElementById('login-show-password');
    if (passwordInput) {
        passwordInput.type = 'password';
    }
    if (showPassCheck) {
        showPassCheck.checked = false;
    }
    if (toggleBtn) {
        toggleBtn.setAttribute('aria-pressed', 'false');
        toggleBtn.setAttribute('aria-label', 'Mostrar contraseña');
        toggleBtn.innerHTML = '<i class="bi bi-eye"></i>';
    }

    const modal = new bootstrap.Modal(modalElement);
    modal.show();
}

async function handleLogin(event) {
    event.preventDefault();

    const usernameInput = document.getElementById('login-username');
    const passwordInput = document.getElementById('login-password');
    const loginError = document.getElementById('login-error');

    const username = usernameInput?.value?.trim() || '';
    const password = passwordInput?.value || '';

    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(data.error || 'No se pudo iniciar sesión');
        }

        appState.authenticated = true;
        appState.username = data.username;
        updateAuthUI();

        const loginModal = bootstrap.Modal.getInstance(document.getElementById('loginModal'));
        if (loginModal) loginModal.hide();

        $('#inicio').addClass('options-active');
        $('#informes').removeClass('options-active');
        loadView('inicio');
    } catch (error) {
        if (loginError) {
            loginError.textContent = error.message;
            loginError.style.display = 'block';
        }
    }
}

async function handleLogout() {
    try {
        await fetch('/api/auth/logout', { method: 'POST' });
    } catch (error) {
        console.error('Error al cerrar sesión:', error);
    }

    appState.authenticated = false;
    appState.username = null;
    updateAuthUI();
    stopRealtimeFlowMonitor();

    const contentDiv = document.getElementById('dynamic-content');
    if (contentDiv) {
        contentDiv.innerHTML = renderAuthRequiredView();
        bindAuthActions();
    }
}

function toggleLoginPasswordVisibility() {
    const passwordInput = document.getElementById('login-password');
    const toggleBtn = document.getElementById('toggle-login-password');
    const showPassCheck = document.getElementById('login-show-password');

    if (!passwordInput || !toggleBtn) {
        return;
    }

    const shouldShow = passwordInput.type === 'password';
    passwordInput.type = shouldShow ? 'text' : 'password';
    if (showPassCheck) {
        showPassCheck.checked = shouldShow;
    }
    toggleBtn.setAttribute('aria-pressed', shouldShow ? 'true' : 'false');
    toggleBtn.setAttribute('aria-label', shouldShow ? 'Ocultar contraseña' : 'Mostrar contraseña');
    toggleBtn.innerHTML = shouldShow
        ? '<i class="bi bi-eye-slash"></i>'
        : '<i class="bi bi-eye"></i>';
}

function toggleLoginPasswordFromCheckbox() {
    const passwordInput = document.getElementById('login-password');
    const toggleBtn = document.getElementById('toggle-login-password');
    const showPassCheck = document.getElementById('login-show-password');

    if (!passwordInput || !toggleBtn || !showPassCheck) {
        return;
    }

    const shouldShow = showPassCheck.checked;
    passwordInput.type = shouldShow ? 'text' : 'password';
    toggleBtn.setAttribute('aria-pressed', shouldShow ? 'true' : 'false');
    toggleBtn.setAttribute('aria-label', shouldShow ? 'Ocultar contraseña' : 'Mostrar contraseña');
    toggleBtn.innerHTML = shouldShow
        ? '<i class="bi bi-eye-slash"></i>'
        : '<i class="bi bi-eye"></i>';
}

function bindAuthActions() {
    $('#btn-open-login').off('click').on('click', showLoginModal);
    $('#btn-open-login-content').off('click').on('click', showLoginModal);
    $('#btn-logout').off('click').on('click', handleLogout);
    $('#login-form').off('submit').on('submit', handleLogin);
    $('#toggle-login-password').off('click').on('click', toggleLoginPasswordVisibility);
    $('#login-show-password').off('change').on('change', toggleLoginPasswordFromCheckbox);
}

// Función para verificar si todos los datos están cargados
function checkAllLoaded() {
    if (appState.loadingStates.weather && 
        appState.loadingStates.visits && 
        appState.loadingStates.flow) {
        $('#loading-overlay').fadeOut();
    }
}

// Función para cargar una vista
async function loadView(viewName) {
    try {
        const contentDiv = document.getElementById('dynamic-content');
        const mainOverlay = document.getElementById('main-loading-overlay');

        if (!appState.authenticated) {
            contentDiv.innerHTML = renderAuthRequiredView();
            bindAuthActions();
            return;
        }
        
        // Detener el monitoreo en tiempo real si estamos saliendo de la vista de inicio
        if (appState.currentView === 'inicio' && viewName !== 'inicio') {
            stopRealtimeFlowMonitor();
        }
        
        // Mostrar overlay principal si existe
        if (mainOverlay) {
            mainOverlay.classList.add('active');
        }
        
        // Simular tiempo de carga (puedes eliminar este setTimeout en producción)
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // Cargar el template
        contentDiv.innerHTML = templates[viewName];
        appState.currentView = viewName;
        
        // Configurar eventos para los botones del template cargado
        if (viewName === 'inicio') {
            // Inicializar la vista
            await initializeHomeView();
        } else if (viewName === 'informes') {
            await initializeReportsView();
        } else if (viewName === 'cuaderno') {
            // Vista embebida, no requiere inicialización adicional
        }
    } catch (error) {
        console.error("Error al cargar la vista:", error);
    } finally {
        // Remover el overlay principal completamente después de la carga inicial
        const mainOverlay = document.getElementById('main-loading-overlay');
        if (mainOverlay) {
            // Primero ocultamos con la animación
            mainOverlay.classList.remove('active');
            // Después de la transición, removemos el elemento
            setTimeout(() => {
                mainOverlay.remove();
            }, 300); // 300ms es el tiempo de la transición definida en CSS
        }
    }
}

// Inicializar vista de inicio
async function initializeHomeView() {
    try {
        appState.loadingStates = { weather: false, visits: false, flow: false };
        $('#loading-overlay').show();
        
        // Iniciar todas las cargas en paralelo
        const loadingPromises = [
            // Cargar visitas
            fetch("/api/visitas", { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    $("#visitas .card-content").html(
                        `<div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; padding: 20px;">
                            <div style="font-size: 5em; font-weight: 700; color: #2c3e50; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
                                ${data.num_visitas}
                            </div>
                        </div>`
                    );
                })
                .catch(error => {
                    console.error("Error al actualizar visitas:", error);
                    $("#visitas .card-content").html(
                        '<p class="text-danger">Error al cargar datos</p>'
                    );
                })
                .finally(() => {
                    appState.loadingStates.visits = true;
                    checkAllLoaded();
                }),

            // Cargar datos del tiempo
            loadWeatherData()
        ];

        // Simulación de carga del flujómetro (reemplaza con logica real)
        loadingPromises.push(
            loadFlowmeterData()
        );

        // Esperar a que todas las cargas terminen
        await Promise.all(loadingPromises);
        
        // Iniciar el medidor en tiempo real después de cargar los datos iniciales
        startRealtimeFlowMonitor();
        
    } catch (error) {
        console.error("Error al inicializar la vista de inicio:", error);
        // Mostrar algún mensaje de error al usuario si es necesario
    }
}

// Inicializar vista de informes
async function initializeReportsView() {
    const informesList = document.getElementById('informes-list');
    
    try {
        // Cargar informes desde la API
        const response = await fetch('/api/informes');
        const data = await response.json();
        
        const informes = data.success ? data.informes : [];
        
        // Detectar si es móvil
        const isMobile = window.innerWidth <= 768;
        
        if (isMobile) {
            // Vista de cards para móvil
            if (informes.length === 0) {
                informesList.parentElement.parentElement.innerHTML = `
                    <div class="text-center p-4">
                        <i class="bi bi-inbox" style="font-size: 3rem; color: #ccc;"></i>
                        <p class="text-muted mt-3">No hay informes disponibles</p>
                        <button class="btn btn-primary" onclick="showGenerateReportModal()">
                            <i class="bi bi-plus-circle"></i> Generar Informe
                        </button>
                    </div>
                `;
            } else {
                const informesHTML = informes.map((informe, index) => `
                    <div class="informe-card" data-id="${informe.id}">
                        <div class="informe-header">
                            <div class="informe-icon">
                                <i class="bi bi-file-earmark-text-fill"></i>
                            </div>
                            <div class="informe-info">
                                <h4>${informe.nombre}</h4>
                                <p><i class="bi bi-calendar3"></i> ${informe.fecha}</p>
                                <small class="text-muted">${informe.periodo}</small>
                            </div>
                        </div>
                        <div class="informe-actions">
                            <button class="btn btn-sm btn-danger btn-block mb-2" onclick="exportReportToPDFDirect('${informe.id}')">
                                <i class="bi bi-file-pdf"></i> Exportar PDF
                            </button>
                            <button class="btn btn-sm btn-primary btn-block" onclick="downloadReport('${informe.id}')">
                                <i class="bi bi-download"></i> JSON
                            </button>
                            <button class="btn btn-sm btn-secondary btn-block" onclick="viewReport('${informe.id}')">
                                <i class="bi bi-eye"></i> Ver
                            </button>
                        </div>
                    </div>
                `).join('');
                
                // Cambiar el contenedor a vista de cards
                informesList.parentElement.parentElement.classList.remove('table-responsive');
                informesList.parentElement.parentElement.classList.add('informes-grid');
                informesList.parentElement.parentElement.innerHTML = `
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <h5 class="mb-0">${informes.length} informe(s)</h5>
                        <button class="btn btn-sm btn-success" onclick="showGenerateReportModal()">
                            <i class="bi bi-plus-circle"></i> Generar
                        </button>
                    </div>
                    ${informesHTML}
                `;
            }
        } else {
            // Vista de tabla para desktop
            if (informes.length === 0) {
                informesList.innerHTML = `
                    <tr>
                        <td colspan="3" class="text-center p-4">
                            <i class="bi bi-inbox" style="font-size: 3rem; color: #ccc;"></i>
                            <p class="text-muted mt-3">No hay informes disponibles</p>
                            <button class="btn btn-primary" onclick="showGenerateReportModal()">
                                <i class="bi bi-plus-circle"></i> Generar Informe
                            </button>
                        </td>
                    </tr>
                `;
            } else {
                const informesHTML = informes.map(informe => `
                    <tr data-id="${informe.id}">
                        <td>
                            ${informe.nombre}
                            <br><small class="text-muted">${informe.periodo}</small>
                        </td>
                        <td>${informe.fecha}</td>
                        <td class="text-end">
                            <button class="btn btn-sm btn-danger me-2" onclick="exportReportToPDFDirect('${informe.id}')">
                                <i class="bi bi-file-pdf"></i> PDF
                            </button>
                            <button class="btn btn-sm btn-primary me-2" onclick="downloadReport('${informe.id}')">
                                <i class="bi bi-download"></i> JSON
                            </button>
                            <button class="btn btn-sm btn-secondary" onclick="viewReport('${informe.id}')">
                                <i class="bi bi-eye"></i> Ver
                            </button>
                        </td>
                    </tr>
                `).join('');
                
                // Agregar botón de generar en el header
                const dashboardTitle = document.querySelector('#dashboard-informes .dashboard-title');
                if (dashboardTitle && !document.getElementById('btn-generar-informe')) {
                    dashboardTitle.insertAdjacentHTML('afterend', `
                        <div class="d-flex justify-content-end mb-3">
                            <button id="btn-generar-informe" class="btn btn-success" onclick="showGenerateReportModal()">
                                <i class="bi bi-plus-circle"></i> Generar Nuevo Informe
                            </button>
                        </div>
                    `);
                }
                
                informesList.innerHTML = informesHTML;
            }
        }
    } catch (error) {
        console.error('Error al cargar informes:', error);
        informesList.innerHTML = `
            <tr>
                <td colspan="3" class="text-center text-danger p-4">
                    <i class="bi bi-exclamation-triangle" style="font-size: 3rem;"></i>
                    <p class="mt-3">Error al cargar informes</p>
                </td>
            </tr>
        `;
    }
}

// Función para mostrar el modal de generación de informes
function showGenerateReportModal() {
    // Crear el modal si no existe
    if (!document.getElementById('generateReportModal')) {
        const modalHTML = `
            <div class="modal fade" id="generateReportModal" tabindex="-1" data-bs-backdrop="static" data-bs-keyboard="false">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Generar Nuevo Informe Mensual</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="alert alert-info">
                                <i class="bi bi-info-circle"></i> 
                                Se generará un informe del último mes. Solo se permite un informe por mes.
                            </div>
                            <p class="text-muted mb-0">
                                <small>El informe incluirá datos de caudal, estadísticas y análisis del período mensual.</small>
                            </p>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                            <button type="button" id="btnGenerarInforme" class="btn btn-primary" onclick="generateReport()">
                                <i class="bi bi-gear-fill"></i> Generar Informe
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHTML);
    }
    
    // Resetear el botón por si acaso
    const btnGenerar = document.getElementById('btnGenerarInforme');
    if (btnGenerar) {
        btnGenerar.innerHTML = '<i class="bi bi-gear-fill"></i> Generar Informe';
        btnGenerar.disabled = false;
    }
    
    // Mostrar el modal
    const modal = new bootstrap.Modal(document.getElementById('generateReportModal'));
    modal.show();
}

// Función para generar un informe
async function generateReport() {
    const modal = bootstrap.Modal.getInstance(document.getElementById('generateReportModal'));
    const btn = document.getElementById('btnGenerarInforme');
    const btnClose = document.querySelector('#generateReportModal .btn-close');
    const btnCancel = document.querySelector('#generateReportModal .btn-secondary');
    
    try {
        // Mostrar indicador de carga
        const originalHTML = btn.innerHTML;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Generando informe, por favor espere...';
        btn.disabled = true;
        btnClose.disabled = true;
        btnCancel.disabled = true;
        
        // Mostrar toast de inicio
        showToast('Generando informe mensual...', 'info');
        
        const response = await fetch('/api/informes/generar', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ periodo: 'ultimo_mes' })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Cerrar modal
            modal.hide();
            
            // Mostrar mensaje de éxito con animación
            showToast('✅ ¡Informe generado exitosamente!', 'success');
            
            // Esperar un momento para que se cierre el modal
            await new Promise(resolve => setTimeout(resolve, 300));
            
            // Recargar la lista de informes para mostrar el nuevo
            await initializeReportsView();
            
            // Mensaje adicional
            showToast(`📊 ${data.informe.nombre} está disponible`, 'info');
        } else {
            // Error de validación (ya existe un informe del mes)
            btn.innerHTML = originalHTML;
            btn.disabled = false;
            btnClose.disabled = false;
            btnCancel.disabled = false;
            
            // Mostrar mensaje de error detallado
            const errorMsg = data.error || 'Error al generar informe';
            
            if (data.dias_restantes) {
                // Mostrar modal con información del informe existente
                modal.hide();
                showErrorModal(
                    '⚠️ Informe ya disponible',
                    errorMsg,
                    data.informe_existente
                );
            } else {
                showToast(errorMsg, 'error');
            }
        }
    } catch (error) {
        console.error('Error al generar informe:', error);
        
        // Restaurar botón
        btn.innerHTML = '<i class="bi bi-gear-fill"></i> Generar Informe';
        btn.disabled = false;
        btnClose.disabled = false;
        btnCancel.disabled = false;
        
        showToast('❌ Error al conectar con el servidor', 'error');
    }
}

// Función para descargar un informe
async function downloadReport(informeId) {
    try {
        // Mostrar toast de inicio
        showToast('📥 Descargando informe...', 'info');
        
        const response = await fetch(`/api/informes/${informeId}`);
        const data = await response.json();
        
        if (data.success) {
            // Crear un blob con los datos del informe
            const blob = new Blob([JSON.stringify(data.informe, null, 2)], { type: 'application/json' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${informeId}.json`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            showToast('✅ Informe descargado exitosamente', 'success');
        } else {
            showToast('❌ Error al descargar informe', 'error');
        }
    } catch (error) {
        console.error('Error al descargar informe:', error);
        showToast('❌ Error al conectar con el servidor', 'error');
    }
}

// Función para ver un informe
async function viewReport(informeId) {
    try {
        // Mostrar toast de carga
        showToast('📄 Cargando informe...', 'info');
        
        const response = await fetch(`/api/informes/${informeId}`);
        const data = await response.json();
        
        if (data.success) {
            // Crear modal para mostrar el informe
            if (!document.getElementById('viewReportModal')) {
                const modalHTML = `
                    <div class="modal fade" id="viewReportModal" tabindex="-1">
                        <div class="modal-dialog modal-lg">
                            <div class="modal-content">
                                <div class="modal-header bg-primary text-white">
                                    <h5 class="modal-title" id="viewReportTitle">
                                        <i class="bi bi-file-earmark-text"></i>
                                        <span id="viewReportTitleText"></span>
                                    </h5>
                                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                                </div>
                                <div class="modal-body" id="viewReportBody" style="max-height: 70vh; overflow-y: auto;">
                                </div>
                                <div class="modal-footer">
                                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                                        <i class="bi bi-x-circle"></i> Cerrar
                                    </button>
                                    <button type="button" class="btn btn-danger" id="btnExportarPDF">
                                        <i class="bi bi-file-pdf"></i> Exportar a PDF
                                    </button>
                                    <button type="button" class="btn btn-success" id="btnDescargarInforme">
                                        <i class="bi bi-download"></i> Descargar JSON
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                document.body.insertAdjacentHTML('beforeend', modalHTML);
            }
            
            const informe = data.informe;
            const modalTitle = document.getElementById('viewReportTitleText');
            const modalBody = document.getElementById('viewReportBody');
            
            modalTitle.textContent = informe.nombre;
            modalBody.innerHTML = `
                <div class="row mb-4">
                    <div class="col-md-6 mb-3">
                        <div class="card border-primary">
                            <div class="card-body">
                                <h6 class="card-title text-primary">
                                    <i class="bi bi-calendar-check"></i> Fecha de Generación
                                </h6>
                                <p class="card-text fs-5 mb-0">${informe.fecha_generacion}</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6 mb-3">
                        <div class="card border-info">
                            <div class="card-body">
                                <h6 class="card-title text-info">
                                    <i class="bi bi-calendar-range"></i> Período
                                </h6>
                                <p class="card-text fs-5 mb-0">${informe.periodo}</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6 mb-3">
                        <div class="card border-success">
                            <div class="card-body">
                                <h6 class="card-title text-success">
                                    <i class="bi bi-calendar3"></i> Fecha Inicio
                                </h6>
                                <p class="card-text fs-5 mb-0">${informe.fecha_inicio}</p>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6 mb-3">
                        <div class="card border-danger">
                            <div class="card-body">
                                <h6 class="card-title text-danger">
                                    <i class="bi bi-calendar3"></i> Fecha Fin
                                </h6>
                                <p class="card-text fs-5 mb-0">${informe.fecha_fin}</p>
                            </div>
                        </div>
                    </div>
                </div>
                <hr>
                <h5 class="mb-3">
                    <i class="bi bi-droplet-fill text-primary"></i> Datos del Flujómetro
                </h5>
                <div class="row mt-3">
                    <div class="col-md-4 mb-3">
                        <div class="card bg-light border-0 shadow-sm">
                            <div class="card-body text-center">
                                <div class="mb-2">
                                    <i class="bi bi-speedometer2" style="font-size: 2rem; color: #17a2b8;"></i>
                                </div>
                                <h6 class="card-title text-muted">Flujo Instantáneo</h6>
                                <h3 class="text-primary mb-0">${informe.datos.flujo_instantaneo.toFixed(2)}</h3>
                                <small class="text-muted">L/min</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4 mb-3">
                        <div class="card bg-light border-0 shadow-sm">
                            <div class="card-body text-center">
                                <div class="mb-2">
                                    <i class="bi bi-droplet-fill" style="font-size: 2rem; color: #28a745;"></i>
                                </div>
                                <h6 class="card-title text-muted">Flujo Acumulado</h6>
                                <h3 class="text-success mb-0">${informe.datos.flujo_acumulado.toFixed(2)}</h3>
                                <small class="text-muted">Litros</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4 mb-3">
                        <div class="card bg-light border-0 shadow-sm">
                            <div class="card-body text-center">
                                <div class="mb-2">
                                    <i class="bi bi-graph-up-arrow" style="font-size: 2rem; color: #ffc107;"></i>
                                </div>
                                <h6 class="card-title text-muted">Promedio Diario</h6>
                                <h3 class="text-warning mb-0">${informe.datos.promedio_diario.toFixed(2)}</h3>
                                <small class="text-muted">Litros/día</small>
                            </div>
                        </div>
                    </div>
                </div>
                <hr>
                <h5 class="mb-3">
                    <i class="bi bi-bar-chart-fill text-success"></i> Estadísticas
                </h5>
                <div class="row mt-3">
                    <div class="col-md-6 mb-3">
                        <div class="card bg-light border-0 shadow-sm">
                            <div class="card-body">
                                <div class="d-flex align-items-center">
                                    <div class="flex-shrink-0">
                                        <i class="bi bi-bucket-fill" style="font-size: 2.5rem; color: #007bff;"></i>
                                    </div>
                                    <div class="flex-grow-1 ms-3">
                                        <h6 class="card-title text-muted mb-1">Total de Litros</h6>
                                        <h4 class="text-primary mb-0">${informe.estadisticas.total_litros.toFixed(2)} L</h4>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6 mb-3">
                        <div class="card bg-light border-0 shadow-sm">
                            <div class="card-body">
                                <div class="d-flex align-items-center">
                                    <div class="flex-shrink-0">
                                        <i class="bi bi-clock-history" style="font-size: 2.5rem; color: #28a745;"></i>
                                    </div>
                                    <div class="flex-grow-1 ms-3">
                                        <h6 class="card-title text-muted mb-1">Promedio L/min</h6>
                                        <h4 class="text-success mb-0">${informe.estadisticas.promedio_lmin.toFixed(2)} L/min</h4>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // Actualizar el botón de descarga con el ID correcto
            const btnDescargar = document.getElementById('btnDescargarInforme');
            btnDescargar.onclick = function() {
                downloadReport(informeId);
            };
            
            // Actualizar el botón de exportar a PDF
            const btnExportarPDF = document.getElementById('btnExportarPDF');
            btnExportarPDF.onclick = function() {
                exportReportToPDF(informeId, informe);
            };
            
            // Mostrar el modal
            const modal = new bootstrap.Modal(document.getElementById('viewReportModal'));
            modal.show();
        } else {
            showToast('❌ Error al cargar informe', 'error');
        }
    } catch (error) {
        console.error('Error al ver informe:', error);
        showToast('❌ Error al conectar con el servidor', 'error');
    }
}

// Función para exportar un informe a PDF
async function exportReportToPDF(informeId, informeData) {
    try {
        const btn = document.getElementById('btnExportarPDF');
        const originalHTML = btn.innerHTML;
        
        // Mostrar indicador de carga
        btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Generando PDF...';
        btn.disabled = true;
        
        showToast('📄 Generando PDF, por favor espere...', 'info');
        
        // Obtener el contenido del modal
        const modalBody = document.getElementById('viewReportBody');
        const modalTitle = document.getElementById('viewReportTitleText').textContent;
        
        // Crear un contenedor temporal con el contenido formateado para PDF
        const tempContainer = document.createElement('div');
        tempContainer.style.position = 'absolute';
        tempContainer.style.left = '-9999px';
        tempContainer.style.width = '210mm'; // Ancho A4
        tempContainer.style.padding = '20mm';
        tempContainer.style.backgroundColor = 'white';
        tempContainer.style.fontFamily = 'Arial, sans-serif';
        
        // Clonar el contenido y agregar header
        tempContainer.innerHTML = `
            <div style="text-align: center; margin-bottom: 30px; border-bottom: 3px solid #007bff; padding-bottom: 20px;">
                <h1 style="color: #007bff; margin-bottom: 10px; font-size: 28px;">
                    <i class="bi bi-droplet-fill"></i> ZAINO WEB
                </h1>
                <h2 style="color: #333; font-size: 22px; margin-bottom: 5px;">${modalTitle}</h2>
                <p style="color: #666; font-size: 12px;">Generado el ${new Date().toLocaleDateString('es-ES', { 
                    day: '2-digit', 
                    month: '2-digit', 
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                })}</p>
            </div>
            ${modalBody.innerHTML}
            <div style="margin-top: 40px; padding-top: 20px; border-top: 2px solid #e9ecef; text-align: center; font-size: 11px; color: #6c757d;">
                <p style="margin: 5px 0;">Zaino Web - Sistema de Monitoreo de Caudal</p>
                <p style="margin: 5px 0;">Instituto Profesional AIEP</p>
                <p style="margin: 5px 0;">© ${new Date().getFullYear()} - Documento generado automáticamente</p>
            </div>
        `;
        
        document.body.appendChild(tempContainer);
        
        // Configurar html2canvas
        const canvas = await html2canvas(tempContainer, {
            scale: 2, // Mayor calidad
            useCORS: true,
            logging: false,
            backgroundColor: '#ffffff'
        });
        
        // Eliminar el contenedor temporal
        document.body.removeChild(tempContainer);
        
        // Crear PDF con jsPDF
        const { jsPDF } = window.jspdf;
        const imgData = canvas.toDataURL('image/png');
        
        // Calcular dimensiones
        const imgWidth = 210; // A4 width in mm
        const pageHeight = 297; // A4 height in mm
        const imgHeight = (canvas.height * imgWidth) / canvas.width;
        
        const pdf = new jsPDF('p', 'mm', 'a4');
        let heightLeft = imgHeight;
        let position = 0;
        
        // Agregar la primera página
        pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
        heightLeft -= pageHeight;
        
        // Si el contenido es más largo que una página, agregar páginas adicionales
        while (heightLeft > 0) {
            position = heightLeft - imgHeight;
            pdf.addPage();
            pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
            heightLeft -= pageHeight;
        }
        
        // Guardar el PDF
        const filename = `${informeId}.pdf`;
        pdf.save(filename);
        
        // Restaurar botón
        btn.innerHTML = originalHTML;
        btn.disabled = false;
        
        showToast('✅ PDF exportado exitosamente', 'success');
        
    } catch (error) {
        console.error('Error al exportar PDF:', error);
        
        // Restaurar botón
        const btn = document.getElementById('btnExportarPDF');
        if (btn) {
            btn.innerHTML = '<i class="bi bi-file-pdf"></i> Exportar a PDF';
            btn.disabled = false;
        }
        
        showToast('❌ Error al generar PDF. Intente nuevamente.', 'error');
    }
}

// Función para exportar directamente a PDF sin abrir el modal
async function exportReportToPDFDirect(informeId) {
    try {
        showToast('📄 Cargando informe para exportar...', 'info');
        
        // Obtener los datos del informe
        const response = await fetch(`/api/informes/${informeId}`);
        const data = await response.json();
        
        if (data.success) {
            const informe = data.informe;
            
            showToast('📄 Generando PDF, por favor espere...', 'info');
            
            // Crear contenedor temporal con el mismo formato que el modal
            const tempContainer = document.createElement('div');
            tempContainer.style.position = 'absolute';
            tempContainer.style.left = '-9999px';
            tempContainer.style.width = '210mm';
            tempContainer.style.padding = '20mm';
            tempContainer.style.backgroundColor = 'white';
            tempContainer.style.fontFamily = 'Arial, sans-serif';
            
            tempContainer.innerHTML = `
                <div style="text-align: center; margin-bottom: 30px; border-bottom: 3px solid #007bff; padding-bottom: 20px;">
                    <h1 style="color: #007bff; margin-bottom: 10px; font-size: 28px;">
                        💧 ZAINO WEB
                    </h1>
                    <h2 style="color: #333; font-size: 22px; margin-bottom: 5px;">${informe.nombre}</h2>
                    <p style="color: #666; font-size: 12px;">Generado el ${new Date().toLocaleDateString('es-ES', { 
                        day: '2-digit', 
                        month: '2-digit', 
                        year: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                    })}</p>
                </div>
                
                <div style="margin-bottom: 30px;">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                        <div style="border: 2px solid #007bff; border-radius: 8px; padding: 15px; background: #f8f9fa;">
                            <h6 style="color: #007bff; font-size: 14px; margin-bottom: 8px;">📅 Fecha de Generación</h6>
                            <p style="font-size: 16px; margin: 0;">${informe.fecha_generacion}</p>
                        </div>
                        <div style="border: 2px solid #17a2b8; border-radius: 8px; padding: 15px; background: #f8f9fa;">
                            <h6 style="color: #17a2b8; font-size: 14px; margin-bottom: 8px;">📊 Período</h6>
                            <p style="font-size: 16px; margin: 0;">${informe.periodo}</p>
                        </div>
                        <div style="border: 2px solid #28a745; border-radius: 8px; padding: 15px; background: #f8f9fa;">
                            <h6 style="color: #28a745; font-size: 14px; margin-bottom: 8px;">📅 Fecha Inicio</h6>
                            <p style="font-size: 16px; margin: 0;">${informe.fecha_inicio}</p>
                        </div>
                        <div style="border: 2px solid #dc3545; border-radius: 8px; padding: 15px; background: #f8f9fa;">
                            <h6 style="color: #dc3545; font-size: 14px; margin-bottom: 8px;">📅 Fecha Fin</h6>
                            <p style="font-size: 16px; margin: 0;">${informe.fecha_fin}</p>
                        </div>
                    </div>
                </div>
                
                <hr style="border: 1px solid #dee2e6; margin: 30px 0;">
                
                <h3 style="color: #007bff; font-size: 20px; margin-bottom: 20px;">💧 Datos del Flujómetro</h3>
                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; margin-bottom: 30px;">
                    <div style="background: #e7f3ff; border-radius: 8px; padding: 20px; text-align: center;">
                        <div style="font-size: 40px; margin-bottom: 10px;">🌊</div>
                        <h6 style="color: #666; font-size: 12px; margin-bottom: 8px;">FLUJO INSTANTÁNEO</h6>
                        <h3 style="color: #007bff; font-size: 28px; margin: 5px 0;">${informe.datos.flujo_instantaneo.toFixed(2)}</h3>
                        <small style="color: #666;">L/min</small>
                    </div>
                    <div style="background: #d4edda; border-radius: 8px; padding: 20px; text-align: center;">
                        <div style="font-size: 40px; margin-bottom: 10px;">💧</div>
                        <h6 style="color: #666; font-size: 12px; margin-bottom: 8px;">FLUJO ACUMULADO</h6>
                        <h3 style="color: #28a745; font-size: 28px; margin: 5px 0;">${informe.datos.flujo_acumulado.toFixed(2)}</h3>
                        <small style="color: #666;">Litros</small>
                    </div>
                    <div style="background: #fff3cd; border-radius: 8px; padding: 20px; text-align: center;">
                        <div style="font-size: 40px; margin-bottom: 10px;">📈</div>
                        <h6 style="color: #666; font-size: 12px; margin-bottom: 8px;">PROMEDIO DIARIO</h6>
                        <h3 style="color: #ffc107; font-size: 28px; margin: 5px 0;">${informe.datos.promedio_diario.toFixed(2)}</h3>
                        <small style="color: #666;">Litros/día</small>
                    </div>
                </div>
                
                <hr style="border: 1px solid #dee2e6; margin: 30px 0;">
                
                <h3 style="color: #28a745; font-size: 20px; margin-bottom: 20px;">📊 Estadísticas</h3>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 30px;">
                    <div style="background: #f8f9fa; border-radius: 8px; padding: 20px; display: flex; align-items: center; gap: 15px;">
                        <div style="font-size: 50px;">🪣</div>
                        <div>
                            <h6 style="color: #666; font-size: 12px; margin-bottom: 5px;">TOTAL DE LITROS</h6>
                            <h4 style="color: #007bff; font-size: 24px; margin: 0;">${informe.estadisticas.total_litros.toFixed(2)} L</h4>
                        </div>
                    </div>
                    <div style="background: #f8f9fa; border-radius: 8px; padding: 20px; display: flex; align-items: center; gap: 15px;">
                        <div style="font-size: 50px;">⏱️</div>
                        <div>
                            <h6 style="color: #666; font-size: 12px; margin-bottom: 5px;">PROMEDIO L/MIN</h6>
                            <h4 style="color: #28a745; font-size: 24px; margin: 0;">${informe.estadisticas.promedio_lmin.toFixed(2)} L/min</h4>
                        </div>
                    </div>
                </div>
                
                <div style="margin-top: 40px; padding-top: 20px; border-top: 2px solid #e9ecef; text-align: center; font-size: 11px; color: #6c757d;">
                    <p style="margin: 5px 0;">Zaino Web - Sistema de Monitoreo de Caudal</p>
                    <p style="margin: 5px 0;">Instituto Profesional AIEP</p>
                    <p style="margin: 5px 0;">© ${new Date().getFullYear()} - Documento generado automáticamente</p>
                </div>
            `;
            
            document.body.appendChild(tempContainer);
            
            // Generar canvas
            const canvas = await html2canvas(tempContainer, {
                scale: 2,
                useCORS: true,
                logging: false,
                backgroundColor: '#ffffff'
            });
            
            document.body.removeChild(tempContainer);
            
            // Crear PDF
            const { jsPDF } = window.jspdf;
            const imgData = canvas.toDataURL('image/png');
            
            const imgWidth = 210;
            const pageHeight = 297;
            const imgHeight = (canvas.height * imgWidth) / canvas.width;
            
            const pdf = new jsPDF('p', 'mm', 'a4');
            let heightLeft = imgHeight;
            let position = 0;
            
            pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
            heightLeft -= pageHeight;
            
            while (heightLeft > 0) {
                position = heightLeft - imgHeight;
                pdf.addPage();
                pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight);
                heightLeft -= pageHeight;
            }
            
            const filename = `${informeId}.pdf`;
            pdf.save(filename);
            
            showToast('✅ PDF exportado exitosamente', 'success');
        } else {
            showToast('❌ Error al cargar informe', 'error');
        }
    } catch (error) {
        console.error('Error al exportar PDF:', error);
        showToast('❌ Error al generar PDF. Intente nuevamente.', 'error');
    }
}

// Función para mostrar notificaciones toast
function showToast(message, type = 'info') {
    // Crear contenedor de toasts si no existe
    if (!document.getElementById('toast-container')) {
        const toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '9999';
        document.body.appendChild(toastContainer);
    }
    
    const toastId = 'toast-' + Date.now();
    const bgClass = type === 'success' ? 'bg-success' : type === 'error' ? 'bg-danger' : 'bg-info';
    
    const toastHTML = `
        <div id="${toastId}" class="toast align-items-center text-white ${bgClass} border-0" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;
    
    document.getElementById('toast-container').insertAdjacentHTML('beforeend', toastHTML);
    
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, { delay: 3000 });
    toast.show();
    
    // Eliminar el toast después de que se oculte
    toastElement.addEventListener('hidden.bs.toast', function() {
        toastElement.remove();
    });
}

// Función para mostrar modal de error con información del informe existente
function showErrorModal(title, message, informeExistente) {
    // Crear el modal si no existe
    if (!document.getElementById('errorInformeModal')) {
        const modalHTML = `
            <div class="modal fade" id="errorInformeModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header bg-warning text-dark">
                            <h5 class="modal-title" id="errorInformeTitulo">
                                <i class="bi bi-exclamation-triangle-fill"></i>
                                <span id="errorInformeTituloTexto"></span>
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="alert alert-warning mb-3">
                                <p id="errorInformeMensaje" class="mb-0"></p>
                            </div>
                            <div id="errorInformeDetalles"></div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
                            <button type="button" class="btn btn-primary" id="btnVerInformeExistente">
                                <i class="bi bi-eye"></i> Ver Informe Actual
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHTML);
    }
    
    // Actualizar contenido
    document.getElementById('errorInformeTituloTexto').textContent = title;
    document.getElementById('errorInformeMensaje').textContent = message;
    
    if (informeExistente) {
        document.getElementById('errorInformeDetalles').innerHTML = `
            <h6 class="mb-3">Informe disponible:</h6>
            <div class="card">
                <div class="card-body">
                    <h6 class="card-title">${informeExistente.nombre}</h6>
                    <p class="card-text">
                        <i class="bi bi-calendar3"></i> Generado el: <strong>${informeExistente.fecha}</strong>
                    </p>
                    <p class="text-muted mb-0">
                        <small>Puede ver o descargar este informe en la lista.</small>
                    </p>
                </div>
            </div>
        `;
        
        // Configurar botón para ver el informe
        const btnVer = document.getElementById('btnVerInformeExistente');
        btnVer.onclick = function() {
            bootstrap.Modal.getInstance(document.getElementById('errorInformeModal')).hide();
            viewReport(informeExistente.id);
        };
    } else {
        document.getElementById('errorInformeDetalles').innerHTML = '';
        document.getElementById('btnVerInformeExistente').style.display = 'none';
    }
    
    // Mostrar el modal
    const modal = new bootstrap.Modal(document.getElementById('errorInformeModal'));
    modal.show();
}

// Inicialización cuando el documento está listo
$(document).ready(function() {
    // Activar el ítem inicial del menú
    $("#inicio").addClass("options-active");

    bindAuthActions();

    refreshAuthStatus().then(() => {
        if (appState.authenticated) {
            loadView('inicio');
        } else {
            const contentDiv = document.getElementById('dynamic-content');
            if (contentDiv) {
                contentDiv.innerHTML = renderAuthRequiredView();
            }
            bindAuthActions();

            const mainOverlay = document.getElementById('main-loading-overlay');
            if (mainOverlay) {
                mainOverlay.classList.remove('active');
                setTimeout(() => {
                    mainOverlay.remove();
                }, 300);
            }
        }
    });

    // Manejador de eventos para todos los items del menú
    $(".menu-item").click(function(e) {
        e.preventDefault();

        if (!appState.authenticated) {
            showLoginModal();
            return;
        }
        
        // Si ya está activo, no hacer nada
        if ($(this).hasClass('options-active')) {
            return;
        }

        // Obtener la vista a cargar
        const viewName = $(this).data('view');
        
        // Actualizar clases activas
        $(".options-active").removeClass("options-active");
        $(this).addClass("options-active");
        
        // Cargar la vista
        loadView(viewName);
    });
    
    // Detectar cambio de orientación o tamaño de ventana
    let resizeTimer;
    $(window).on('resize orientationchange', function() {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function() {
            // Si estamos en la vista de informes, recargar para adaptar el layout
            if (appState.currentView === 'informes') {
                initializeReportsView();
            }
        }, 250);
    });
});


async function loadWeatherData() {
    try {
        const response = await fetch('/api/weather');
        const data = await response.json();

        if (data && response.ok) {
            const Tiempo = document.getElementById('tiempo');

            let weatherHtml = '<div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; padding: 20px;">';
            
            // Determinar el estado del tiempo según la presión atmosférica
            if (data.bar) {
                const presion = data.bar;
                if (presion < 1000) {
                    weatherHtml += '<div style="font-size: 4.5em; margin-bottom: 15px;"><i class="bi bi-cloud-rain-fill text-info"></i></div>';
                } else if (presion > 1020) {
                    weatherHtml += '<div style="font-size: 4.5em; margin-bottom: 15px;"><i class="bi bi-sun-fill text-warning"></i></div>';
                } else {
                    weatherHtml += '<div style="font-size: 4.5em; margin-bottom: 15px;"><i class="bi bi-cloud-sun-fill text-primary"></i></div>';
                }
            }

            // Añadir la sensación térmica
            const computed = data.computed;
            const temperature = computed && computed.feel !== null ? computed.feel : '-';
            weatherHtml += `<div style="font-size: 3em; font-weight: 700; color: #2c3e50; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">${temperature}°C</div>`;
            weatherHtml += '</div>';

            $("#tiempo .card-content").html(weatherHtml);
        }
    } catch (error) {
        console.error('Error al cargar los datos meteorológicos:', error);
        $("#tiempo .card-content").html(
            `<div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; padding: 20px;">
                <div style="font-size: 3.5em; color: #dc3545;"><i class="bi bi-exclamation-triangle-fill"></i></div>
                <div style="margin-top: 15px; font-size: 1em; color: #7f8c8d; text-align: center;">Error al cargar<br>datos del clima</div>
            </div>`
        );
    } finally {
        appState.loadingStates.weather = true;
        checkAllLoaded();
    }
}


async function loadFlowmeterData() {
    try {
        const response = await fetch('/api/arduino/flowmeter');
        const result = await response.json();

        if (result.success && result.data) {
            const data = result.data;
            
            // Guardar en caché para uso posterior
            appState.lastFlowData = data;
            
            // CORREGIDO: Los valores estaban al revés
            // constflow = Flujo instantáneo (L/min en tiempo real) 
            // instflow = Flujo acumulado/constante (Total de litros)
            
            const instValue = data.constflow?.value || 0;  // Flujo instantáneo
            const constValue = data.instflow?.value || 0;  // Flujo acumulado
            
            // Crear el HTML con estilo de medidor mejorado
            const flowmeterHtml = `
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; padding: 15px 10px;">
                    <!-- Medidor tipo gauge para flujo instantáneo -->
                    <div style="position: relative; width: 180px; height: 110px; margin-bottom: 10px;">
                        <svg viewBox="0 0 200 120" style="width: 100%; height: 100%;">
                            <!-- Fondo del arco -->
                            <path d="M 20 100 A 80 80 0 0 1 180 100" 
                                  fill="none" 
                                  stroke="#e8f4f8" 
                                  stroke-width="18" 
                                  stroke-linecap="round"/>
                            <!-- Arco de progreso -->
                            <path d="M 20 100 A 80 80 0 0 1 180 100" 
                                  fill="none" 
                                  stroke="url(#gradient)" 
                                  stroke-width="18" 
                                  stroke-linecap="round"
                                  stroke-dasharray="${Math.min((instValue / 100) * 251.2, 251.2)} 251.2"
                                  style="transition: stroke-dasharray 0.5s ease;"/>
                            <!-- Definir gradiente -->
                            <defs>
                                <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                                    <stop offset="0%" style="stop-color:#17a2b8;stop-opacity:1" />
                                    <stop offset="100%" style="stop-color:#20c997;stop-opacity:1" />
                                </linearGradient>
                            </defs>
                            <!-- Texto del valor -->
                            <text x="100" y="80" 
                                  text-anchor="middle" 
                                  style="font-size: 36px; font-weight: 700; fill: #2c3e50; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
                                ${instValue.toFixed(2)}
                            </text>
                            <text x="100" y="102" 
                                  text-anchor="middle" 
                                  style="font-size: 13px; fill: #7f8c8d; font-weight: 500;">
                                L/min
                            </text>
                        </svg>
                        <!-- Etiquetas de escala -->
                        <div style="position: absolute; bottom: 0px; left: 5px; font-size: 10px; color: #95a5a6; font-weight: 500;">0</div>
                        <div style="position: absolute; bottom: 0px; right: 5px; font-size: 10px; color: #95a5a6; font-weight: 500;">100</div>
                    </div>
                    
                    <!-- Separador -->
                    <div style="width: 80%; height: 1px; background: linear-gradient(to right, transparent, #d1d8dd, transparent); margin: 10px 0;"></div>
                    
                    <!-- Flujo acumulado -->
                    <div style="text-align: center;">
                        <div style="font-size: 11px; color: #7f8c8d; margin-bottom: 6px; font-weight: 500; letter-spacing: 0.5px;">
                            <i class="bi bi-droplet-fill" style="color: #17a2b8;"></i> FLUJO ACUMULADO
                        </div>
                        <div style="font-size: 28px; font-weight: 700; color: #17a2b8; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;">
                            ${constValue.toFixed(2)} <span style="font-size: 16px; font-weight: 500; color: #7f8c8d;">L</span>
                        </div>
                    </div>
                </div>
            `;
            
            $("#flujometro .card-content").html(flowmeterHtml);
            
            console.log('Datos del flujómetro cargados:', data);
        } else {
            throw new Error(result.error || 'Error al cargar datos');
        }
    } catch (error) {
        console.error('Error al cargar datos del flujómetro:', error);
        $("#flujometro .card-content").html(
            `<div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; padding: 20px;">
                <div style="font-size: 3.5em; color: #dc3545;">
                    <i class="bi bi-exclamation-triangle-fill"></i>
                </div>
                <div style="margin-top: 15px; font-size: 1em; color: #7f8c8d; text-align: center;">
                    Error al cargar<br>datos del flujómetro
                </div>
            </div>`
        );
    } finally {
        appState.loadingStates.flow = true;
        checkAllLoaded();
    }
}


// Función para iniciar el monitoreo en tiempo real
function startRealtimeFlowMonitor() {
    // Limpiar intervalo anterior si existe
    if (appState.realtimeInterval) {
        clearInterval(appState.realtimeInterval);
    }
    
    // Inicializar el historial con 30 puntos (5 minutos si actualizamos cada 10 segundos)
    appState.flowHistory = new Array(30).fill(0);
    
    // Usar el último dato cargado si existe
    const initialValue = appState.lastFlowData?.constflow?.value || 0;
    updateRealtimeDisplay(initialValue);
    
    // Actualizar cada 10 segundos (reducir la frecuencia para evitar 429)
    appState.realtimeInterval = setInterval(async () => {
        // Si ya hay una petición en curso, saltar esta iteración
        if (appState.requestInProgress) {
            console.log('Petición en curso, saltando...');
            return;
        }
        
        try {
            appState.requestInProgress = true;
            
            const response = await fetch('/api/arduino/flowmeter');
            
            // Manejar error 429 (Too Many Requests)
            if (response.status === 429) {
                console.warn('⚠️ Rate limit alcanzado (429). Usando datos en caché...');
                // Usar el último dato válido
                if (appState.lastFlowData) {
                    const cachedFlow = appState.lastFlowData.constflow?.value || 0;
                    appState.flowHistory.push(cachedFlow);
                    if (appState.flowHistory.length > 30) {
                        appState.flowHistory.shift();
                    }
                    updateRealtimeDisplay(cachedFlow);
                }
                return;
            }
            
            const result = await response.json();
            
            if (result.success && result.data) {
                // Guardar en caché
                appState.lastFlowData = result.data;
                
                // constflow es el valor instantáneo en L/min
                const currentFlow = result.data.constflow?.value || 0;
                
                // Agregar al historial y mantener solo los últimos 30 valores
                appState.flowHistory.push(currentFlow);
                if (appState.flowHistory.length > 30) {
                    appState.flowHistory.shift();
                }
                
                // Actualizar la visualización
                updateRealtimeDisplay(currentFlow);
            }
        } catch (error) {
            console.error('Error al actualizar flujo en tiempo real:', error);
            // En caso de error, usar datos en caché si están disponibles
            if (appState.lastFlowData) {
                const cachedFlow = appState.lastFlowData.constflow?.value || 0;
                updateRealtimeDisplay(cachedFlow);
            }
        } finally {
            appState.requestInProgress = false;
        }
    }, 10000); // Actualizar cada 10 segundos en lugar de 2
}

// Función para detener el monitoreo en tiempo real
function stopRealtimeFlowMonitor() {
    if (appState.realtimeInterval) {
        clearInterval(appState.realtimeInterval);
        appState.realtimeInterval = null;
    }
}

// Función para actualizar la visualización en tiempo real
function updateRealtimeDisplay(currentValue) {
    const maxValue = Math.max(...appState.flowHistory, 100); // Escala dinámica con mínimo de 100
    const minValue = Math.min(...appState.flowHistory, 0);
    
    // Calcular promedio
    const average = appState.flowHistory.reduce((a, b) => a + b, 0) / appState.flowHistory.length;
    
    // Crear puntos para el gráfico de línea (simplificado)
    const width = 100;
    const height = 60;
    const points = appState.flowHistory.map((value, index) => {
        const x = (index / (appState.flowHistory.length - 1)) * width;
        const y = height - ((value - minValue) / (maxValue - minValue || 1)) * height;
        return `${x},${y}`;
    }).join(' ');
    
    // Determinar color según el valor actual
    let valueColor = '#17a2b8'; // Turquesa por defecto
    if (currentValue > average * 1.5) {
        valueColor = '#28a745'; // Verde si es alto
    } else if (currentValue < average * 0.5) {
        valueColor = '#ffc107'; // Amarillo si es bajo
    }
    
    const realtimeHtml = `
        <div style="display: flex; align-items: center; justify-content: space-between; height: 100%; padding: 20px 30px;">
            <!-- Valor actual grande -->
            <div style="flex: 0 0 200px; text-align: center;">
                <div style="font-size: 12px; color: #7f8c8d; margin-bottom: 8px; font-weight: 500; letter-spacing: 0.5px;">
                    CAUDAL ACTUAL
                </div>
                <div style="font-size: 48px; font-weight: 700; color: ${valueColor}; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1;">
                    ${currentValue.toFixed(2)}
                </div>
                <div style="font-size: 14px; color: #7f8c8d; margin-top: 5px;">
                    L/min
                </div>
            </div>
            
            <!-- Separador vertical -->
            <div style="width: 2px; height: 80%; background: linear-gradient(to bottom, transparent, #d1d8dd, transparent);"></div>
            
            <!-- Gráfico de línea en tiempo real -->
            <div style="flex: 1; padding: 0 30px;">
                <div style="font-size: 12px; color: #7f8c8d; margin-bottom: 10px; font-weight: 500; letter-spacing: 0.5px;">
                    HISTORIAL (ÚLTIMOS 5 MINUTOS)
                </div>
                <svg viewBox="0 0 ${width} ${height}" style="width: 100%; height: 80px;">
                    <!-- Línea de fondo (promedio) -->
                    <line x1="0" y1="${height - ((average - minValue) / (maxValue - minValue || 1)) * height}" 
                          x2="${width}" y2="${height - ((average - minValue) / (maxValue - minValue || 1)) * height}" 
                          stroke="#e8f4f8" 
                          stroke-width="1" 
                          stroke-dasharray="2,2"/>
                    
                    <!-- Área bajo la curva -->
                    <polygon points="0,${height} ${points} ${width},${height}" 
                             fill="url(#areaGradient)" 
                             opacity="0.3"/>
                    
                    <!-- Línea del gráfico -->
                    <polyline points="${points}" 
                              fill="none" 
                              stroke="#17a2b8" 
                              stroke-width="2.5" 
                              stroke-linecap="round"
                              stroke-linejoin="round"/>
                    
                    <!-- Punto actual -->
                    <circle cx="${width}" 
                            cy="${height - ((currentValue - minValue) / (maxValue - minValue || 1)) * height}" 
                            r="3.5" 
                            fill="${valueColor}" 
                            stroke="white" 
                            stroke-width="1.5"/>
                    
                    <!-- Gradiente para el área -->
                    <defs>
                        <linearGradient id="areaGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                            <stop offset="0%" style="stop-color:#17a2b8;stop-opacity:0.6" />
                            <stop offset="100%" style="stop-color:#17a2b8;stop-opacity:0.05" />
                        </linearGradient>
                    </defs>
                </svg>
                <div style="display: flex; justify-content: space-between; margin-top: 5px; font-size: 10px; color: #95a5a6;">
                    <span>-5min</span>
                    <span>Promedio: ${average.toFixed(2)} L/min</span>
                    <span>Ahora</span>
                </div>
            </div>
            
            <!-- Estadísticas -->
            <div style="flex: 0 0 150px; display: flex; flex-direction: column; gap: 15px;">
                <div style="text-align: center;">
                    <div style="font-size: 10px; color: #7f8c8d; margin-bottom: 3px; font-weight: 500;">MÁXIMO</div>
                    <div style="font-size: 20px; font-weight: 700; color: #28a745;">${maxValue.toFixed(2)}</div>
                </div>
                <div style="width: 80%; height: 1px; background: #e8f4f8; margin: 0 auto;"></div>
                <div style="text-align: center;">
                    <div style="font-size: 10px; color: #7f8c8d; margin-bottom: 3px; font-weight: 500;">MÍNIMO</div>
                    <div style="font-size: 20px; font-weight: 700; color: #ffc107;">${minValue.toFixed(2)}</div>
                </div>
            </div>
        </div>
    `;
    
    $("#realtime-flow .card-content").html(realtimeHtml);
}
