"""
Módulo de permisos y filtrado de datos según rol.
Define lógica de control de acceso y filtrado automático de ORM.
"""

from django.db.models import Q

from .models import Usuario, Predio, Cuartel, Riego, Fertilizacion, Cosecha, AplicacionQuimica, LaborAgricola


# ============================================================================
# CONSTANTES DE PERMISOS POR ROL
# ============================================================================

ROLE_PERMISSIONS = {
    Usuario.ROL_ADMIN: {
        "can_manage_usuarios": True,
        "can_manage_predios": True,
        "can_manage_cuarteles": True,
        "can_manage_riegos": True,
        "can_manage_fertilizaciones": True,
        "can_manage_cosechas": True,
        "can_manage_aplicaciones_quimicas": True,
        "can_manage_labores_agricolas": True,
        "can_manage_auditoria": True,
        "can_view_all_data": True,
    },
    Usuario.ROL_TECNICO: {
        # PRODESAL: supervision y apoyo tecnico. Solo lectura + comentarios + notificaciones.
        "can_manage_usuarios": False,
        "can_manage_predios": False,
        "can_manage_cuarteles": False,
        "can_manage_riegos": False,
        "can_manage_fertilizaciones": False,
        "can_manage_cosechas": False,
        "can_manage_aplicaciones_quimicas": False,
        "can_manage_labores_agricolas": False,
        "can_manage_auditoria": False,
        "can_view_all_data": True,
        "can_comment": True,
        "can_send_notifications": True,
    },
    Usuario.ROL_PRODUCTOR: {
        "can_manage_usuarios": False,
        "can_manage_predios": True,
        "can_manage_cuarteles": True,
        "can_manage_riegos": True,
        "can_manage_fertilizaciones": True,
        "can_manage_cosechas": True,
        "can_manage_aplicaciones_quimicas": True,
        "can_manage_labores_agricolas": True,
        "can_manage_auditoria": False,
        "can_view_all_data": False,  # Solo sus propios datos
    },
}

# Sidebar items según rol
SIDEBAR_ITEMS = {
    Usuario.ROL_ADMIN: [
        "usuarios_lista",
        "predios_lista",
        "cuarteles_lista",
        "riegos_lista",
        "fertilizaciones_lista",
        "cosechas_lista",
        "aplicaciones_quimicas_lista",
        "labores_agricolas_lista",
        "auditoria_logs",
    ],
    Usuario.ROL_TECNICO: [
        "productores_lista",
        "predios_lista",
        "cuarteles_lista",
        "riegos_lista",
        "fertilizaciones_lista",
        "cosechas_lista",
        "aplicaciones_quimicas_lista",
        "labores_agricolas_lista",
    ],
    Usuario.ROL_PRODUCTOR: [
        "predios_lista",
        "cuarteles_lista",
        "riegos_lista",
        "fertilizaciones_lista",
        "cosechas_lista",
        "aplicaciones_quimicas_lista",
        "labores_agricolas_lista",
    ],
}


# ============================================================================
# FUNCIONES DE VALIDACIÓN DE PERMISOS
# ============================================================================

def has_permission(request, permission_key):
    """Valida si el usuario actual tiene un permiso específico."""
    rol = request.session.get("rol")
    if not rol:
        return False
    
    permissions = ROLE_PERMISSIONS.get(rol, {})
    return permissions.get(permission_key, False)


def can_manage_usuarios(request):
    """¿Puede gestionar usuarios?"""
    return has_permission(request, "can_manage_usuarios")


def can_manage_predios(request):
    """¿Puede gestionar predios?"""
    return has_permission(request, "can_manage_predios")


def can_manage_cuarteles(request):
    """¿Puede gestionar cuarteles?"""
    return has_permission(request, "can_manage_cuarteles")


def can_manage_riegos(request):
    """¿Puede gestionar riegos?"""
    return has_permission(request, "can_manage_riegos")


