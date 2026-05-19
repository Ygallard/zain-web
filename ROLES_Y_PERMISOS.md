# Sistema de Roles y Permisos - Cuaderno de Campo Digital

## Descripción General

Se ha implementado un sistema completo de roles y permisos para el Cuaderno de Campo Digital que controla el acceso a módulos, vistas y datos según el rol del usuario autenticado.

**Niveles de seguridad:**
- Backend: Decorators, validación de ORM, middleware
- Frontend: Sidebar dinámico, botones condicionales
- Base de datos: Filtrado automático por usuario

---

## Roles Implementados

### 1. ADMIN (Administrador)
**Descripción:** Control total del sistema.

**Permisos:**
- ✅ Acceder a TODOS los módulos
- ✅ Crear, editar, eliminar usuarios
- ✅ Gestionar predios
- ✅ Gestionar cuarteles
- ✅ Visualizar todos los registros agrícolas (riego, fertilización, cosechas, aplicaciones químicas)
- ✅ Ver datos de todos los usuarios/productores
- ✅ Exportar datos (CSV, Excel)

**Módulos Accesibles:**
- Gestión Usuarios
- Predios
- Cuarteles
- Riego
- Fertilización
- Cosechas
- Aplicaciones Químicas

**Dashboard:** Estadísticas globales del sistema

---

### 2. TECNICO (Técnico Agrícola)
**Descripción:** Gestión de registros operativos sin acceso a datos administrativos.

**Permisos:**
- ✅ Visualizar predios (todos)
- ✅ Visualizar cuarteles (todos)
- ✅ Crear/editar/eliminar riegos
- ✅ Crear/editar/eliminar fertilizaciones
- ✅ Crear/editar/eliminar cosechas
- ✅ Crear/editar/eliminar aplicaciones químicas
- ❌ NO puede gestionar usuarios
- ❌ NO puede eliminar registros críticos
- ❌ NO puede ver datos de gestión

**Módulos Accesibles:**
- Riego
- Fertilización
- Cosechas
- Aplicaciones Químicas

**Dashboard:** Resumen de registros operativos globales

---

### 3. PRODUCTOR (Productor Agrícola)
**Descripción:** Acceso limitado a datos propios.

**Permisos:**
- ✅ Visualizar SOLO sus predios
- ✅ Visualizar SOLO sus cuarteles
- ✅ Crear/editar/eliminar riegos en sus predios
- ✅ Crear/editar/eliminar fertilizaciones en sus predios
- ✅ Crear/editar/eliminar cosechas en sus predios
- ✅ Crear/editar/eliminar aplicaciones químicas en sus predios
- ❌ NO puede ver datos de otros productores
- ❌ NO puede gestionar usuarios
- ❌ NO puede ver/gestionar predios de otros

**Módulos Accesibles:**
- Predios (solo los suyos)
- Cuarteles (solo los de sus predios)
- Riego
- Fertilización
- Cosechas
- Aplicaciones Químicas

**Dashboard:** Resumen de sus datos únicamente

---

## Arquitectura de Seguridad

### 1. Decorators (`usuarios/decorators.py`)

```python
# Decorador básico
@login_required_custom
def algunaVista(request):
    ...

# Decorador con roles
@role_required(Usuario.ROL_ADMIN, Usuario.ROL_TECNICO)
def algunaVista(request):
    ...

# Decoradores específicos
@admin_only
def soloAdmin(request):
    ...

@tecnico_or_admin
def adminOTecnico(request):
    ...
```

### 2. Permisos y Filtrado (`usuarios/permissions.py`)

**Funciones de validación de permisos:**
```python
has_permission(request, "can_manage_usuarios")
can_manage_riegos(request)
can_view_all_data(request)  # ADMIN/TECNICO: True, PRODUCTOR: False
```

**Funciones de filtrado ORM automático:**
```python
# El filtrado se aplica automáticamente según el rol
get_filtered_riegos(request, q="")  # PRODUCTOR solo ve sus riegos
get_filtered_cosechas(request, q="")  # PRODUCTOR solo ve sus cosechas
get_filtered_aplicaciones_quimicas(request, q="")  # PRODUCTOR solo ve sus apps
```

