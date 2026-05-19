from django import forms
from django.contrib.auth.hashers import make_password

from .models import AplicacionQuimica, Cosecha, Cuartel, Fertilizacion, Predio, Riego, Usuario
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
        fields = ["usuario", "nombre_predio", "ubicacion", "superficie", "descripcion", "estado"]

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

    def clean_superficie(self):
        superficie = self.cleaned_data.get("superficie")
        if superficie is not None and superficie < 0:
            raise forms.ValidationError("La superficie no puede ser negativa.")
        return superficie


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
            "horas_riego",
            "caudal",
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

    def clean_horas_riego(self):
        horas = self.cleaned_data.get("horas_riego")
        if horas is not None and horas < 0:
            raise forms.ValidationError("Las horas de riego no pueden ser negativas.")
        return horas

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