def can_manage_fertilizaciones(request):
    """¿Puede gestionar fertilizaciones?"""
    return has_permission(request, "can_manage_fertilizaciones")


def can_manage_cosechas(request):
    """¿Puede gestionar cosechas?"""
    return has_permission(request, "can_manage_cosechas")


def can_manage_aplicaciones_quimicas(request):
    """¿Puede gestionar aplicaciones químicas?"""
    return has_permission(request, "can_manage_aplicaciones_quimicas")


def can_manage_labores_agricolas(request):
    """¿Puede gestionar labores agrícolas?"""
    return has_permission(request, "can_manage_labores_agricolas")


def can_view_all_data(request):
    """¿Puede ver todos los datos o solo los suyos?"""
    return has_permission(request, "can_view_all_data")


def can_manage_auditoria(request):
    """¿Puede visualizar la auditoria del sistema?"""
    return has_permission(request, "can_manage_auditoria")


def can_comment(request):
    """¿Puede dejar observaciones tecnicas sobre registros?"""
    return has_permission(request, "can_comment")


def can_send_notifications(request):
    """¿Puede enviar notificaciones a productores?"""
    return has_permission(request, "can_send_notifications")


# ============================================================================
# FUNCIONES DE FILTRADO ORM
# ============================================================================

def get_filtered_predios(request):
    """
    Retorna QuerySet de predios filtrado según rol.
    - ADMIN: todos
    - TECNICO: todos
    - PRODUCTOR: solo suyos
    """
    rol = request.session.get("rol")
    user_id = request.session.get("usuario_id")
    
    queryset = Predio.objects.select_related("usuario").all()
    
    if rol == Usuario.ROL_PRODUCTOR and user_id:
        queryset = queryset.filter(usuario_id=user_id)
    
    return queryset


def get_form_predios_queryset(request):
    """Retorna predios activos permitidos para formularios segun rol."""
    return get_filtered_predios(request).filter(estado=True).order_by("nombre_predio")


def get_filtered_cuarteles(request):
    """
    Retorna QuerySet de cuarteles filtrado según rol.
    - ADMIN: todos
    - TECNICO: todos
    - PRODUCTOR: solo sus cuarteles (a través de su predio)
    """
    rol = request.session.get("rol")
    user_id = request.session.get("usuario_id")
    
    queryset = Cuartel.objects.select_related("predio", "predio__usuario").all()
    
    if rol == Usuario.ROL_PRODUCTOR and user_id:
        queryset = queryset.filter(predio__usuario_id=user_id)
    
    return queryset


def get_form_cuarteles_queryset(request, predio_id=None):
    """Retorna cuarteles activos permitidos para formularios segun rol."""
    queryset = get_filtered_cuarteles(request).filter(estado=True, predio__estado=True)
    if predio_id:
        queryset = queryset.filter(predio_id=predio_id)
    return queryset.order_by("nombre_cuartel")


def get_filtered_riegos(request, q=""):
    """
    Retorna QuerySet de riegos filtrado según rol.
    - ADMIN: todos
    - TECNICO: todos
    - PRODUCTOR: solo sus riegos (a través de sus cuarteles)
    """
    rol = request.session.get("rol")
    user_id = request.session.get("usuario_id")
    
    queryset = Riego.objects.select_related("cuartel", "cuartel__predio", "cuartel__predio__usuario").all()
    
    if rol == Usuario.ROL_PRODUCTOR and user_id:
        queryset = queryset.filter(cuartel__predio__usuario_id=user_id)
    
    if q:
        queryset = queryset.filter(
            Q(cuartel__predio__nombre_predio__icontains=q)
            | Q(cuartel__nombre_cuartel__icontains=q)
            | Q(tipo_riego__icontains=q)
            | Q(observaciones__icontains=q)
        )
    
    return queryset


