from django.contrib import admin

from .models import LogActividad, Usuario


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ("id", "rut", "nombre", "usuario", "rol", "estado", "created_at")
    list_filter = ("rol", "estado", "created_at")
    search_fields = ("rut", "nombre", "usuario", "sector")


@admin.register(LogActividad)
class LogActividadAdmin(admin.ModelAdmin):
    list_display = ("id", "usuario", "accion", "modulo", "fecha")
    list_filter = ("accion", "modulo", "fecha")
    search_fields = ("usuario__nombre", "usuario__usuario", "descripcion")
    readonly_fields = ("usuario", "accion", "modulo", "descripcion", "fecha")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
