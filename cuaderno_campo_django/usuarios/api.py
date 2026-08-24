"""
API endpoints para autenticación centralizada.
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import check_password
from django.shortcuts import redirect
import logging
import json
import hmac
import hashlib
from datetime import datetime, timedelta
from .audit import IMPORTANT_AUDIT_ACTIONS, registrar_auditoria
from .models import LogActividad, Usuario
from django.conf import settings
from .decorators import AUTH_SESSION_KEY
from .services.weather_service import WeatherService


logger = logging.getLogger(__name__)

# Token cache - en producción usar Redis
TOKEN_CACHE = {}


def generate_auth_token(user_id, username, rol):
    """Genera un token de autenticación para la sesión"""
    timestamp = datetime.now().isoformat()
    token_data = f"{user_id}:{username}:{rol}:{timestamp}"
    token = hmac.new(
        settings.SECRET_KEY.encode(),
        token_data.encode(),
        hashlib.sha256
    ).hexdigest()
    
    TOKEN_CACHE[token] = {
        'user_id': user_id,
        'username': username,
        'rol': rol,
        'created_at': timestamp,
        'expires_at': (datetime.now() + timedelta(hours=24)).isoformat()
    }
    return token


def validate_auth_token(token):
    """Valida un token y retorna los datos del usuario si es válido"""
    if token not in TOKEN_CACHE:
        return None
    
    token_data = TOKEN_CACHE[token]
    expires_at = datetime.fromisoformat(token_data['expires_at'])
    
    if datetime.now() > expires_at:
        del TOKEN_CACHE[token]
        return None
    
    return token_data


def get_token_from_request(request):
    """Extrae el token de la solicitud"""
    # Primero desde header Authorization
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if auth_header.startswith('Bearer '):
        return auth_header[7:]
    
    # O desde cookie
    return request.COOKIES.get('auth_token')


@csrf_exempt
@require_http_methods(["POST"])
def auth_login(request):
    """
    Endpoint de login centralizado
    
    POST /api/auth/login/
    Body: {"username": "...", "password": "..."}
    
    Retorna: {
        "success": true/false,
        "token": "...",
        "user": {
            "id": 1,
            "username": "admin",
            "nombre": "Administrador",
            "rol": "admin"
        }
    }
    """
    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        data = {}
    
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''
    
    if not username or not password:
        return JsonResponse({
            'success': False,
            'error': 'Usuario y contraseña son requeridos'
        }, status=400)
    
    # Buscar usuario en BD
    try:
        usuario = Usuario.objects.get(usuario=username, estado=True)
    except Usuario.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Usuario o contraseña inválidos'
        }, status=401)
    
    # Validar contraseña (asumiendo que está hasheada)
    # Si las contraseñas están en texto plano, comparar directamente
    password_valid = False
    
    # Intentar validar como hash
    if usuario.password.startswith('pbkdf2_sha256$') or usuario.password.startswith('sha1$'):
        password_valid = check_password(password, usuario.password)
    else:
        # Comparar como texto plano
        password_valid = (password == usuario.password)
    
    if not password_valid:
        return JsonResponse({
            'success': False,
            'error': 'Usuario o contraseña inválidos'
        }, status=401)
    
    # Generar token
    token = generate_auth_token(usuario.id, usuario.usuario, usuario.rol)
    
    # Preparar respuesta
    response_data = {
        'success': True,
        'token': token,
        'user': {
            'id': usuario.id,
            'username': usuario.usuario,
            'nombre': usuario.nombre,
            'rol': usuario.rol,
            'rut': usuario.rut
        }
    }
    
    response = JsonResponse(response_data)
    response.set_cookie(
        'auth_token',
        token,
        max_age=86400,  # 24 horas
        httponly=True,
        samesite='Lax'
    )

    registrar_auditoria(
        usuario,
        LogActividad.ACCION_LOGIN,
        "autenticacion",
        f"{usuario.nombre} inicio sesion via autenticacion centralizada.",
    )

    return response


@require_http_methods(["GET"])
def auth_validate(request):
    """
    Valida un token de autenticación
    
    GET /api/auth/validate/?token=...
    o Header: Authorization: Bearer <token>
    
    Retorna: {
        "valid": true/false,
        "user": {...}  # si válido
    }
    """
    token = get_token_from_request(request) or request.GET.get('token', '')
    
    if not token:
        return JsonResponse({
            'valid': False,
            'error': 'Token requerido'
        }, status=400)
    
    token_data = validate_auth_token(token)
    
    if not token_data:
        return JsonResponse({
            'valid': False,
            'error': 'Token inválido o expirado'
        }, status=401)
    
    return JsonResponse({
        'valid': True,
        'user': {
            'id': token_data['user_id'],
            'username': token_data['username'],
            'rol': token_data['rol']
        }
    })


@require_http_methods(["GET"])
def auth_user_info(request):
    """
    Obtiene información del usuario autenticado
    
    GET /api/auth/user-info/
    Header: Authorization: Bearer <token>
    
    Retorna: {
        "user": {
            "id": 1,
            "username": "admin",
            "nombre": "Admin User",
            "rol": "admin",
            "rut": "12345678-9"
        }
    }
    """
    token = get_token_from_request(request)
    
    if not token:
        return JsonResponse({
            'error': 'Token requerido'
        }, status=401)
    
    token_data = validate_auth_token(token)
    
    if not token_data:
        return JsonResponse({
            'error': 'Token inválido o expirado'
        }, status=401)
    
    # Obtener datos completos del usuario
    try:
        usuario = Usuario.objects.get(id=token_data['user_id'])
        return JsonResponse({
            'user': {
                'id': usuario.id,
                'username': usuario.usuario,
                'nombre': usuario.nombre,
                'rol': usuario.rol,
                'rut': usuario.rut,
                'celular': usuario.celular,
                'sector': usuario.sector
            }
        })
    except Usuario.DoesNotExist:
        return JsonResponse({
            'error': 'Usuario no encontrado'
        }, status=404)


@csrf_exempt
@require_http_methods(["POST"])
def auth_logout(request):
    """
    Invalida un token

    POST /api/auth/logout/
    Header: Authorization: Bearer <token>
    """
    token = get_token_from_request(request)
    token_data = validate_auth_token(token) if token else None

    if token and token in TOKEN_CACHE:
        del TOKEN_CACHE[token]

    if token_data:
        usuario = Usuario.objects.filter(id=token_data["user_id"], estado=True).first()
        if usuario:
            registrar_auditoria(
                usuario,
                LogActividad.ACCION_LOGOUT,
                "autenticacion",
                f"{usuario.nombre} cerro sesion via autenticacion centralizada.",
            )

    response = JsonResponse({'success': True})
    response.delete_cookie('auth_token')
    return response


@require_http_methods(["GET"])
def auth_sso(request):
    """
    Inicia sesión en Django usando token centralizado y redirige a una ruta interna.

    GET /api/auth/sso/?token=...&next=/dashboard/
    """
    token = request.GET.get("token", "")
    next_url = request.GET.get("next", "/dashboard/")

    # Evita open redirect: solo rutas internas.
    if not next_url.startswith("/"):
        next_url = "/dashboard/"

    token_data = validate_auth_token(token)
    if not token_data:
        return redirect("login")

    usuario = Usuario.objects.filter(id=token_data["user_id"], estado=True).first()
    if not usuario:
        return redirect("login")

    # Sobrescribe explícitamente la identidad de sesión para evitar arrastrar
    # una sesión previa (por ejemplo, admin) al entrar desde Flujómetro.
    request.session[AUTH_SESSION_KEY] = usuario.id
    request.session["rol"] = usuario.rol
    request.session["nombre"] = usuario.nombre
    request.session["usuario"] = usuario.usuario

    return redirect(next_url)


@csrf_exempt
@require_http_methods(["POST"])
def auth_activity_log(request):
    """Registra actividad de módulos integrados."""
    token = get_token_from_request(request)
    token_data = validate_auth_token(token) if token else None

    if not token_data:
        return JsonResponse({"success": False, "error": "Token inválido o expirado"}, status=401)

    usuario = Usuario.objects.filter(id=token_data["user_id"], estado=True).first()
    if not usuario:
        return JsonResponse({"success": False, "error": "Usuario no encontrado"}, status=404)

    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        payload = {}

    modulo = (payload.get("modulo") or "sistema").strip()[:100]
    accion = (payload.get("accion") or "").strip().upper()[:100]
    descripcion = (payload.get("descripcion") or "Actividad registrada desde integracion externa.").strip()

    if not modulo:
        modulo = "sistema"

    if accion not in IMPORTANT_AUDIT_ACTIONS:
        return JsonResponse({"success": True, "skipped": True, "reason": "accion_no_importante"})

    log = registrar_auditoria(usuario, accion, modulo, descripcion, deduplicate_seconds=10)
    if not log:
        return JsonResponse({"success": False, "error": "No se pudo registrar el log"}, status=500)

    return JsonResponse({"success": True, "log_id": log.id})


@require_http_methods(["GET"])
def weather_current(request):
    """Obtiene el estado meteorológico actual desde Weather Underground."""
    station_id = (request.GET.get("station_id") or "").strip() or None

    try:
        payload = WeatherService().get_current_weather(station_id=station_id)
        if not payload.get("success"):
            logger.warning("Weather Service no disponible: %s", payload.get("error", "sin detalle"))
            return JsonResponse({"success": False, "error": "Centro meteorológico no disponible."}, status=503)

        # Transformar respuesta al formato solicitado
        data = payload.get("data") or payload
        response_data = {
            "temperature": data.get("temperature"),
            "humidity": data.get("humidity"),
            "wind_speed": data.get("wind_speed"),
            "wind_direction": data.get("wind_direction"),
            "pressure": data.get("pressure"),
            "rain_day": data.get("rain_day"),
            "uv": data.get("uv"),
            "feels_like": data.get("feels_like"),
            "updated_at": data.get("updated_at"),
            "updated_at_text": data.get("updated_at_text"),
        }
        
        return JsonResponse({
            "success": True,
            "data": response_data,
            "cached": payload.get("cached", False)
        })
    except Exception:
        logger.exception("Error inesperado al obtener datos meteorológicos")
        return JsonResponse({"success": False, "error": "Centro meteorológico no disponible."}, status=503)