def get_filtered_fertilizaciones(request, q=""):
    """
    Retorna QuerySet de fertilizaciones filtrado según rol.
    - ADMIN: todas
    - TECNICO: todas
    - PRODUCTOR: solo sus fertilizaciones (a través de sus cuarteles)
    """
    rol = request.session.get("rol")
    user_id = request.session.get("usuario_id")
    
    queryset = Fertilizacion.objects.select_related("cuartel", "cuartel__predio", "cuartel__predio__usuario").all()
    
    if rol == Usuario.ROL_PRODUCTOR and user_id:
        queryset = queryset.filter(cuartel__predio__usuario_id=user_id)
    
    if q:
        queryset = queryset.filter(
            Q(cuartel__predio__nombre_predio__icontains=q)
            | Q(cuartel__nombre_cuartel__icontains=q)
            | Q(producto__icontains=q)
            | Q(metodo_aplicacion__icontains=q)
        )
    
    return queryset


def get_filtered_cosechas(request, q=""):
    """
    Retorna QuerySet de cosechas filtrado según rol.
    - ADMIN: todas
    - TECNICO: todas
    - PRODUCTOR: solo sus cosechas (a través de sus cuarteles)
    """
    rol = request.session.get("rol")
    user_id = request.session.get("usuario_id")
    
    queryset = Cosecha.objects.select_related("cuartel", "cuartel__predio", "cuartel__predio__usuario").all()
    
    if rol == Usuario.ROL_PRODUCTOR and user_id:
        queryset = queryset.filter(cuartel__predio__usuario_id=user_id)
    
    if q:
        queryset = queryset.filter(
            Q(cuartel__predio__nombre_predio__icontains=q)
            | Q(cuartel__nombre_cuartel__icontains=q)
            | Q(tipo_cosecha__icontains=q)
            | Q(destino__icontains=q)
        )
    
    return queryset


def get_filtered_aplicaciones_quimicas(request, q=""):
    """
    Retorna QuerySet de aplicaciones químicas filtrado según rol.
    - ADMIN: todas
    - TECNICO: todas
    - PRODUCTOR: solo sus aplicaciones (a través de sus cuarteles)
    """
    rol = request.session.get("rol")
    user_id = request.session.get("usuario_id")
    
    queryset = AplicacionQuimica.objects.select_related("cuartel", "cuartel__predio", "cuartel__predio__usuario").all()
    
    if rol == Usuario.ROL_PRODUCTOR and user_id:
        queryset = queryset.filter(cuartel__predio__usuario_id=user_id)
    
    if q:
        queryset = queryset.filter(
            Q(cuartel__predio__nombre_predio__icontains=q)
            | Q(cuartel__nombre_cuartel__icontains=q)
            | Q(producto__icontains=q)
            | Q(tipo_producto__icontains=q)
            | Q(responsable__icontains=q)
        )
    
    return queryset


def get_filtered_labores_agricolas(request, q=""):
    """
    Retorna QuerySet de labores agrícolas filtrado según rol.
    - ADMIN: todas
    - TECNICO: todas
    - PRODUCTOR: solo sus labores (a través de sus cuarteles)
    """
    rol = request.session.get("rol")
    user_id = request.session.get("usuario_id")

    queryset = LaborAgricola.objects.select_related(
        "usuario", "predio", "cuartel", "cuartel__predio", "cuartel__predio__usuario"
    ).all()

    if rol == Usuario.ROL_PRODUCTOR and user_id:
        queryset = queryset.filter(cuartel__predio__usuario_id=user_id)

    if q:
        queryset = queryset.filter(
            Q(predio__nombre_predio__icontains=q)
            | Q(cuartel__nombre_cuartel__icontains=q)
            | Q(tipo_labor__icontains=q)
            | Q(subtipo__icontains=q)
            | Q(responsable__icontains=q)
            | Q(descripcion__icontains=q)
            | Q(observaciones__icontains=q)
        )

    return queryset


# ============================================================================
# FUNCIONES DE VALIDACIÓN DE PROPIEDAD DE DATOS
# ============================================================================

