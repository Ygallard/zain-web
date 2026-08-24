import os

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError

from usuarios.models import Usuario


class Command(BaseCommand):
    help = "Crea o actualiza el administrador inicial cuando el bootstrap esta habilitado."

    def handle(self, *args, **options):
        if os.getenv("BOOTSTRAP_ADMIN_ENABLED", "false").strip().lower() != "true":
            self.stdout.write("Bootstrap de administrador deshabilitado.")
            return

        username = os.getenv("AUTH_USERNAME", "").strip()
        password = os.getenv("AUTH_PASSWORD", "")
        rut = os.getenv("BOOTSTRAP_ADMIN_RUT", "").strip()
        nombre = os.getenv("BOOTSTRAP_ADMIN_NOMBRE", "Administrador").strip()

        if not username or not password or not rut:
            raise CommandError(
                "BOOTSTRAP_ADMIN_RUT, AUTH_USERNAME y AUTH_PASSWORD son obligatorios."
            )

        usuario = Usuario.objects.filter(usuario__iexact=username).first()
        if usuario is None:
            usuario = Usuario(usuario=username, rut=rut, nombre=nombre)
        elif usuario.rut != rut and Usuario.objects.filter(rut=rut).exclude(pk=usuario.pk).exists():
            raise CommandError("BOOTSTRAP_ADMIN_RUT ya pertenece a otro usuario.")

        usuario.usuario = username
        usuario.rut = rut
        usuario.nombre = nombre
        usuario.rol = Usuario.ROL_ADMIN
        usuario.estado = True
        usuario.password = make_password(password)
        usuario.save()
        self.stdout.write(self.style.SUCCESS(f"Administrador '{username}' configurado."))
