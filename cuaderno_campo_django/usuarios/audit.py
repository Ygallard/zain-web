from threading import local
from datetime import timedelta

from django.utils import timezone

from .decorators import AUTH_SESSION_KEY
from .models import (
    AplicacionQuimica,
    Cosecha,
    Cuartel,
    Fertilizacion,
    LogActividad,
    Predio,
    Riego,
    Usuario,
)


_audit_local = local()


MODEL_MODULES = {
    Usuario: "usuarios",
    Predio: "predios",
    Cuartel: "cuarteles",
    Riego: "riego",
    Fertilizacion: "fertilizacion",
    Cosecha: "cosechas",
    AplicacionQuimica: "aplicaciones_quimicas",
}


IMPORTANT_AUDIT_ACTIONS = {
    LogActividad.ACCION_CREAR,
    LogActividad.ACCION_EDITAR,
    LogActividad.ACCION_ELIMINAR,
    LogActividad.ACCION_LOGIN,
    LogActividad.ACCION_LOGOUT,
}


def set_current_request(request):
    _audit_local.request = request


def clear_current_request():
    if hasattr(_audit_local, "request"):
        delattr(_audit_local, "request")


def get_current_request():
    return getattr(_audit_local, "request", None)


def get_actor_from_request(request):
    if not request:
        return None

    user_id = request.session.get(AUTH_SESSION_KEY)
    if not user_id:
        return None

    return Usuario.objects.filter(id=user_id, estado=True).first()


def get_module_for_instance(instance):
    for model_class, module_name in MODEL_MODULES.items():
        if isinstance(instance, model_class):
            return module_name
    return "sistema"


def build_crud_description(actor, accion, modulo, instance):
    actor_name = actor.nombre if actor else "Sistema"
    instance_label = str(instance)

    if accion == LogActividad.ACCION_CREAR:
        verb = "creo"
    elif accion == LogActividad.ACCION_EDITAR:
        verb = "edito"
    elif accion == LogActividad.ACCION_ELIMINAR:
        verb = "elimino"
    else:
        verb = "registro"

    return f"{actor_name} {verb} {modulo}: {instance_label}"


def _sanitize_text(value, fallback, max_len):
    text = (value or "").strip()
    if not text:
        text = fallback
    return text[:max_len]


def registrar_auditoria(usuario, accion, modulo, descripcion, deduplicate_seconds=5):
    """Registra auditoría solo para acciones importantes y evita duplicados inmediatos."""
    if not usuario:
        return None

    accion = _sanitize_text(accion, "", 100).upper()
    if accion not in IMPORTANT_AUDIT_ACTIONS:
        return None

    modulo = _sanitize_text(modulo, "sistema", 100).lower()
    descripcion = _sanitize_text(descripcion, "Sin detalle", 240)

    if deduplicate_seconds and deduplicate_seconds > 0:
        since = timezone.now() - timedelta(seconds=deduplicate_seconds)
        duplicated = (
            LogActividad.objects.filter(
                usuario=usuario,
                accion=accion,
                modulo=modulo,
                descripcion=descripcion,
                fecha__gte=since,
            )
            .order_by("-id")
            .first()
        )
        if duplicated:
            return duplicated

    try:
        return LogActividad.objects.create(
            usuario=usuario,
            accion=accion,
            modulo=modulo,
            descripcion=descripcion,
        )
    except Exception:
        return None


def registrar_log_actividad(usuario, accion, modulo, descripcion):
    """Compatibilidad retroactiva: delega al helper centralizado."""
    return registrar_auditoria(usuario, accion, modulo, descripcion)


def registrar_log_desde_request(request, accion, modulo, descripcion):
    actor = get_actor_from_request(request)
    return registrar_auditoria(actor, accion, modulo, descripcion)


def registrar_auditoria_desde_request(request, accion, modulo, descripcion, deduplicate_seconds=5):
    actor = get_actor_from_request(request)
    return registrar_auditoria(actor, accion, modulo, descripcion, deduplicate_seconds=deduplicate_seconds)