**Validación de propiedad de datos:**
```python
user_owns_riego(request, riego_id)  # ¿Es dueño de este riego?
user_owns_cosecha(request, cosecha_id)  # ¿Es dueño de esta cosecha?
user_owns_aplicacion_quimica(request, app_id)  # ¿Es dueño?
```

### 3. Middleware (`usuarios/middleware.py`)

- **RoleBasedAccessMiddleware:** Valida acceso a URLs según rol
- Previene acceso directo a URLs administrativas por parte de productores
- Redirige a dashboard en caso de intento no autorizado

### 4. Sidebar Dinámico (`usuarios/templates/base.html`)

El sidebar se renderiza dinámicamente basado en `sidebar_context`:
```django
{% if sidebar_context.can_manage_usuarios %}
    <li><a href="...">Gestión Usuarios</a></li>
{% endif %}

{% if sidebar_context.can_manage_riegos %}
    <li><a href="...">Riego</a></li>
{% endif %}
```

### 5. Dashboard Dinámico (`usuarios/views.py`)

Diferentes datos según rol:

**ADMIN:**
- Total de usuarios
- Estadísticas de predios
- Producción total (kg, bins)
- Análisis químicos

**TECNICO:**
- Riegos totales
- Fertilizaciones totales
- Cosechas totales
- Aplicaciones químicas

**PRODUCTOR:**
- Sus predios totales
- Sus cuarteles totales
- Sus riegos totales
- Su producción (kg, bins)

---

## Flujo de Autenticación y Autorización

### 1. Login
```python
# views.py - login_view()
usuario = Usuario.objects.filter(usuario=usuario_input, estado=True).first()
if usuario and check_password(password, usuario.password):
    request.session["usuario_id"] = usuario.id
    request.session["rol"] = usuario.rol  # Almacenar rol en sesión
```

### 2. Protección en Vistas
```python
@role_required(Usuario.ROL_ADMIN, Usuario.ROL_TECNICO)
def riego_list_view(request):
    # Accesible para ADMIN y TECNICO
    riegos = get_filtered_riegos(request, q)  # Automáticamente filtrado
    # PRODUCTOR es redirigido al dashboard si intenta acceder
```

### 3. Validación de Propiedad
```python
@role_required(Usuario.ROL_ADMIN, Usuario.ROL_TECNICO, Usuario.ROL_PRODUCTOR)
def riego_detail_view(request, pk):
    if not user_owns_riego(request, pk):  # Validación
        return JsonResponse({"error": "No autorizado"}, status=403)
    # Continuar...
```

### 4. Filtrado Automático ORM
```python
def get_filtered_riegos(request, q=""):
    queryset = Riego.objects.select_related("cuartel", "cuartel__predio")
    
    if rol == Usuario.ROL_PRODUCTOR:
        # PRODUCTOR solo ve sus riegos
        queryset = queryset.filter(cuartel__predio__usuario_id=user_id)
    
    # ADMIN y TECNICO ven todos
    return queryset
```

---

## Integración en Vistas

### Patrón Standard en List Views
```python
@role_required(Usuario.ROL_ADMIN, Usuario.ROL_TECNICO, Usuario.ROL_PRODUCTOR)
def riegos_list_view(request):
    current_user = get_current_user(request)
    q = request.GET.get("q", "").strip()
    
    # Filtrado automático según rol
    riegos = get_filtered_riegos(request, q)
    
    # Contexto para template (incluye sidebar dinámico)
    return render(request, "template.html", {
        "riegos": riegos,
        "current_user": current_user,
        "sidebar_context": get_sidebar_context(request),
        "can_manage": can_manage_riegos(request),
    })
```

