from django.contrib import admin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ("id", "rut", "nombre", "usuario", "rol", "estado", "created_at")
    list_filter = ("rol", "estado", "created_at")
    search_fields = ("rut", "nombre", "usuario", "sector")