def user_owns_predio(request, predio_id):
    """Valida que el usuario sea propietario del predio."""
    rol = request.session.get("rol")
    user_id = request.session.get("usuario_id")
    
    # Admins ven todo
    if rol == Usuario.ROL_ADMIN:
        return True
    
    # Productores solo ven sus predios
    if rol == Usuario.ROL_PRODUCTOR:
        try:
            predio = Predio.objects.get(id=predio_id, usuario_id=user_id)
            return True
        except Predio.DoesNotExist:
            return False
    
    # Técnicos pueden ver todos
    return True


def user_owns_cuartel(request, cuartel_id):
    """Valida que el usuario sea propietario del cuartel."""
    rol = request.session.get("rol")
    user_id = request.session.get("usuario_id")
    
    # Admins ven todo
    if rol == Usuario.ROL_ADMIN:
        return True
    
    # Productores solo ven sus cuarteles
    if rol == Usuario.ROL_PRODUCTOR:
        try:
            cuartel = Cuartel.objects.get(id=cuartel_id, predio__usuario_id=user_id)
            return True
        except Cuartel.DoesNotExist:
            return False
    
    # Técnicos pueden ver todos
    return True


def user_owns_riego(request, riego_id):
    """Valida que el usuario sea propietario del riego."""
    rol = request.session.get("rol")
    user_id = request.session.get("usuario_id")
    
    # Admins ven todo
    if rol == Usuario.ROL_ADMIN:
        return True
    
    # Productores solo ven sus riegos
    if rol == Usuario.ROL_PRODUCTOR:
        try:
            riego = Riego.objects.get(id=riego_id, cuartel__predio__usuario_id=user_id)
            return True
        except Riego.DoesNotExist:
            return False
    
    # Técnicos pueden ver todos
    return True


def user_owns_fertilizacion(request, fertilizacion_id):
    """Valida que el usuario sea propietario de la fertilización."""
    rol = request.session.get("rol")
    user_id = request.session.get("usuario_id")
    
    # Admins ven todo
    if rol == Usuario.ROL_ADMIN:
        return True
    
    # Productores solo ven sus fertilizaciones
    if rol == Usuario.ROL_PRODUCTOR:
        try:
            fertilizacion = Fertilizacion.objects.get(id=fertilizacion_id, cuartel__predio__usuario_id=user_id)
            return True
        except Fertilizacion.DoesNotExist:
            return False
    
    # Técnicos pueden ver todos
    return True


def user_owns_cosecha(request, cosecha_id):
    """Valida que el usuario sea propietario de la cosecha."""
    rol = request.session.get("rol")
    user_id = request.session.get("usuario_id")
    
    # Admins ven todo
    if rol == Usuario.ROL_ADMIN:
        return True
    
    # Productores solo ven sus cosechas
    if rol == Usuario.ROL_PRODUCTOR:
        try:
            cosecha = Cosecha.objects.get(id=cosecha_id, cuartel__predio__usuario_id=user_id)
            return True
        except Cosecha.DoesNotExist:
            return False
    
    # Técnicos pueden ver todos
    return True


def user_owns_aplicacion_quimica(request, aplicacion_id):
    """Valida que el usuario sea propietario de la aplicación química."""
    rol = request.session.get("rol")
    user_id = request.session.get("usuario_id")
    
    # Admins ven todo
    if rol == Usuario.ROL_ADMIN:
        return True
    
    # Productores solo ven sus aplicaciones
    if rol == Usuario.ROL_PRODUCTOR:
        try:
            aplicacion = AplicacionQuimica.objects.get(id=aplicacion_id, cuartel__predio__usuario_id=user_id)
            return True
        except AplicacionQuimica.DoesNotExist:
            return False
    
    # Técnicos pueden ver todos
    return True


