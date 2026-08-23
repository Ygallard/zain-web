"""
Ejemplos de respuestas de la API meteorológica.
Este archivo muestra qué devolvería el endpoint en diferentes escenarios.
"""

# ============================================================================
# ESCENARIO 1: Respuesta exitosa (datos disponibles desde API)
# ============================================================================

response_success_example = {
    "success": True,
    "data": {
        "temperature": 25.3,
        "humidity": 65,
        "wind_speed": 5.2,
        "wind_direction": "NE",
        "pressure": 1013.2,
        "rain_day": 0.0,
        "uv": 7.0,
        "feels_like": 24.8,
        "updated_at": "2026-06-29T15:42:24+00:00",
        "updated_at_text": "Hace 2 minutos"
    },
    "cached": False
}

# ============================================================================
# ESCENARIO 2: Respuesta desde caché (refresco anterior a 5 minutos)
# ============================================================================

response_cached_example = {
    "success": True,
    "data": {
        "temperature": 25.1,
        "humidity": 66,
        "wind_speed": 5.0,
        "wind_direction": "NE",
        "pressure": 1013.1,
        "rain_day": 0.0,
        "uv": 6.9,
        "feels_like": 24.6,
        "updated_at": "2026-06-29T15:40:24+00:00",
        "updated_at_text": "Hace 4 minutos"
    },
    "cached": True  # ← Indicador de que proviene del caché
}

# ============================================================================
# ESCENARIO 3: Estación offline o sin datos
# ============================================================================

response_station_offline = {
    "success": False,
    "error": "Centro meteorológico no disponible."
}

# ============================================================================
# ESCENARIO 4: Error de conectividad o timeout
# ============================================================================

response_connection_error = {
    "success": False,
    "error": "Centro meteorológico no disponible."
}

# ============================================================================
# ESCENARIO 5: Credenciales incompletas
# ============================================================================

response_no_credentials = {
    "success": False,
    "error": "Centro meteorológico no disponible."
}

# ============================================================================
# ESCENARIO 6: Respuesta con algunos valores null (campos no disponibles)
# ============================================================================

response_partial_data = {
    "success": True,
    "data": {
        "temperature": 25.3,
        "humidity": 65,
        "wind_speed": 5.2,
        "wind_direction": "NE",
        "pressure": 1013.2,
        "rain_day": None,  # ← No disponible en esta estación
        "uv": None,        # ← No disponible en esta estación
        "feels_like": 24.8,
        "updated_at": "2026-06-29T15:42:24+00:00",
        "updated_at_text": "Hace 2 minutos"
    },
    "cached": False
}

# ============================================================================
# Códigos HTTP retornados
# ============================================================================

"""
200 OK:
  - Datos obtenidos correctamente (success=true o false)
  - Formato JSON válido siempre

503 Service Unavailable:
  - Error al conectar con Weather Underground
  - Error inesperado durante el procesamiento
  - Ambos casos retornan: {"success": false, "error": "Centro meteorológico no disponible."}
"""

# ============================================================================
# Ejemplo de respuesta real de Weather Underground API v2
# ============================================================================

weather_underground_raw_response = {
    "observations": [
        {
            "stationID": "ICATEM1",
            "obsTimeUtc": "2026-06-29T15:42:24Z",
            "obsTimeLocal": "2026-06-29 10:42:24",
            "neighborhood": "ICATEM1",
            "softwareType": "Davis WeatherLink Live v2.14.2",
            "country": "CR",
            "solarRadiation": 850.0,
            "uv": 7.0,
            "windSpeed": 5.2,
            "windGust": 8.1,
            "windGustDir": 45,
            "windDir": 45,
            "windDirAvg": 46,
            "windSpeedAvg": 5.0,
            "temp": 25.3,
            "feelsLike": 24.8,
            "humidity": 65,
            "humidityAvg": 64,
            "pressure": 1013.2,
            "pressureTrend": "stable",
            "dewpt": 18.1,
            "dewptAvg": 17.9,
            "precipRate": 0.0,
            "precipTotal": 0.0,
            "precipHourly": None,
            "precipDaily": 0.0,
            "precip": 0.0,
            "location": {
                "latitude": 9.8234,
                "longitude": -84.1734,
                "elevation": 1200
            }
        }
    ]
}

if __name__ == "__main__":
    import json
    print("Ejemplos de respuestas de la API meteorológica\n")
    print("=" * 80)
    print("\n✓ ÉXITO con datos recientes:\n")
    print(json.dumps(response_success_example, indent=2))
    
    print("\n" + "=" * 80)
    print("\n✓ ÉXITO desde caché:\n")
    print(json.dumps(response_cached_example, indent=2))
    
    print("\n" + "=" * 80)
    print("\n✗ ERROR (cualquier tipo):\n")
    print(json.dumps(response_station_offline, indent=2))
    
    print("\n" + "=" * 80)
    print("\n✓ ÉXITO con datos parciales (algunos null):\n")
    print(json.dumps(response_partial_data, indent=2))
