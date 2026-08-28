from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone


class CreatedAtMixin:
    def save(self, *args, **kwargs):
        if self._state.adding and self.created_at is None:
            self.created_at = timezone.now()
        super().save(*args, **kwargs)


class Usuario(models.Model):
    ROL_ADMIN = "admin"
    ROL_TECNICO = "tecnico"
    ROL_PRODUCTOR = "productor"

    ROLE_CHOICES = [
        (ROL_ADMIN, "Administrador"),
        (ROL_TECNICO, "PRODESAL"),
        (ROL_PRODUCTOR, "Productor"),
    ]

    SECTOR_CHOICES = [
        ("Zaino", "Zaino"),
        ("Jahuelito", "Jahuelito"),
        ("Santa Filomena", "Santa Filomena"),
        ("El Llano", "El Llano"),
        ("Tabolango", "Tabolango"),
        ("Lo Galdames", "Lo Galdames"),
    ]

    rut = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=100)
    usuario = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=255)
    rol = models.CharField(max_length=20, choices=ROLE_CHOICES)
    celular = models.CharField(max_length=20, blank=True)
    sector = models.CharField(max_length=100, blank=True, choices=SECTOR_CHOICES)
    estado = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "usuarios"
        ordering = ["-created_at"]
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        return f"{self.nombre} ({self.usuario})"


class Predio(CreatedAtMixin, models.Model):
    usuario = models.ForeignKey(
        Usuario,
        models.DO_NOTHING,
        db_column="usuario_id",
        related_name="predios",
    )
    nombre_predio = models.CharField(max_length=100)
    ubicacion = models.CharField(max_length=150, blank=True, null=True)
    superficie = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    superficie_hectareas = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    inscripcion_cbr = models.CharField(max_length=255, blank=True, null=True)
    inscripcion_agua = models.TextField(blank=True, null=True)
    geolocalizacion_lat = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    geolocalizacion_lng = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
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


class Cuartel(CreatedAtMixin, models.Model):
    TIPO_PLANTACION_CHOICES = [
        ("olivo", "Olivo"),
        ("durazno", "Durazno"),
        ("damasco", "Damasco"),
        ("tunales", "Tunales"),
        ("higueras", "Higueras"),
        ("otros", "Otros"),
    ]

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
    tipo_cultivo = models.CharField(max_length=100, blank=True, null=True, choices=TIPO_PLANTACION_CHOICES)
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


class Riego(CreatedAtMixin, models.Model):
    TIPO_RIEGO_CHOICES = [
        ("goteo", "Goteo"),
        ("tendido_taza", "Tendido (x taza)"),
        ("aspersion", "Aspersión"),
    ]

    cuartel = models.ForeignKey(
        Cuartel,
        models.DO_NOTHING,
        db_column="cuartel_id",
        related_name="riegos",
    )
    fecha_riego = models.DateField()
    tipo_riego = models.CharField(max_length=100, blank=True, null=True, choices=TIPO_RIEGO_CHOICES)
    horas_riego = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    minutos_riego = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
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


class Fertilizacion(CreatedAtMixin, models.Model):
    PRODUCTO_CHOICES = [
        ("urea", "Urea"),
        ("mezcla", "Mezcla"),
        ("nitrato_potasio", "Nitrato Potasio"),
        ("otro", "Otro"),
    ]

    cuartel = models.ForeignKey(
        Cuartel,
        models.DO_NOTHING,
        db_column="cuartel_id",
        related_name="fertilizaciones",
    )
    fecha_aplicacion = models.DateField()
    producto = models.CharField(max_length=150, blank=True, null=True, choices=PRODUCTO_CHOICES)
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


class Cosecha(CreatedAtMixin, models.Model):
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


class AplicacionQuimica(CreatedAtMixin, models.Model):
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


class LaborAgricola(CreatedAtMixin, models.Model):
    TIPO_LABOR_CHOICES = [
        ("poda", "Poda"),
        ("brote", "Brote"),
        ("limpieza", "Limpieza"),
        ("mantencion", "Mantención"),
        ("revision", "Revisión"),
        ("otro", "Otro"),
    ]

    usuario = models.ForeignKey(
        Usuario,
        models.DO_NOTHING,
        db_column="usuario_id",
        related_name="labores_agricolas",
    )
    predio = models.ForeignKey(
        Predio,
        models.DO_NOTHING,
        db_column="predio_id",
        related_name="labores_agricolas",
    )
    cuartel = models.ForeignKey(
        Cuartel,
        models.DO_NOTHING,
        db_column="cuartel_id",
        related_name="labores_agricolas",
    )
    fecha = models.DateField()
    tipo_labor = models.CharField(max_length=50, choices=TIPO_LABOR_CHOICES)
    subtipo = models.CharField(max_length=80, blank=True, null=True)
    responsable = models.CharField(max_length=120, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    estado = models.BooleanField(default=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = "labores_agricolas"
        ordering = ["-fecha", "-created_at", "-id"]
        verbose_name = "Labor agrícola"
        verbose_name_plural = "Labores agrícolas"

    def __str__(self):
        return f"{self.get_tipo_labor_display()} - {self.cuartel.nombre_cuartel} ({self.fecha})"


class ComentarioTecnico(models.Model):
    MODULO_CHOICES = [
        ("predio", "Predio"),
        ("cuartel", "Cuartel"),
        ("riego", "Riego"),
        ("fertilizacion", "Fertilización"),
        ("cosecha", "Cosecha"),
        ("aplicacion_quimica", "Aplicación química"),
        ("labor_agricola", "Labor agrícola"),
    ]

    usuario_prodesal = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name="comentarios_realizados",
    )
    productor = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name="comentarios_recibidos",
    )
    modulo = models.CharField(max_length=30, choices=MODULO_CHOICES)
    objeto_id = models.PositiveIntegerField()
    comentario = models.TextField()
    leido = models.BooleanField(default=False)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "comentarios_tecnicos"
        ordering = ["-fecha", "-id"]
        verbose_name = "Comentario técnico"
        verbose_name_plural = "Comentarios técnicos"

    def __str__(self):
        return f"Observación de {self.usuario_prodesal.nombre} sobre {self.modulo} #{self.objeto_id}"


class Notificacion(models.Model):
    usuario_generador = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name="notificaciones_enviadas",
    )
    productor = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name="notificaciones_recibidas",
    )
    titulo = models.CharField(max_length=150)
    mensaje = models.TextField()
    modulo = models.CharField(max_length=30, choices=ComentarioTecnico.MODULO_CHOICES, blank=True, null=True)
    objeto_id = models.PositiveIntegerField(blank=True, null=True)
    leido = models.BooleanField(default=False)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notificaciones"
        ordering = ["-fecha", "-id"]
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"

    def __str__(self):
        return f"{self.titulo} -> {self.productor.nombre}"