def user_owns_labor_agricola(request, labor_id):
    """Valida que el usuario sea propietario de la labor agrícola."""
    rol = request.session.get("rol")
    user_id = request.session.get("usuario_id")

    if rol == Usuario.ROL_ADMIN:
        return True

    if rol == Usuario.ROL_PRODUCTOR:
        try:
            LaborAgricola.objects.get(id=labor_id, cuartel__predio__usuario_id=user_id)
            return True
        except LaborAgricola.DoesNotExist:
            return False

    return True


# ============================================================================
# COMENTARIOS / OBSERVACIONES TECNICAS (PRODESAL)
# ============================================================================

# Mapa de modulo -> (modelo, campo de relacion hasta el usuario/productor propietario)
MODULO_OWNER_LOOKUP = {
    "predio": (Predio, "usuario_id"),
    "cuartel": (Cuartel, "predio__usuario_id"),
    "riego": (Riego, "cuartel__predio__usuario_id"),
    "fertilizacion": (Fertilizacion, "cuartel__predio__usuario_id"),
    "cosecha": (Cosecha, "cuartel__predio__usuario_id"),
    "aplicacion_quimica": (AplicacionQuimica, "cuartel__predio__usuario_id"),
    "labor_agricola": (LaborAgricola, "cuartel__predio__usuario_id"),
}


def get_registro_y_productor(modulo, objeto_id):
    """
    Resuelve el registro y el id del productor propietario para un modulo/objeto_id dado.
    Retorna (registro, productor_id) o (None, None) si no existe.
    """
    lookup = MODULO_OWNER_LOOKUP.get(modulo)
    if not lookup:
        return None, None

    model_class, owner_field = lookup
    try:
        registro = model_class.objects.get(id=objeto_id)
    except model_class.DoesNotExist:
        return None, None

    productor_id = registro
    for attr in owner_field.split("__"):
        if productor_id is None:
            break
        productor_id = getattr(productor_id, attr, None)

    return registro, productor_id


def user_can_view_registro(request, modulo, objeto_id):
    """Valida que el usuario actual tenga permiso para consultar el registro (misma regla que las listas filtradas)."""
    rol = request.session.get("rol")
    user_id = request.session.get("usuario_id")

    registro, productor_id = get_registro_y_productor(modulo, objeto_id)
    if registro is None:
        return False

    if rol in {Usuario.ROL_ADMIN, Usuario.ROL_TECNICO}:
        return True

    if rol == Usuario.ROL_PRODUCTOR:
        return productor_id == user_id

    return False


# ============================================================================
# CONTEXTO PARA TEMPLATES
# ============================================================================

def get_sidebar_context(request):
    """Retorna contexto para renderizar sidebar dinámico según rol."""
    rol = request.session.get("rol")
    available_items = SIDEBAR_ITEMS.get(rol, [])

    user_id = request.session.get("usuario_id")
    notificaciones_no_leidas = 0
    if rol == Usuario.ROL_PRODUCTOR and user_id:
        from .models import Notificacion

        notificaciones_no_leidas = Notificacion.objects.filter(productor_id=user_id, leido=False).count()

    return {
        "rol": rol,
        "sidebar_items": available_items,
        "can_manage_usuarios": can_manage_usuarios(request),
        "can_manage_predios": can_manage_predios(request),
        "can_manage_cuarteles": can_manage_cuarteles(request),
        "can_manage_riegos": can_manage_riegos(request),
        "can_manage_fertilizaciones": can_manage_fertilizaciones(request),
        "can_manage_cosechas": can_manage_cosechas(request),
        "can_manage_aplicaciones_quimicas": can_manage_aplicaciones_quimicas(request),
        "can_manage_labores_agricolas": can_manage_labores_agricolas(request),
        "can_manage_auditoria": can_manage_auditoria(request),
        "can_comment": can_comment(request),
        "can_send_notifications": can_send_notifications(request),
        "notificaciones_no_leidas": notificaciones_no_leidas,
    }
