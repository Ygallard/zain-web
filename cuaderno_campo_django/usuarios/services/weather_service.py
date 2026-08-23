"""
Servicio de integración con la API oficial de Weather Underground.
Consulta datos meteorológicos de estaciones personales (PWS).
"""
import os
import logging
import socket
import traceback
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import requests
from django.core.cache import cache
from dotenv import load_dotenv


logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(ENV_PATH)


class WeatherService:
    """Servicio para obtener datos meteorológicos de Weather Underground API."""
    
    BASE_URL = "https://api.weather.com/v2/pws/observations/current"
    CACHE_TTL = 300  # 5 minutos
    CACHE_KEY_PREFIX = "weather:current"
    TIMEOUT = 10
    VERIFY_SSL = True
    
    def __init__(self):
        """Inicializa el servicio con credenciales desde variables de entorno."""
        self.api_key = os.getenv("WU_API_KEY", "").strip()
        self.station_id = os.getenv("WU_STATION_ID", "").strip()
        self.station_key = os.getenv("WU_STATION_KEY", "").strip()
        
        if not self.api_key or not self.station_id:
            logger.warning(
                "Weather Service: API Key o Station ID no configurados. "
                "Verifique las variables de entorno WU_API_KEY y WU_STATION_ID."
            )
        
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            ),
        })
    
    def get_current_weather(self, station_id=None):
        """
        Obtiene el estado meteorológico actual desde Weather Underground.
        
        Args:
            station_id (str, opcional): ID de estación. Si no se proporciona,
                                       usa la configurada en el entorno.
        
        Returns:
            dict: Objeto con datos meteorológicos normalizados o error.
        """
        station_id = station_id or self.station_id
        
        if not self.api_key or not station_id:
            logger.warning(
                "Weather Service: credenciales incompletas para la estación '%s'.",
                station_id or "desconocida"
            )
            return {
                "success": False,
                "error": "Credenciales de Weather Underground no configuradas.",
                "source_hint": "error"
            }
        
        cache_key = self._cache_key(station_id)
        cached_payload = cache.get(cache_key)
        if cached_payload:
            payload = dict(cached_payload)
            payload["cached"] = True
            logger.debug("Weather Service: datos desde caché para estación '%s'", station_id)
            return payload
        
        try:
            logger.debug("Weather Service: consultando API para estación '%s'", station_id)
            payload = self._fetch_and_parse(station_id)
            
            # Guardar en caché si fue exitoso
            if payload.get("success"):
                cache.set(cache_key, payload, self.CACHE_TTL)
                logger.info("Weather Service: datos obtenidos exitosamente para estación '%s'", station_id)
            else:
                logger.warning("Weather Service: respuesta sin datos para estación '%s'", station_id)
            
            return payload
        
        except requests.Timeout as e:
            logger.error(
                "Weather Service timeout: station=%s exception=%r traceback=%s",
                station_id,
                e,
                traceback.format_exc(),
            )
            return {
                "success": False,
                "error": "Timeout al conectar con Weather Underground.",
                "source_hint": "error"
            }
        
        except requests.RequestException as e:
            response_status = None
            response_text = None
            if getattr(e, "response", None) is not None:
                response_status = e.response.status_code
                response_text = e.response.text

            logger.error(
                "Weather Service request_exception: station=%s exception=%r status=%s response_text=%s traceback=%s",
                station_id,
                e,
                response_status,
                response_text,
                traceback.format_exc(),
            )
            return {
                "success": False,
                "error": "No se pudo conectar con Weather Underground.",
                "source_hint": "error"
            }
        
        except Exception as e:
            logger.error(
                "Weather Service unexpected_error: station=%s exception=%r traceback=%s",
                station_id,
                e,
                traceback.format_exc(),
            )
            return {
                "success": False,
                "error": "Error procesando datos meteorológicos.",
                "source_hint": "error"
            }
    
    def _fetch_and_parse(self, station_id):
        """
        Realiza la petición a Weather Underground y parsea la respuesta.
        
        Args:
            station_id (str): ID de estación meteorológica.
        
        Returns:
            dict: Objeto con datos normalizados.
        """
        params = {
            "stationId": station_id,
            "apiKey": self.api_key,
            "units": "m",  # Sistema métrico
            "format": "json"
        }

        request = requests.Request("GET", self.BASE_URL, params=params)
        prepared_request = self.session.prepare_request(request)

        self._log_dns_resolution(prepared_request.url)

        logger.info(
            "Weather Service request: method=%s endpoint=%s url=%s params=%s headers=%s timeout=%s verify_ssl=%s",
            prepared_request.method,
            self.BASE_URL,
            self._mask_url_api_key(prepared_request.url),
            self._mask_params(params),
            self._mask_headers(dict(prepared_request.headers)),
            self.TIMEOUT,
            self.VERIFY_SSL,
        )

        response = self.session.send(
            prepared_request,
            timeout=self.TIMEOUT,
            verify=self.VERIFY_SSL,
        )
        logger.warning(
            "Weather Service response: status=%s body=%s",
            response.status_code,
            response.text,
        )
        response.raise_for_status()
        
        data = response.json()
        
        # Validar estructura de respuesta
        if not data or "observations" not in data or not data["observations"]:
            logger.warning(
                "Weather Service: respuesta vacía o inválida para estación '%s'. "
                "Posible estación offline o no accesible.",
                station_id
            )
            return {
                "success": False,
                "error": "La estación meteorológica está offline o no disponible.",
                "source_hint": "weather_underground"
            }
        
        # Tomar la primera (y generalmente única) observación
        obs = data["observations"][0]
        
        return self._normalize_payload(obs)
    
    def _normalize_payload(self, observation):
        """
        Transforma la respuesta de Weather Underground a formato uniforme.
        
        Args:
            observation (dict): Observación desde la API de WU.
        
        Returns:
            dict: Objeto normalizado con campos estándar.
        """
        logger.debug("Weather Service: normalizando observación con %d campos", len(observation))
        
        # Extraer valores, manejando ausencia de campos
        metric = observation.get("metric") if isinstance(observation.get("metric"), dict) else {}

        temp = self._get_number(observation, ["temp", "temperature"])
        if temp is None:
            temp = self._get_number(metric, "temp")

        humidity = self._get_number(observation, "humidity")
        pressure = self._get_number(observation, "pressure")
        if pressure is None:
            pressure = self._get_number(metric, "pressure")

        wind_speed = self._get_number(observation, ["windSpeed", "wind_speed"])
        if wind_speed is None:
            wind_speed = self._get_number(metric, "windSpeed")

        wind_dir = self._get_wind_direction(
            observation.get("windDir", observation.get("winddir"))
        )

        rain_day = self._get_number(observation, ["precipDaily", "precipHourly", "precip", "precipTotal"])
        if rain_day is None:
            rain_day = self._get_number(metric, ["precipTotal", "precipRate"])

        feels_like = self._get_number(observation, ["feelsLike", "heatIndex"])
        if feels_like is None:
            feels_like = self._get_number(metric, ["heatIndex", "windChill"])

        uv = self._get_number(observation, "uv")
        
        # Obtener timestamp de actualización
        timestamp_str = observation.get("obsTimeUtc")
        last_updated = self._parse_timestamp(timestamp_str)
        
        payload = {
            "success": True,
            "temperature": temp,
            "humidity": humidity,
            "wind_speed": wind_speed,
            "wind_direction": wind_dir,
            "pressure": pressure,
            "rain_day": rain_day,
            "uv": uv,
            "feels_like": feels_like,
            "updated_at": last_updated,
            "updated_at_text": self._format_relative_time(last_updated),
            "source_hint": "weather_underground",
            "cached": False,
            "fetched_at": datetime.now(timezone.utc).isoformat()
        }
        
        logger.debug("Weather Service: payload normalizado - temp: %s, humedad: %s, viento: %s",
                    temp, humidity, wind_speed)
        
        return payload
    
    def _get_number(self, obj, keys):
        """
        Obtiene valor numérico de un diccionario, intentando múltiples claves.
        
        Args:
            obj (dict): Diccionario de observación.
            keys (str o list): Clave(s) a buscar.
        
        Returns:
            float o None: Valor encontrado o None.
        """
        if isinstance(keys, str):
            keys = [keys]
        
        for key in keys:
            value = obj.get(key)
            if value is not None:
                try:
                    return float(value)
                except (ValueError, TypeError):
                    logger.debug("Weather Service: valor no numérico para clave '%s': %s",
                               key, type(value).__name__)
        
        return None
    
    def _get_wind_direction(self, wind_dir_deg):
        """
        Convierte grados de dirección del viento a notación cardinal.
        Args:
            wind_dir_deg (float o int): Dirección en grados (0-360).
        
        Returns:
            str o None: Código cardinal (N, NE, E, etc.) o None.
        """
        if wind_dir_deg is None:
            return None
        
        try:
            deg = float(wind_dir_deg)
            directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                         "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
            idx = int((deg + 11.25) / 22.5) % 16
            return directions[idx]
        except (ValueError, TypeError):
            logger.debug("Weather Service: dirección de viento inválida: %s", wind_dir_deg)
            return None
    
    def _parse_timestamp(self, timestamp_str):
        """
        Parsea timestamp ISO 8601 de Weather Underground.
        
        Args:
            timestamp_str (str): Timestamp ISO 8601 (ej: "2026-06-29T15:42:24Z").
        
        Returns:
            str o None: Timestamp formateado o None.
        """
        if not timestamp_str:
            return None
        
        try:
            # Weather Underground devuelve en UTC
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return dt.isoformat()
        except (ValueError, AttributeError):
            logger.debug("Weather Service: no se pudo parsear timestamp: %s", timestamp_str)
            return None
    
    def _format_relative_time(self, timestamp_str):
        """
        Formatea timestamp como tiempo relativo (ej: "hace 5 minutos").
        
        Args:
            timestamp_str (str): Timestamp ISO 8601.
        
        Returns:
            str o None: Texto relativo o None.
        """
        if not timestamp_str:
            return None
        
        try:
            dt = datetime.fromisoformat(timestamp_str)
            now = datetime.now(timezone.utc)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            
            delta = now - dt
            seconds = int(delta.total_seconds())
            
            if seconds < 60:
                return "Hace menos de un minuto"
            
            minutes = seconds // 60
            if minutes < 60:
                return f"Hace {minutes} minuto" if minutes == 1 else f"Hace {minutes} minutos"
            
            hours = minutes // 60
            if hours < 24:
                return f"Hace {hours} hora" if hours == 1 else f"Hace {hours} horas"
            
            days = hours // 24
            return f"Hace {days} día" if days == 1 else f"Hace {days} días"
        
        except (ValueError, TypeError):
            logger.debug("Weather Service: no se pudo formatear timestamp relativo: %s", timestamp_str)
            return None
    
    def _cache_key(self, station_id):
        """Genera clave de caché para una estación."""
        return f"{self.CACHE_KEY_PREFIX}:{station_id}"

    def _mask_secret(self, value):
        """Oculta parcialmente secretos para logging seguro."""
        if not value:
            return value
        value = str(value)
        if len(value) <= 8:
            return "*" * len(value)
        return f"{value[:4]}...{value[-4:]}"

    def _mask_headers(self, headers):
        """Enmascara headers sensibles antes de loguear."""
        masked = dict(headers)
        for key in ["Authorization", "authorization", "X-Api-Key", "x-api-key"]:
            if key in masked:
                masked[key] = self._mask_secret(masked[key])
        return masked

    def _mask_params(self, params):
        """Enmascara parámetros sensibles antes de loguear."""
        masked = dict(params)
        if "apiKey" in masked:
            masked["apiKey"] = self._mask_secret(masked["apiKey"])
        return masked

    def _mask_url_api_key(self, url):
        """Enmascara apiKey en URL completa para logging."""
        split = urlsplit(url)
        query_pairs = parse_qsl(split.query, keep_blank_values=True)
        masked_pairs = []
        for key, value in query_pairs:
            if key == "apiKey":
                masked_pairs.append((key, self._mask_secret(value)))
            else:
                masked_pairs.append((key, value))
        return urlunsplit((split.scheme, split.netloc, split.path, urlencode(masked_pairs), split.fragment))

    def _log_dns_resolution(self, url):
        """Registra resolución DNS del host de destino para diagnóstico."""
        host = urlsplit(url).hostname
        if not host:
            return
        try:
            infos = socket.getaddrinfo(host, 443, proto=socket.IPPROTO_TCP)
            addresses = sorted({info[4][0] for info in infos})
            logger.info("Weather Service DNS: host=%s resolved_ips=%s", host, addresses)
        except Exception as e:
            logger.warning("Weather Service DNS: host=%s resolution_error=%r", host, e)