### Patrón en Detail/Update/Delete Views
```python
@role_required(Usuario.ROL_ADMIN, Usuario.ROL_TECNICO, Usuario.ROL_PRODUCTOR)
def riego_update_view(request, pk):
    # VALIDACIÓN CRÍTICA: ¿Es dueño del dato?
    if not user_owns_riego(request, pk):
        return JsonResponse({"error": "No autorizado"}, status=403)
    
    # Proceder con actualización
    riego = Riego.objects.get(pk=pk)
    ...
```

---

## Seguridad Implementada

### ✅ Frontend
- Sidebar oculta opciones no permitidas
- Botones de crear/editar/eliminar deshabilitados
- Formularios condicionados por rol

### ✅ Backend
- Decorators `@role_required` validan rol
- `user_owns_*` valida propiedad de datos
- Middleware previene acceso directo a URLs
- Filtrado ORM automático en queries

### ✅ Base de Datos
- Relación `usuario_id` en Predio
- Filtrado automático en JOIN (cuartel → predio → usuario)
- Imposible manipular SQL para ver datos ajenos

### ✅ API/AJAX
- Endpoints devuelven 403 Forbidden si no autorizado
- JSON responses con mensajes claros
- No expone datos en errores

---

## URLs Protegidas

### Solo ADMIN
- `/usuarios/` - Gestión de usuarios
- `/predios/` - Gestión de predios
- `/cuarteles/` - Gestión de cuarteles

### ADMIN + TECNICO + PRODUCTOR
- `/riegos/` - Lista de riegos (filtrada automáticamente)
- `/fertilizaciones/` - Lista de fertilizaciones (filtrada)
- `/cosechas/` - Lista de cosechas (filtrada)
- `/aplicaciones-quimicas/` - Aplicaciones químicas (filtradas)

### Rutas de Detalle/Edición/Eliminación
- Requieren validación de propiedad adicional para PRODUCTOR

---

## Archivos Modificados

1. **`usuarios/decorators.py`** - Decorators mejorados
2. **`usuarios/permissions.py`** - Nuevo: Sistema de permisos y filtrado
3. **`usuarios/middleware.py`** - Nuevo: Middleware de control de acceso
4. **`usuarios/views.py`** - Actualizado: Decorators y filtrado en vistas
5. **`usuarios/templates/base.html`** - Sidebar dinámico
6. **`cuaderno_campo_django/settings.py`** - Middleware registrado

---

## Pruebas Recomendadas

### Test 1: Login y Roles
1. Login como ADMIN → Ver todos los módulos
2. Login como TECNICO → Ver solo módulos operativos
3. Login como PRODUCTOR → Ver solo sus datos

### Test 2: Sidebar Dinámico
1. Admin → 7 items en sidebar
2. Técnico → 4 items (sin usuarios, predios, cuarteles)
3. Productor → 6 items (sin usuarios)

### Test 3: Filtrado de Datos
1. PRODUCTOR crea riego → Solo ve el suyo
2. PRODUCTOR intenta acceder a `/riegos/?id=2` → Si no es suyo: 403

### Test 4: URLs Protegidas
1. PRODUCTOR intenta `/usuarios/` → Redirigido a dashboard
2. TECNICO intenta `/predios/` → Redirigido a dashboard
3. ADMIN accede a todo → OK

### Test 5: API/AJAX
1. PRODUCTOR intenta editar riego ajeno vía AJAX → 403 JSON
2. TECNICO actualiza fertilización → OK
3. ADMIN elimina cualquier dato → OK

---

## Notas Importantes

- **Sin acceso visible = Sin acceso real:** La seguridad no se basa solo en ocultar opciones
- **Validación en Backend:** Toda protección ocurre en backend, no en cliente
- **Filtrado Automático:** No necesita código manual en cada vista
- **Escalable:** Fácil agregar nuevos roles usando `ROLE_PERMISSIONS`

---

## Próximas Mejoras Sugeridas

- [ ] Auditoría de acciones (logs)
- [ ] Rate limiting por rol
- [ ] 2FA para ADMIN
- [ ] Backup automático
- [ ] Permisos granulares (por módulo, por acción)
- [ ] Sistema de grupos de usuarios
