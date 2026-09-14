import calendar
import json
import os
from datetime import date, datetime, timedelta, timezone as dt_timezone
from pathlib import Path

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET

from usuarios.decorators import AUTH_SESSION_KEY
from usuarios.models import Usuario
from usuarios.services.weather_service import WeatherService

from .services import ArduinoFlowmeterService


def index(request):
    return render(request, "flujometro/app.html")


@require_GET
def health(request):
    return JsonResponse({"status": "ok"})


@require_GET
def flowmeter_data(request):
    payload, status_code = ArduinoFlowmeterService().get_data()
    return JsonResponse(payload, status=status_code)


@require_GET
def auth_status(request):
    user = Usuario.objects.filter(id=request.session.get(AUTH_SESSION_KEY), estado=True).first()
    return JsonResponse({
        "authenticated": user is not None,
        "user": _serialize_user(user),
        "sso_url": "/dashboard/" if user else None,
    })


@csrf_exempt
def auth_login(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Método no permitido."}, status=405)
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        payload = {}
    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""
    user = Usuario.objects.filter(usuario__iexact=username, estado=True).first()
    valid = bool(user and _password_matches(password, user.password))
    if (
        user
        and not valid
        and user.usuario == os.getenv("AUTH_USERNAME", "").strip()
        and password == os.getenv("AUTH_PASSWORD", "")
    ):
        user.password = make_password(password)
        user.save(update_fields=["password"])
        valid = True
    if not valid:
        return JsonResponse({"success": False, "error": "Usuario o contraseña inválidos."}, status=401)
    request.session[AUTH_SESSION_KEY] = user.id
    request.session["rol"] = user.rol
    request.session["nombre"] = user.nombre
    request.session["usuario"] = user.usuario
    request.session.set_expiry(43200)
    return JsonResponse({"success": True, "user": _serialize_user(user), "sso_url": "/dashboard/"})


@csrf_exempt
def auth_logout(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Método no permitido."}, status=405)
    request.session.flush()
    return JsonResponse({"success": True})


@require_GET
def quick_stats(request):
    user = Usuario.objects.filter(id=request.session.get(AUTH_SESSION_KEY), estado=True).first()
    if not user:
        return JsonResponse({"error": "No autenticado"}, status=401)
    from usuarios.models import Cuartel, Predio

    return JsonResponse({"success": True, "data": {
        "usuarios_activos": Usuario.objects.filter(estado=True).count(),
        "predios_registrados": Predio.objects.count(),
        "cuarteles_activos": Cuartel.objects.filter(estado=True).count(),
        "ultima_actividad": None,
    }})


@require_GET
def weather_current(request):
    payload = WeatherService().get_current_weather(request.GET.get("station_id") or None)
    if not payload.get("success"):
        return JsonResponse({"success": False, "error": "Centro meteorológico no disponible."}, status=503)
    data = payload.get("data") or payload
    fields = ("temperature", "humidity", "wind_speed", "wind_direction", "pressure", "rain_day", "uv", "feels_like", "updated_at", "updated_at_text")
    return JsonResponse({"success": True, "data": {field: data.get(field) for field in fields}, "cached": payload.get("cached", False)})


@csrf_exempt
def visitas(request):
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido."}, status=405)
    path = Path(os.getenv("VISITAS_DATA_PATH", "/tmp/visitas.json"))
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"num_visitas": 0}
    except (OSError, json.JSONDecodeError):
        data = {"num_visitas": 0}
    data["num_visitas"] = int(data.get("num_visitas", 0)) + 1
    path.write_text(json.dumps(data), encoding="utf-8")
    return JsonResponse(data)


def _reports_dir():
    path = Path(os.getenv("INFORMES_DATA_DIR", "/tmp/informes"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def _numeric_value(property_data):
    if not isinstance(property_data, dict):
        return 0.0
    try:
        return float(property_data.get("value") or 0)
    except (TypeError, ValueError):
        return 0.0


@require_GET
def informes(request):
    result = []
    for path in _reports_dir().glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        timestamp = timezone.localtime(datetime.fromtimestamp(path.stat().st_mtime, dt_timezone.utc))
        result.append({"id": path.stem, "nombre": data.get("nombre", path.name), "fecha": timestamp.strftime("%d/%m/%Y"), "fecha_completa": timestamp.strftime("%d/%m/%Y %H:%M"), "periodo": data.get("periodo", "N/A"), "datos": data})
    result.sort(key=lambda item: item["fecha_completa"], reverse=True)
    return JsonResponse({"success": True, "informes": result})


@csrf_exempt
def generar_informe(request):
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido."}, status=405)
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        payload = {}

    now = timezone.localtime()
    fecha_inicio = payload.get("fecha_inicio")
    fecha_fin = payload.get("fecha_fin")
    try:
        fecha_inicio_obj = date.fromisoformat(fecha_inicio) if fecha_inicio else None
        fecha_fin_obj = date.fromisoformat(fecha_fin) if fecha_fin else None
    except ValueError:
        return JsonResponse({"success": False, "error": "Las fechas deben tener formato válido."}, status=400)

    if fecha_inicio_obj and fecha_fin_obj and fecha_inicio_obj > fecha_fin_obj:
        return JsonResponse({"success": False, "error": "La fecha de inicio no puede ser posterior a la fecha fin."}, status=400)

    if not fecha_inicio or not fecha_fin:
        fecha_fin = now.date().isoformat()
        fecha_inicio = (now.date() - timedelta(days=30)).isoformat()
    for path in _reports_dir().glob("*.json"):
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
            generated = datetime.strptime(existing.get("fecha_generacion", ""), "%d/%m/%Y %H:%M:%S")
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        if generated.year == now.year and generated.month == now.month:
            return JsonResponse({"success": False, "error": "Ya existe un informe del mes actual."}, status=400)

    flow_payload, flow_status = ArduinoFlowmeterService().get_data()
    if flow_status != 200 or not flow_payload.get("success"):
        return JsonResponse({
            "success": False,
            "error": "No se pudo obtener la lectura del flujómetro. El informe no fue generado.",
        }, status=502)

    flow_data = flow_payload.get("data") or {}
    flujo_instantaneo = _numeric_value(flow_data.get("constflow"))
    flujo_acumulado = _numeric_value(flow_data.get("instflow"))
    dias_periodo = (date.fromisoformat(fecha_fin) - date.fromisoformat(fecha_inicio)).days + 1
    promedio_diario = flujo_acumulado / dias_periodo if dias_periodo else 0.0
    data = {
        "nombre": "Informe de Caudal",
        "fecha_generacion": now.strftime("%d/%m/%Y %H:%M:%S"),
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "periodo": f"{fecha_inicio} a {fecha_fin}",
        "datos": {
            "flujo_instantaneo": flujo_instantaneo,
            "flujo_acumulado": flujo_acumulado,
            "promedio_diario": promedio_diario,
        },
        "estadisticas": {
            "total_litros": flujo_acumulado,
            "promedio_lmin": flujo_instantaneo,
        },
    }
    path = _reports_dir() / f"informe_{now.strftime('%Y%m%d_%H%M%S')}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return JsonResponse({"success": True, "message": "Informe generado exitosamente", "informe": {"id": path.stem, "nombre": data["nombre"], "fecha": now.strftime("%d/%m/%Y"), "periodo": data["periodo"]}})


def informe_detail(request, informe_id):
    path = _reports_dir() / f"{informe_id}.json"
    if not path.is_file() or path.parent != _reports_dir():
        return JsonResponse({"error": "Informe no encontrado"}, status=404)
    if request.method == "DELETE":
        path.unlink()
        return JsonResponse({"success": True, "message": "Informe eliminado exitosamente"})
    if request.method != "GET":
        return JsonResponse({"error": "Método no permitido."}, status=405)
    try:
        return JsonResponse({"success": True, "informe": json.loads(path.read_text(encoding="utf-8"))})
    except (OSError, json.JSONDecodeError):
        return JsonResponse({"error": "Informe inválido"}, status=500)


def _serialize_user(user):
    if not user:
        return None
    return {"id": user.id, "username": user.usuario, "nombre": user.nombre, "rol": user.rol, "rut": user.rut}


def _password_matches(raw_password, stored_password):
    if stored_password.startswith(("pbkdf2_", "argon2$", "bcrypt")):
        return check_password(raw_password, stored_password)
    return raw_password == stored_password