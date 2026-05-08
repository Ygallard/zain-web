from django.db import models


class Usuario(models.Model):
    ROL_ADMIN = "admin"
    ROL_TECNICO = "tecnico"
    ROL_PRODUCTOR = "productor"

    ROLE_CHOICES = [
        (ROL_ADMIN, "Administrador"),
        (ROL_TECNICO, "Tecnico"),
        (ROL_PRODUCTOR, "Productor"),
    ]

    rut = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=100)
    usuario = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=255)
    rol = models.CharField(max_length=20, choices=ROLE_CHOICES)
    celular = models.CharField(max_length=20, blank=True)
    sector = models.CharField(max_length=100, blank=True)
    estado = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "usuarios"
        ordering = ["-created_at"]
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        return f"{self.nombre} ({self.usuario})"
