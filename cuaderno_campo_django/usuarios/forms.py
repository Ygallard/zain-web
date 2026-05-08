from django import forms
from django.contrib.auth.hashers import make_password

from .models import Usuario


class LoginForm(forms.Form):
    usuario = forms.CharField(max_length=50, label="Usuario")
    password = forms.CharField(widget=forms.PasswordInput, label="Contrasena")


class UsuarioCreateForm(forms.ModelForm):
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


class UsuarioUpdateForm(forms.ModelForm):
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
