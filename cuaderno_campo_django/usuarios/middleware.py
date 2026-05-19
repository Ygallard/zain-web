"""
Middleware para proteccion de acceso URL segun rol.
Bloquea acceso manual a rutas sensibles segun permisos backend.
"""

from django.shortcuts import redirect
from django.contrib import messages

from .audit import clear_current_request, set_current_request
from .decorators import AUTH_SESSION_KEY
from .models import Usuario


class RoleBasedAccessMiddleware:
    """
    Middleware que valida acceso a URLs según el rol del usuario.
    Previene que productores accedan a áreas restringidas.
    """
    
    ADMIN_ONLY_PREFIXES = (
        "/usuarios/",
        "/auditoria/",
        "/admin/",
    )
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        set_current_request(request)
        try:
            user_id = request.session.get(AUTH_SESSION_KEY)
            if user_id:
                user = Usuario.objects.filter(id=user_id, estado=True).only("id", "rol").first()
                if not user:
                    request.session.flush()
                    messages.error(request, "Tu sesion no es valida. Vuelve a iniciar sesion.")
                    return redirect("login")

                request.session["rol"] = user.rol

                if self._should_deny_access(request.path, user.rol):
                    messages.error(request, "No tienes permisos para acceder a esta área.")
                    return redirect("acceso_denegado")

            response = self.get_response(request)
            return response
        finally:
            clear_current_request()
    
    def _should_deny_access(self, path, rol):
        """Determina si se debe denegar acceso a la ruta manual."""
        if rol == Usuario.ROL_ADMIN:
            return False

        for prefix in self.ADMIN_ONLY_PREFIXES:
            if path.startswith(prefix):
                return True

        return False
