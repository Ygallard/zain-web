from django.db import models
from django.core.exceptions import ValidationError


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


class Predio(models.Model):
    usuario = models.ForeignKey(
        Usuario,
        models.DO_NOTHING,
        db_column="usuario_id",
        related_name="predios",
    )
    nombre_predio = models.CharField(max_length=100)
    ubicacion = models.CharField(max_length=150, blank=True, null=True)
    superficie = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    estado = models.BooleanField(blank=True, null=True, default=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "predios"
        ordering = ["-created_at", "-id"]
        verbose_name = "Predio"
        verbose_name_plural = "Predios"

    def __str__(self):
        return self.nombre_predio


class Cuartel(models.Model):
    FORMA_RIEGO_CHOICES = [
        ("goteo", "Goteo"),
        ("aspersion", "Aspersión"),
        ("microaspersion", "Microaspersión"),
        ("surcos", "Surcos"),
        ("tendido", "Tendido"),
        ("otro", "Otro"),
    ]

    predio = models.ForeignKey(
        Predio,
        on_delete=models.CASCADE,
        db_column="predio_id",
        related_name="cuarteles",
    )
    nombre_cuartel = models.CharField(max_length=100)
    tipo_cultivo = models.CharField(max_length=100, blank=True, null=True)
    variedad = models.CharField(max_length=100, blank=True, null=True)
    forma_riego = models.CharField(max_length=50, choices=FORMA_RIEGO_CHOICES, blank=True, null=True)
    anio_plantacion = models.IntegerField(blank=True, null=True)
    superficie = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    estado = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = "cuarteles"
        ordering = ["-created_at", "-id"]
        verbose_name = "Cuartel"
        verbose_name_plural = "Cuarteles"

    def __str__(self):
        return f"{self.nombre_cuartel} ({self.predio.nombre_predio})"


class Riego(models.Model):
    cuartel = models.ForeignKey(
        Cuartel,
        models.DO_NOTHING,
        db_column="cuartel_id",
        related_name="riegos",
    )
    fecha_riego = models.DateField()
    tipo_riego = models.CharField(max_length=100, blank=True, null=True)
    horas_riego = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    caudal = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    estado = models.BooleanField(default=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "riego"
        ordering = ["-fecha_riego", "-created_at", "-id"]
        verbose_name = "Riego"
        verbose_name_plural = "Riegos"

    def __str__(self):
        return f"Riego {self.id} - {self.cuartel.nombre_cuartel}"


class Fertilizacion(models.Model):
    cuartel = models.ForeignKey(
        Cuartel,
        models.DO_NOTHING,
        db_column="cuartel_id",
        related_name="fertilizaciones",
    )
    fecha_aplicacion = models.DateField()
    producto = models.CharField(max_length=150, blank=True, null=True)
    dosis = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    unidad = models.CharField(max_length=50, blank=True, null=True)
    metodo_aplicacion = models.CharField(max_length=100, blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    estado = models.BooleanField(default=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "fertilizacion"
        ordering = ["-fecha_aplicacion", "-created_at", "-id"]
        verbose_name = "Fertilización"
        verbose_name_plural = "Fertilizaciones"

    def __str__(self):
        return f"Fertilización {self.id} - {self.cuartel.nombre_cuartel}"


class Cosecha(models.Model):
    CALIDAD_CHOICES = [
        ("excelente", "Excelente"),
        ("muy_buena", "Muy buena"),
        ("buena", "Buena"),
        ("regular", "Regular"),
        ("mala", "Mala"),
    ]

    DESTINO_CHOICES = [
        ("mercado", "Mercado"),
        ("venta_directa", "Venta directa"),
        ("procesamiento", "Procesamiento"),
        ("almacenamiento", "Almacenamiento"),
        ("otro", "Otro"),
    ]

    cuartel = models.ForeignKey(
        Cuartel,
        models.DO_NOTHING,
        db_column="cuartel_id",
        related_name="cosechas",
    )
    fecha_cosecha = models.DateField()
    tipo_cosecha = models.CharField(max_length=100, blank=True, null=True)
    cantidad_kg = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    cantidad_bins = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    calidad = models.CharField(max_length=50, choices=CALIDAD_CHOICES, blank=True, null=True)
    destino = models.CharField(max_length=100, choices=DESTINO_CHOICES, blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    estado = models.BooleanField(default=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "cosechas"
        ordering = ["-fecha_cosecha", "-created_at", "-id"]
        verbose_name = "Cosecha"
        verbose_name_plural = "Cosechas"

    def __str__(self):
        return f"Cosecha {self.id} - {self.cuartel.nombre_cuartel}"


class AplicacionQuimica(models.Model):
    cuartel = models.ForeignKey(
        Cuartel,
        models.DO_NOTHING,
        db_column="cuartel_id",
        related_name="aplicaciones_quimicas",
    )
    fecha_aplicacion = models.DateField()
    producto = models.CharField(max_length=150)
    tipo_producto = models.CharField(max_length=100, blank=True, null=True)
    dosis = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    unidad = models.CharField(max_length=50, blank=True, null=True)
    metodo_aplicacion = models.CharField(max_length=100, blank=True, null=True)
    responsable = models.CharField(max_length=120, blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    estado = models.BooleanField(blank=True, null=True, default=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "aplicaciones_quimicas"
        ordering = ["-fecha_aplicacion", "-created_at", "-id"]
        verbose_name = "Aplicación química"
        verbose_name_plural = "Aplicaciones químicas"

    def __str__(self):
        return f"Aplicación química {self.id} - {self.cuartel.nombre_cuartel}"


class LogActividad(models.Model):
    ACCION_CREAR = "CREAR"
    ACCION_EDITAR = "EDITAR"
    ACCION_ELIMINAR = "ELIMINAR"
    ACCION_LOGIN = "LOGIN"
    ACCION_LOGOUT = "LOGOUT"
    ACCION_CONSULTA = "CONSULTA"

    ACCIONES = [
        (ACCION_CREAR, "Crear"),
        (ACCION_EDITAR, "Editar"),
        (ACCION_ELIMINAR, "Eliminar"),
        (ACCION_LOGIN, "Iniciar sesión"),
        (ACCION_LOGOUT, "Cerrar sesión"),
        (ACCION_CONSULTA, "Consulta"),
    ]

    usuario = models.ForeignKey(
        Usuario,
        models.DO_NOTHING,
        db_column="usuario_id",
        related_name="logs_actividad",
    )
    accion = models.CharField(max_length=100, choices=ACCIONES)
    modulo = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    fecha = models.DateTimeField(blank=True, null=True, auto_now_add=True)

    class Meta:
        managed = False
        db_table = "logs_actividad"
        ordering = ["-fecha", "-id"]
        verbose_name = "Log de actividad"
        verbose_name_plural = "Logs de actividad"

    def __str__(self):
        return f"{self.usuario.usuario} - {self.modulo} - {self.accion}"

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError("Los logs de actividad no se pueden modificar.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Los logs de actividad no se pueden eliminar.")
