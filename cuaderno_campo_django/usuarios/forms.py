from django import forms
from django.contrib.auth.hashers import make_password

from .models import (
    AplicacionQuimica,
    ComentarioTecnico,
    Cosecha,
    Cuartel,
    Fertilizacion,
    LaborAgricola,
    Notificacion,
    Predio,
    Riego,
    Usuario,
)
from .permissions import get_form_cuarteles_queryset, get_form_predios_queryset


class EstadoCheckboxMixin:
    def clean_estado(self):
        raw_value = self.data.get("estado")
        if raw_value is None:
            return False

        normalized = str(raw_value).strip().lower()
        return normalized not in {"", "0", "false", "off", "none", "null"}


class LoginForm(forms.Form):
    usuario = forms.CharField(max_length=50, label="Usuario")
    password = forms.CharField(widget=forms.PasswordInput, label="Contrasena")


class UsuarioCreateForm(EstadoCheckboxMixin, forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Contrasena", min_length=6)

    class Meta:
        model = Usuario
        fields = ["rut", "nombre", "usuario", "password", "rol", "celular", "sector", "estado"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["sector"].required = False
        self.fields["sector"].widget = forms.Select(
            choices=[("", "Selecciona un sector")] + list(Usuario.SECTOR_CHOICES)
        )

    def clean(self):
        cleaned_data = super().clean()
        usuario = cleaned_data.get("usuario")
        rut = cleaned_data.get("rut")

        if usuario and Usuario.objects.filter(usuario=usuario).exists():
            self.add_error("usuario", "Este nombre de usuario ya existe.")

        if rut and Usuario.objects.filter(rut=rut).exists():
            self.add_error("rut", "Este RUT ya existe.")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.password = make_password(self.cleaned_data["password"])
        if commit:
            instance.save()
        return instance


class UsuarioUpdateForm(EstadoCheckboxMixin, forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput,
        label="Nueva contrasena",
        required=False,
        help_text="Deja en blanco para mantener la contrasena actual.",
    )

    class Meta:
        model = Usuario
        fields = ["rut", "nombre", "usuario", "rol", "celular", "sector", "estado"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["sector"].required = False
        self.fields["sector"].widget = forms.Select(
            choices=[("", "Selecciona un sector")] + list(Usuario.SECTOR_CHOICES)
        )

    def clean(self):
        cleaned_data = super().clean()
        usuario = cleaned_data.get("usuario")
        rut = cleaned_data.get("rut")
        password = cleaned_data.get("password")

        qs = Usuario.objects.exclude(pk=self.instance.pk)

        if usuario and qs.filter(usuario=usuario).exists():
            self.add_error("usuario", "Este nombre de usuario ya existe.")

        if rut and qs.filter(rut=rut).exists():
            self.add_error("rut", "Este RUT ya existe.")

        if password and len(password) < 6:
            self.add_error("password", "La contrasena debe tener al menos 6 caracteres.")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        password = self.cleaned_data.get("password")
        if password:
            instance.password = make_password(password)
        if commit:
            instance.save()
        return instance


class UsuarioChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f"{obj.nombre} ({obj.usuario})"


class PredioBaseForm(EstadoCheckboxMixin, forms.ModelForm):
    usuario = UsuarioChoiceField(
        queryset=Usuario.objects.filter(estado=True).order_by("nombre"),
        empty_label="Selecciona un usuario",
    )

    class Meta:
        model = Predio
        fields = [
            "usuario",
            "nombre_predio",
            "ubicacion",
            "superficie_hectareas",
            "inscripcion_cbr",
            "inscripcion_agua",
            "geolocalizacion_lat",
            "geolocalizacion_lng",
            "descripcion",
            "estado",
        ]

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        queryset = Usuario.objects.filter(estado=True).order_by("nombre")
        if self.request and self.request.session.get("rol") == Usuario.ROL_PRODUCTOR:
            user_id = self.request.session.get("usuario_id")
            queryset = queryset.filter(id=user_id)
            self.fields["usuario"].empty_label = None
            if user_id:
                self.fields["usuario"].initial = user_id

        self.fields["usuario"].queryset = queryset

    def clean_usuario(self):
        usuario = self.cleaned_data.get("usuario")

        if self.request and self.request.session.get("rol") == Usuario.ROL_PRODUCTOR:
            user_id = self.request.session.get("usuario_id")
            if not usuario or usuario.id != user_id:
                raise forms.ValidationError("Solo puedes asociar predios a tu propio usuario.")

        return usuario

    def clean_nombre_predio(self):
        nombre_predio = (self.cleaned_data.get("nombre_predio") or "").strip()
        if not nombre_predio:
            raise forms.ValidationError("El nombre del predio es obligatorio.")
        return nombre_predio

    def clean_superficie_hectareas(self):
        superficie = self.cleaned_data.get("superficie_hectareas")
        if superficie is not None and superficie < 0:
            raise forms.ValidationError("La superficie por hectárea no puede ser negativa.")
        return superficie

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.superficie = self.cleaned_data.get("superficie_hectareas")
        if commit:
            instance.save()
        return instance


class PredioCreateForm(PredioBaseForm):
    pass


class PredioUpdateForm(PredioBaseForm):
    pass


class PredioChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.nombre_predio


class CuartelBaseForm(EstadoCheckboxMixin, forms.ModelForm):
    predio = PredioChoiceField(
        queryset=Predio.objects.filter(estado=True).order_by("nombre_predio"),
        empty_label="Selecciona un predio",
    )

    class Meta:
        model = Cuartel
        fields = [
            "predio",
            "nombre_cuartel",
            "tipo_cultivo",
            "variedad",
            "forma_riego",
            "anio_plantacion",
            "superficie",
            "descripcion",
            "estado",
        ]

    def __init__(self, *args, **kwargs):
        request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)
        if request:
            self.fields["predio"].queryset = get_form_predios_queryset(request)

        choices = [("", "Selecciona tipo de plantación")]
        choices.extend(Cuartel.TIPO_PLANTACION_CHOICES)

        current_value = (self.instance.tipo_cultivo if self.instance and self.instance.pk else None) or ""
        if current_value and current_value not in {value for value, _ in Cuartel.TIPO_PLANTACION_CHOICES}:
            choices.append((current_value, current_value))

        self.fields["tipo_cultivo"].required = False
        self.fields["tipo_cultivo"].widget = forms.Select(choices=choices)
        self.fields["tipo_cultivo"].label = "Tipo de Plantación"

    def clean_nombre_cuartel(self):
        nombre = (self.cleaned_data.get("nombre_cuartel") or "").strip()
        if not nombre:
            raise forms.ValidationError("El nombre del cuartel es obligatorio.")
        return nombre

    def clean_superficie(self):
        superficie = self.cleaned_data.get("superficie")
        if superficie is not None and superficie < 0:
            raise forms.ValidationError("La superficie no puede ser negativa.")
        return superficie

    def clean_anio_plantacion(self):
        anio = self.cleaned_data.get("anio_plantacion")
        if anio is not None and (anio < 1900 or anio > 2100):
            raise forms.ValidationError("Año de plantación inválido.")
        return anio


class CuartelCreateForm(CuartelBaseForm):
    pass


class CuartelUpdateForm(CuartelBaseForm):
    pass


class CuartelRiegoChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f"{obj.nombre_cuartel} ({obj.predio.nombre_predio})"


class RiegoBaseForm(EstadoCheckboxMixin, forms.ModelForm):
    predio = PredioChoiceField(
        queryset=Predio.objects.filter(estado=True).order_by("nombre_predio"),
        empty_label="Selecciona un predio",
    )
    cuartel = CuartelRiegoChoiceField(
        queryset=Cuartel.objects.select_related("predio")
        .filter(estado=True, predio__estado=True)
        .order_by("predio__nombre_predio", "nombre_cuartel"),
        empty_label="Selecciona un cuartel",
    )

    class Meta:
        model = Riego
        fields = [
            "cuartel",
            "fecha_riego",
            "tipo_riego",
            "minutos_riego",
            "caudal",
            "observaciones",
            "estado",
        ]

    def __init__(self, *args, **kwargs):
        request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        if request:
            self.fields["predio"].queryset = get_form_predios_queryset(request)

        tipo_choices = [("", "Selecciona tipo de riego")] + list(Riego.TIPO_RIEGO_CHOICES)
        current_tipo = (self.instance.tipo_riego if self.instance and self.instance.pk else None) or ""
        if current_tipo and current_tipo not in {value for value, _ in Riego.TIPO_RIEGO_CHOICES}:
            tipo_choices.append((current_tipo, current_tipo))
        self.fields["tipo_riego"].required = False
        self.fields["tipo_riego"].widget = forms.Select(choices=tipo_choices)

        predio_id = None
        if self.is_bound:
            predio_id = self.data.get("predio")
        elif self.instance and self.instance.pk:
            predio_id = self.instance.cuartel.predio_id
            self.fields["predio"].initial = predio_id

        if request:
            self.fields["cuartel"].queryset = get_form_cuarteles_queryset(request, predio_id)
        else:
            queryset = Cuartel.objects.select_related("predio").filter(estado=True, predio__estado=True)
            if predio_id:
                queryset = queryset.filter(predio_id=predio_id)
            self.fields["cuartel"].queryset = queryset.order_by("nombre_cuartel")

    def clean(self):
        cleaned_data = super().clean()
        predio = cleaned_data.get("predio")
        cuartel = cleaned_data.get("cuartel")

        if predio and cuartel and cuartel.predio_id != predio.id:
            self.add_error("cuartel", "El cuartel seleccionado no pertenece al predio indicado.")

        return cleaned_data

    def clean_minutos_riego(self):
        minutos = self.cleaned_data.get("minutos_riego")
        if minutos is not None and minutos < 0:
            raise forms.ValidationError("Los minutos de riego no pueden ser negativos.")
        return minutos

    def save(self, commit=True):
        instance = super().save(commit=False)
        minutos = self.cleaned_data.get("minutos_riego")
        instance.horas_riego = (minutos / 60) if minutos is not None else None
        if commit:
            instance.save()
        return instance

    def clean_caudal(self):
        caudal = self.cleaned_data.get("caudal")
        if caudal is not None and caudal < 0:
            raise forms.ValidationError("El caudal no puede ser negativo.")
        return caudal


class RiegoCreateForm(RiegoBaseForm):
    pass


class RiegoUpdateForm(RiegoBaseForm):
    pass


class FertilizacionBaseForm(EstadoCheckboxMixin, forms.ModelForm):
    predio = PredioChoiceField(
        queryset=Predio.objects.filter(estado=True).order_by("nombre_predio"),
        empty_label="Selecciona un predio",
    )
    cuartel = CuartelRiegoChoiceField(
        queryset=Cuartel.objects.select_related("predio")
        .filter(estado=True, predio__estado=True)
        .order_by("predio__nombre_predio", "nombre_cuartel"),
        empty_label="Selecciona un cuartel",
    )

    class Meta:
        model = Fertilizacion
        fields = [
            "cuartel",
            "fecha_aplicacion",
            "producto",
            "dosis",
            "unidad",
            "metodo_aplicacion",
            "observaciones",
            "estado",
        ]

    def __init__(self, *args, **kwargs):
        request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        product_choices = [("", "Selecciona un producto")] + list(Fertilizacion.PRODUCTO_CHOICES)
        current_producto = (self.instance.producto if self.instance and self.instance.pk else None) or ""
        if current_producto and current_producto not in {value for value, _ in Fertilizacion.PRODUCTO_CHOICES}:
            product_choices.append((current_producto, current_producto))
        self.fields["producto"].required = False
        self.fields["producto"].widget = forms.Select(choices=product_choices)

        if request:
            self.fields["predio"].queryset = get_form_predios_queryset(request)

        predio_id = None
        if self.is_bound:
            predio_id = self.data.get("predio")
        elif self.instance and self.instance.pk:
            predio_id = self.instance.cuartel.predio_id
            self.fields["predio"].initial = predio_id

        if request:
            self.fields["cuartel"].queryset = get_form_cuarteles_queryset(request, predio_id)
        else:
            queryset = Cuartel.objects.select_related("predio").filter(estado=True, predio__estado=True)
            if predio_id:
                queryset = queryset.filter(predio_id=predio_id)
            self.fields["cuartel"].queryset = queryset.order_by("nombre_cuartel")

    def clean(self):
        cleaned_data = super().clean()
        predio = cleaned_data.get("predio")
        cuartel = cleaned_data.get("cuartel")

        if predio and cuartel and cuartel.predio_id != predio.id:
            self.add_error("cuartel", "El cuartel seleccionado no pertenece al predio indicado.")

        return cleaned_data

    def clean_dosis(self):
        dosis = self.cleaned_data.get("dosis")
        if dosis is not None and dosis < 0:
            raise forms.ValidationError("La dosis no puede ser negativa.")
        return dosis


class FertilizacionCreateForm(FertilizacionBaseForm):
    pass


class FertilizacionUpdateForm(FertilizacionBaseForm):
    pass


class CosechaBaseForm(EstadoCheckboxMixin, forms.ModelForm):
    predio = PredioChoiceField(
        queryset=Predio.objects.filter(estado=True).order_by("nombre_predio"),
        empty_label="Selecciona un predio",
    )
    cuartel = CuartelRiegoChoiceField(
        queryset=Cuartel.objects.select_related("predio")
        .filter(estado=True, predio__estado=True)
        .order_by("predio__nombre_predio", "nombre_cuartel"),
        empty_label="Selecciona un cuartel",
    )

    class Meta:
        model = Cosecha
        fields = [
            "cuartel",
            "fecha_cosecha",
            "tipo_cosecha",
            "cantidad_kg",
            "cantidad_bins",
            "calidad",
            "destino",
            "observaciones",
            "estado",
        ]

    def __init__(self, *args, **kwargs):
        request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        if request:
            self.fields["predio"].queryset = get_form_predios_queryset(request)

        predio_id = None
        if self.is_bound:
            predio_id = self.data.get("predio")
        elif self.instance and self.instance.pk:
            predio_id = self.instance.cuartel.predio_id
            self.fields["predio"].initial = predio_id

        if request:
            self.fields["cuartel"].queryset = get_form_cuarteles_queryset(request, predio_id)
        else:
            queryset = Cuartel.objects.select_related("predio").filter(estado=True, predio__estado=True)
            if predio_id:
                queryset = queryset.filter(predio_id=predio_id)
            self.fields["cuartel"].queryset = queryset.order_by("nombre_cuartel")

    def clean(self):
        cleaned_data = super().clean()
        predio = cleaned_data.get("predio")
        cuartel = cleaned_data.get("cuartel")

        if predio and cuartel and cuartel.predio_id != predio.id:
            self.add_error("cuartel", "El cuartel seleccionado no pertenece al predio indicado.")

        return cleaned_data

    def clean_cantidad_kg(self):
        cantidad_kg = self.cleaned_data.get("cantidad_kg")
        if cantidad_kg is not None and cantidad_kg < 0:
            raise forms.ValidationError("La cantidad en KG no puede ser negativa.")
        return cantidad_kg

    def clean_cantidad_bins(self):
        cantidad_bins = self.cleaned_data.get("cantidad_bins")
        if cantidad_bins is not None and cantidad_bins < 0:
            raise forms.ValidationError("La cantidad de bins no puede ser negativa.")
        return cantidad_bins


class CosechaCreateForm(CosechaBaseForm):
    pass


class CosechaUpdateForm(CosechaBaseForm):
    pass


class AplicacionQuimicaBaseForm(EstadoCheckboxMixin, forms.ModelForm):
    predio = PredioChoiceField(
        queryset=Predio.objects.filter(estado=True).order_by("nombre_predio"),
        empty_label="Selecciona un predio",
    )
    cuartel = CuartelRiegoChoiceField(
        queryset=Cuartel.objects.select_related("predio")
        .filter(estado=True, predio__estado=True)
        .order_by("predio__nombre_predio", "nombre_cuartel"),
        empty_label="Selecciona un cuartel",
    )

    class Meta:
        model = AplicacionQuimica
        fields = [
            "cuartel",
            "fecha_aplicacion",
            "producto",
            "tipo_producto",
            "dosis",
            "unidad",
            "metodo_aplicacion",
            "responsable",
            "observaciones",
            "estado",
        ]

    def __init__(self, *args, **kwargs):
        request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        if request:
            self.fields["predio"].queryset = get_form_predios_queryset(request)

        predio_id = None
        if self.is_bound:
            predio_id = self.data.get("predio")
        elif self.instance and self.instance.pk:
            predio_id = self.instance.cuartel.predio_id
            self.fields["predio"].initial = predio_id

        if request:
            self.fields["cuartel"].queryset = get_form_cuarteles_queryset(request, predio_id)
        else:
            queryset = Cuartel.objects.select_related("predio").filter(estado=True, predio__estado=True)
            if predio_id:
                queryset = queryset.filter(predio_id=predio_id)
            self.fields["cuartel"].queryset = queryset.order_by("nombre_cuartel")

    def clean(self):
        cleaned_data = super().clean()
        predio = cleaned_data.get("predio")
        cuartel = cleaned_data.get("cuartel")

        if predio and cuartel and cuartel.predio_id != predio.id:
            self.add_error("cuartel", "El cuartel seleccionado no pertenece al predio indicado.")

        return cleaned_data

    def clean_producto(self):
        producto = (self.cleaned_data.get("producto") or "").strip()
        if not producto:
            raise forms.ValidationError("El producto es obligatorio.")
        return producto

    def clean_dosis(self):
        dosis = self.cleaned_data.get("dosis")
        if dosis is not None and dosis < 0:
            raise forms.ValidationError("La dosis no puede ser negativa.")
        return dosis


class AplicacionQuimicaCreateForm(AplicacionQuimicaBaseForm):
    pass


class AplicacionQuimicaUpdateForm(AplicacionQuimicaBaseForm):
    pass


class LaborAgricolaBaseForm(EstadoCheckboxMixin, forms.ModelForm):
    predio = PredioChoiceField(
        queryset=Predio.objects.filter(estado=True).order_by("nombre_predio"),
        empty_label="Selecciona un predio",
    )
    cuartel = CuartelRiegoChoiceField(
        queryset=Cuartel.objects.select_related("predio")
        .filter(estado=True, predio__estado=True)
        .order_by("predio__nombre_predio", "nombre_cuartel"),
        empty_label="Selecciona un cuartel",
    )

    class Meta:
        model = LaborAgricola
        fields = [
            "predio",
            "cuartel",
            "fecha",
            "tipo_labor",
            "subtipo",
            "responsable",
            "descripcion",
            "observaciones",
            "estado",
        ]

    def __init__(self, *args, **kwargs):
        request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

        tipo_choices = [("", "Selecciona tipo de labor")] + list(LaborAgricola.TIPO_LABOR_CHOICES)
        self.fields["tipo_labor"].widget = forms.Select(choices=tipo_choices)

        if request:
            self.fields["predio"].queryset = get_form_predios_queryset(request)

        predio_id = None
        if self.is_bound:
            predio_id = self.data.get("predio")
        elif self.instance and self.instance.pk:
            predio_id = self.instance.cuartel.predio_id
            self.fields["predio"].initial = predio_id

        if request:
            self.fields["cuartel"].queryset = get_form_cuarteles_queryset(request, predio_id)

    def clean(self):
        cleaned_data = super().clean()
        predio = cleaned_data.get("predio")
        cuartel = cleaned_data.get("cuartel")
        tipo_labor = (cleaned_data.get("tipo_labor") or "").strip()
        subtipo = (cleaned_data.get("subtipo") or "").strip()

        if predio and cuartel and cuartel.predio_id != predio.id:
            self.add_error("cuartel", "El cuartel seleccionado no pertenece al predio indicado.")

        if tipo_labor in {"poda", "brote"} and not subtipo:
            self.add_error("subtipo", "El subtipo es obligatorio para el tipo de labor seleccionado.")

        return cleaned_data


class LaborAgricolaCreateForm(LaborAgricolaBaseForm):
    pass


class LaborAgricolaUpdateForm(LaborAgricolaBaseForm):
    pass


class ComentarioTecnicoForm(forms.ModelForm):
    class Meta:
        model = ComentarioTecnico
        fields = ["comentario"]
        widgets = {
            "comentario": forms.Textarea(attrs={"rows": 4}),
        }

    def clean_comentario(self):
        comentario = self.cleaned_data["comentario"].strip()
        if not comentario:
            raise forms.ValidationError("El comentario no puede estar vacío.")
        return comentario


class NotificacionForm(forms.ModelForm):
    class Meta:
        model = Notificacion
        fields = ["titulo", "mensaje"]

    def clean_titulo(self):
        titulo = self.cleaned_data["titulo"].strip()
        if not titulo:
            raise forms.ValidationError("El título es obligatorio.")
        return titulo

    def clean_mensaje(self):
        mensaje = self.cleaned_data["mensaje"].strip()
        if not mensaje:
            raise forms.ValidationError("El mensaje es obligatorio.")
        return mensaje
