"""
Servicio de integración con Weather Underground API
para estaciones meteorológicas personales (PWS).
"""
import os
import logging
from datetime import datetime, timezone
from pathlib import Path

import requests
from django.core.cache import cache
from dotenv import load_dotenv


logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(ENV_PATH)


class WeatherUndergroundService:
    """Servicio para obtener datos meteorológicos de Weather Underground."""
    
    BASE_URL = "https://api.weatherunderground.com/v2"
    CACHE_TTL = 300  # 5 minutos
    CACHE_KEY_PREFIX = "weather_underground:current"
    TIMEOUT = 10
    
    def __init__(self):
        """Inicializa el servicio con credenciales desde variables de entorno."""
        self.api_key = os.getenv("WU_API_KEY", "").strip()
        self.station_id = os.getenv("WU_STATION_ID", "").strip()
        
        if not self.api_key or not self.station_id:
            logger.warning(
                "Weather Underground: API Key o Station ID no configurados. "
                "Verifique las variables de entorno WU_API_KEY y WU_STATION_ID."
            )
        
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
            ),
        })
    
    def get_current_weather(self, station_id=None):
        """
        Obtiene el estado meteorológico actual.
        
        Args:
            station_id (str, opcional): ID de estación. Si no se proporciona,
                                       usa la configurada en el entorno.
        
        Returns:
            dict: Objeto con datos meteorológicos normalizados o error.
        """
        station_id = station_id or self.station_id
        
        if not self.api_key or not station_id:
            logger.warning(
                "Weather Underground: credenciales incompletas para la estación '%s'.",
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
            return payload
        
        try:
            payload = self._fetch_and_parse(station_id)
            
            # Guardar en caché si fue exitoso
            if payload.get("success"):
                cache.set(cache_key, payload, self.CACHE_TTL)
            
            return payload
        
        except requests.RequestException as e:
            logger.exception(
                "Weather Underground: Error de conexión al obtener datos (estación: %s).",
                station_id
            )
            return {
                "success": False,
                "error": "No se pudo conectar con Weather Underground.",
                "source_hint": "error"
            }
        
        except Exception as e:
            logger.exception(
                "Weather Underground: Error inesperado al procesar datos (estación: %s).",
                station_id
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
        url = f"{self.BASE_URL}/pws/observations/current"
        params = {
            "stationId": station_id,
            "apiKey": self.api_key,
            "units": "m"  # Sistema métrico
        }
        
        response = self.session.get(url, params=params, timeout=self.TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        
        # Validar estructura de respuesta
        if "observations" not in data or not data["observations"]:
            logger.warning(
                "Weather Underground: respuesta vacía para estación '%s'.",
                station_id
            )
            return {
                "success": False,
                "error": "Sin datos disponibles.",
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
        # Extraer valores, manejando ausencia de campos
        temp = self._get_number(observation, "temp")
        humidity = self._get_number(observation, "humidity")
        pressure = self._get_number(observation, "pressure")
        wind_speed = self._get_number(observation, "windSpeed")
        wind_dir = self._get_wind_direction(observation.get("windDir"))
        rain = self._get_number(observation, ["precipHourly", "precipDaily", "precip"])
        feels_like = self._get_number(observation, "feelsLike")
        uv = self._get_number(observation, "uv")
        
        # Derivar estado del clima
        status = self._derive_status(temp, humidity, pressure, rain, uv)
        
        # Normalizar timestamp
        timestamp_str = observation.get("obsTimeUtc")
        last_updated = self._parse_timestamp(timestamp_str)
        
        return {
            "success": True,
            "status": status,
            "temperature": temp,
            "humidity": humidity,
            "pressure": pressure,
            "wind_speed": wind_speed,
            "wind_direction": wind_dir,
            "rain_today": rain,
            "feels_like": feels_like,
            "uv_index": uv,
            "last_updated_at": last_updated,
            "last_updated_text": self._format_relative_time(last_updated),
            "source_hint": "weather_underground",
            "cached": False,
            "fetched_at": datetime.now(timezone.utc).isoformat()
        }
    
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
                    pass
        
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
            minutes = int(delta.total_seconds() / 60)
            
            if minutes < 1:
                return "Hace menos de un minuto"
            elif minutes == 1:
                return "Hace 1 minuto"
            elif minutes < 60:
                return f"Hace {minutes} minutos"
            else:
                hours = int(minutes / 60)
                if hours == 1:
                    return "Hace 1 hora"
                else:
                    return f"Hace {hours} horas"
        except (ValueError, TypeError):
            return None
    
    def _derive_status(self, temp, humidity, pressure, rain, uv):
        """
        Deriva un estado textual del clima basado en condiciones.
        
        Args:
            temp (float): Temperatura en °C.
            humidity (float): Humedad en %.
            pressure (float): Presión en hPa.
            rain (float): Lluvia en mm.
            uv (float): Índice UV.
        
        Returns:
            str: Descripción del estado (ej: "Despejado", "Nublado", "Lluvioso").
        """
        # Lógica simple: si hay lluvia reciente, "Lluvioso"
        if rain and rain > 0.1:
            return "Lluvioso"
        
        # Si UV es alto, probablemente despejado
        if uv and uv >= 6:
            return "Despejado"
        
        # Si UV es moderado, probablemente parcialmente nublado
        if uv and uv >= 3:
            return "Parcialmente Nublado"
        
        # Por defecto, sin mucha información
        return "Parcialmente Nublado"
    
    def _cache_key(self, station_id):
        """Genera clave de caché para una estación."""
        return f"{self.CACHE_KEY_PREFIX}:{station_id}"
