from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


AUTH_SESSION_KEY = "usuario_id"


def login_required_custom(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.session.get(AUTH_SESSION_KEY):
            messages.error(request, "Debes iniciar sesion para continuar.")
            return redirect("login")
        return view_func(request, *args, **kwargs)

    return _wrapped


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.session.get(AUTH_SESSION_KEY):
                messages.error(request, "Debes iniciar sesion para continuar.")
                return redirect("login")

            current_role = request.session.get("rol")
            if current_role not in roles:
                messages.error(request, "No tienes permisos para acceder a esta seccion.")
                return redirect("dashboard")

            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator
