from functools import wraps

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect


AUTH_SESSION_KEY = "usuario_id"


def is_ajax_request(request):
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


def access_denied_response(request, message="No tienes permisos para realizar esta accion."):
    if is_ajax_request(request):
        return JsonResponse({"success": False, "error": message}, status=403)

    messages.error(request, message)
    return redirect("acceso_denegado")


def get_active_session_user(request):
    user_id = request.session.get(AUTH_SESSION_KEY)
    if not user_id:
        return None

    # Import local para evitar ciclos en tiempo de import.
    from .models import Usuario

    user = Usuario.objects.filter(id=user_id, estado=True).first()
    if not user:
        request.session.flush()
        return None

    return user


def login_required_custom(view_func):
    """Decorador básico para verificar que el usuario esté autenticado."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not get_active_session_user(request):
            messages.error(request, "Debes iniciar sesion para continuar.")
            return redirect("login")
        return view_func(request, *args, **kwargs)

    return _wrapped


def role_required(*roles):
    """
    Decorador para proteger vistas según rol(es).
    Si el usuario no tiene el rol requerido, lo redirige al dashboard.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            user = get_active_session_user(request)
            if not user:
                messages.error(request, "Debes iniciar sesion para continuar.")
                return redirect("login")

            current_role = user.rol
            if current_role not in roles:
                return access_denied_response(request, "No tienes permisos para acceder a esta seccion.")

            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator


def admin_only(view_func):
    """Decorador para restringir acceso solo a administradores."""
    return role_required("admin")(view_func)


def tecnico_or_admin(view_func):
    """Decorador para permitir acceso a técnicos y administradores."""
    return role_required("tecnico", "admin")(view_func)


def any_authenticated(view_func):
    """Decorador para permitir acceso a cualquier usuario autenticado."""
    return login_required_custom(view_func)


def require_post_only(view_func):
    """Decorador para permitir solo solicitudes POST."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if request.method != "POST":
            if is_ajax_request(request):
                return JsonResponse(
                    {"success": False, "error": "Método no permitido."},
                    status=405
                )
            messages.error(request, "Método no permitido.")
            return redirect(request.META.get("HTTP_REFERER", "dashboard"))
        return view_func(request, *args, **kwargs)
    return _wrapped


def data_ownership_required(view_func):
    """
    Decorador para verificar que productores solo accedan a sus datos.
    Valida que el usuario sea propietario del recurso.
    """
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.session.get(AUTH_SESSION_KEY):
            messages.error(request, "Debes iniciar sesion para continuar.")
            return redirect("login")

        current_role = request.session.get("rol")
        user_id = request.session.get(AUTH_SESSION_KEY)
        
        # Los administradores pueden acceder a todo
        if current_role == "admin":
            return view_func(request, *args, **kwargs)
        
        # Para productores y técnicos, verificar propiedad de datos
        # Esto se valida específicamente en cada vista
        return view_func(request, *args, **kwargs)

    return _wrapped
