from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .audit import (
    build_crud_description,
    get_actor_from_request,
    get_current_request,
    get_module_for_instance,
    registrar_auditoria,
)
from .models import AplicacionQuimica, Cosecha, Cuartel, Fertilizacion, Predio, Riego, Usuario, LogActividad


MONITORED_MODELS = (Usuario, Predio, Cuartel, Riego, Fertilizacion, Cosecha, AplicacionQuimica)


@receiver(post_save)
def registrar_creacion_edicion(sender, instance, created, **kwargs):
    if sender not in MONITORED_MODELS:
        return

    request = get_current_request()
    actor = get_actor_from_request(request)
    if not actor:
        return

    accion = LogActividad.ACCION_CREAR if created else LogActividad.ACCION_EDITAR
    modulo = get_module_for_instance(instance)
    descripcion = build_crud_description(actor, accion, modulo, instance)

    registrar_auditoria(actor, accion, modulo, descripcion)


@receiver(post_delete)
def registrar_eliminacion(sender, instance, **kwargs):
    if sender not in MONITORED_MODELS:
        return

    request = get_current_request()
    actor = get_actor_from_request(request)
    if not actor:
        return

    accion = LogActividad.ACCION_ELIMINAR
    modulo = get_module_for_instance(instance)
    descripcion = build_crud_description(actor, accion, modulo, instance)

    registrar_auditoria(actor, accion, modulo, descripcion)
