from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path


def root_redirect(request):
    return redirect("dashboard")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", root_redirect, name="root"),
    path("", include("usuarios.urls")),
]
