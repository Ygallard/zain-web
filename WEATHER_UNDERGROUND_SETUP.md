# Integración Weather Underground - Instrucciones de Configuración

## ✅ Cambios Realizados

La integración ha sido completamente migrada de WeatherCloud a **Weather Underground API**.

### Archivos Modificados/Creados

1. **`.env`** - Actualizado
   - Removidas variables de WeatherCloud
   - Agregadas nuevas variables para Weather Underground

2. **`cuaderno_campo_django/usuarios/services/weather_underground_service.py`** - CREADO
   - Nuevo servicio que consulta la API de Weather Underground
   - Transforma datos a formato uniforme
   - Implementa caché de 5 minutos
   - Manejo robusto de errores

3. **`cuaderno_campo_django/usuarios/api.py`** - Actualizado
   - Endpoint `GET /api/weather/current/` ahora usa `WeatherUndergroundService`
   - Respuesta mantiene el mismo formato para compatibilidad con frontend

4. **`cuaderno_campo_django/usuarios/services/__init__.py`** - CREADO
   - Paquete Python inicializado

### Estado del Frontend

El frontend ya está listo y consumiendo el endpoint correctamente:
- Tarjeta "Tiempo Actual" renderiza correctamente
- Auto-refresco cada 5 minutos habilitado
- Manejo de errores implementado

---

## 🔧 Configuración Requerida

### Paso 1: Obtener API Key de Weather Underground

1. Ve a [https://www.weatherunderground.com/member/api](https://www.weatherunderground.com/member/api)
2. Inicia sesión o crea una cuenta (si no tienes una)
3. Accede a **"My API Keys"** o **"Get API Key"**
4. Busca la sección de **"Personal Weather Station"** o **"PWS"**
5. Copia tu **API Key**

### Paso 2: Agregar la API Key al `.env`

Edita el archivo `.env` en la raíz del proyecto:

```
c:\Users\Yordano\Documents\Proyectos\zaino-web-main\.env
```

Busca la línea:
```
WU_API_KEY=
```

Y reemplázala con tu API Key (sin espacios ni comillas):
```
WU_API_KEY=tu_api_key_aqui
```

**Ejemplo completo:**
```
WU_API_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
WU_STATION_ID=FT0360
```

### Paso 3: Guardar cambios

- Guarda el archivo `.env`
- El servidor Django **detectará automáticamente** los cambios (gracias a StatReloader)
- No es necesario reiniciar el servidor

### Paso 4: Verificar que funciona

Abre una terminal en la carpeta del proyecto:

```powershell
# Realizar petición de prueba
Invoke-WebRequest -UseBasicParsing 'http://localhost:8000/api/weather/current/' | Select-Object -ExpandProperty Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

**Respuesta exitosa (ejemplo):**
```json
{
  "success": true,
  "data": {
    "status": "Despejado",
    "temperature": 25.3,
    "humidity": 60,
    "pressure": 1013.2,
    "wind_speed": 5.2,
    "wind_direction": "NE",
    "rain_today": 0.0,
    "feels_like": 24.8,
    "uv_index": 7.0,
    "last_updated_at": "2026-06-29T15:42:24+00:00",
    "last_updated_text": "Hace 2 minutos",
    "source_hint": "weather_underground",
    "cached": false
  },
  "source": "weather_underground"
}
```

**Respuesta si falta API Key (esperada inicialmente):**
```json
{
  "success": false,
  "error": "Centro meteorológico no disponible."
}
```

---

## 📊 Datos Disponibles

El endpoint retorna los siguientes campos:

| Campo | Tipo | Descripción | Ejemplo |
|-------|------|-------------|---------|
| `status` | string | Estado del clima | "Despejado" |
| `temperature` | float | Temperatura en °C | 25.3 |
| `humidity` | float | Humedad en % | 60 |
| `pressure` | float | Presión en hPa | 1013.2 |
| `wind_speed` | float | Velocidad del viento en km/h | 5.2 |
| `wind_direction` | string | Dirección del viento (cardinal) | "NE" |
| `rain_today` | float | Lluvia del día en mm | 0.0 |
| `feels_like` | float | Sensación térmica en °C | 24.8 |
| `uv_index` | float | Índice UV | 7.0 |
| `last_updated_at` | string | Timestamp ISO 8601 | "2026-06-29T15:42:24+00:00" |
| `last_updated_text` | string | Tiempo relativo | "Hace 2 minutos" |

---

## 🔐 Seguridad

✅ **Credenciales Seguras:**
- API Key SOLO se almacena en `.env` (no versionado en Git)
- Nunca se expone en logs, respuestas o errores
- Mensajes de error genéricos: "Centro meteorológico no disponible."

✅ **Caché:**
- 5 minutos TTL para reducir llamadas a la API
- Minimiza uso de API Key y mejora rendimiento

---

## 🐛 Troubleshooting

### "Centro meteorológico no disponible."

**Causas posibles:**
1. API Key no configurada o incorrecta
2. Estación ID inválido (debería ser "FT0360")
3. Credenciales expiradas
4. Problema de conectividad a Weather Underground

**Soluciones:**
- Verifica que `.env` tenga `WU_API_KEY` configurado correctamente
- Comprueba que puedas acceder a `https://api.weatherunderground.com` desde tu red
- Revisa los logs del servidor Django para más detalles

### Datos vacíos (null)

Si la API responde pero algunos campos son null:
- Weather Underground podría no tener datos para esos campos
- Comprueba que tu estación WS0360 está activa en Weather Underground
- Algunos campos (como `uv_index`) son opcionales

---

## 📝 Variables de Entorno

```
WU_API_KEY=            # Tu API Key de Weather Underground (REQUERIDO)
WU_STATION_ID=FT0360   # ID de tu estación meteorológica
```

---

## ✨ Características

- **Integración completa** con Weather Underground API v2
- **Caché automático** de 5 minutos
- **Manejo robusto** de errores sin exposición de credenciales
- **Frontend integrado** - la tarjeta "Tiempo Actual" se actualiza automáticamente
- **Formato uniforme** - compatibilidad total con interfaz anterior
- **Auto-refresco** cada 5 minutos en el dashboard

---

## 📱 Endpoint API

```
GET /api/weather/current/

Parámetros opcionales:
  ?station_id=FT0360    # Especificar estación (default: FT0360)

Response (200):
{
  "success": true,
  "data": { ...datos meteorológicos... },
  "source": "weather_underground"
}

Response (503 - Error):
{
  "success": false,
  "error": "Centro meteorológico no disponible."
}
```

---

**Implementación completada el 29 de junio de 2026.**
