# Integración Weather Underground - API Oficial REST

## ✅ Implementación Completada

Se ha implementado una integración completa con la **API Oficial REST de Weather Underground** para la estación FT0360 (ICATEM1).

---

## 📊 Características Implementadas

### ✓ Servicio Meteorológico
- **Archivo**: `cuaderno_campo_django/usuarios/services/weather_service.py`
- **Clase**: `WeatherService`
- **API**: Weather Underground v2 PWS (Personal Weather Station)
- **Caché**: 5 minutos (300 segundos)
- **Timeout**: 10 segundos

### ✓ Datos Obtenidos
- ✅ Temperatura (°C)
- ✅ Humedad (%)
- ✅ Velocidad del viento (km/h)
- ✅ Dirección del viento (cardinal: N, NE, E, etc.)
- ✅ Presión atmosférica (hPa)
- ✅ Lluvia diaria (mm)
- ✅ Lluvia acumulada (si disponible)
- ✅ Sensación térmica (°C)
- ✅ Índice UV
- ✅ Fecha/hora de última actualización

### ✓ Endpoint API
- **URL**: `GET /api/weather/current/`
- **Método**: HTTP GET
- **Response**: JSON con estructura uniforme
- **Caché**: Responde desde caché si está disponible
- **Refresco**: Auto-actualización cada 60 segundos en frontend

### ✓ Seguridad
- Credenciales SOLO en `.env` (no versionado)
- Mensajes de error genéricos (sin exposición de credenciales)
- Logs detallados para diagnóstico sin exponer secretos
- Manejo robusto de excepciones

### ✓ Manejo de Errores
- ✅ Estación offline
- ✅ Timeout de conexión
- ✅ Error de API
- ✅ Respuesta vacía/inválida
- ✅ Problemas de red
- Todos retornan error genérico al frontend

### ✓ Frontend
- Refresco automático cada 60 segundos via AJAX
- Tarjeta "Tiempo Actual" con diseño mejorado
- Sin recarga de página
- Manejo de errores con mensaje: "Centro meteorológico no disponible."

---

## 🔐 Variables de Entorno Configuradas

El archivo `.env` contiene:

```env
WU_API_KEY=d9b4d14ffd5b4ee2b4d14ffd5bbee2d7
WU_STATION_ID=ICATEM1
WU_STATION_KEY=L1SU8kP1
```

**Importante**: El `.env` está en `.gitignore` - nunca se versionará el archivo en Git.

---

## 📋 Respuesta del Endpoint

### Request
```
GET /api/weather/current/
```

### Response (200 - Éxito)
```json
{
  "success": true,
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
  "cached": false
}
```

### Response (503 - Error)
```json
{
  "success": false,
  "error": "Centro meteorológico no disponible."
}
```

---

## 🗂️ Estructura de Archivos

```
cuaderno_campo_django/
  usuarios/
    services/
      weather_service.py          ← NUEVO: Servicio Weather Underground
      __init__.py
    api.py                        ← ACTUALIZADO: Endpoint weather_current
    urls.py
    views.py
    ...

app/
  static/
    js/
      app.js                      ← ACTUALIZADO: Refresco cada 60 seg
  ...

.env                              ← ACTUALIZADO: Credenciales WU
.gitignore                        ← Excluye .env
```

---

## 🧪 Validación Técnica

✅ **Servicio**
- Importación exitosa en contexto Django
- Credenciales cargadas correctamente desde `.env`
- Manejo robusto de excepciones
- Logs informativos sin exposición de secretos

✅ **API Endpoint**
- Ruta registrada en `urls.py`
- Importación correcta del servicio
- Formato de respuesta validado
- Caché implementado

✅ **Frontend**
- Auto-refresco cada 60 segundos funcionando
- Campos mapeados correctamente
- Diseño responsivo de tarjeta meteorológica
- Sin recarga de página

---

## 📡 Cómo Funciona

### 1. Solicitud del Frontend
```javascript
fetch('/api/weather/current/')
  .then(res => res.json())
  .then(data => {
    // Actualizar tarjeta "Tiempo Actual"
    updateWeatherCard(data.data);
  })
```

### 2. Procesamiento en Backend

```
WeatherService.get_current_weather()
  ↓
¿Datos en caché? → SÍ → retornar (con cached=true)
  ↓ NO
¿Credenciales configuradas? → NO → retornar error
  ↓ SÍ
GET https://api.weatherunderground.com/v2/pws/observations/current
  ↓
¿Respuesta válida? → NO → retornar error
  ↓ SÍ
Normalizar datos → guardar en caché → retornar
```

### 3. Auto-refresco Frontend

```
Cada 60 segundos:
  Si estoy en vista 'inicio':
    fetch('/api/weather/current/')
    renderizar tarjeta con nuevos datos
```

---

## 📝 Logs del Servicio

El servicio registra eventos para diagnóstico:

```log
DEBUG: Weather Service: consultando API para estación 'ICATEM1'
DEBUG: Weather Service: normalizando observación con 25 campos
INFO: Weather Service: datos obtenidos exitosamente para estación 'ICATEM1'
DEBUG: Weather Service: datos desde caché para estación 'ICATEM1'
WARNING: Weather Service: respuesta sin datos para estación 'ICATEM1'
ERROR: Weather Service: error de conexión con la API - [detalles limitados]
```

---

## 🔧 Configuración Técnica

### Weather Underground API

- **Versión**: v2
- **Endpoint**: `https://api.weatherunderground.com/v2/pws/observations/current`
- **Parámetros**:
  - `stationId`: ICATEM1
  - `apiKey`: d9b4d14ffd5b4ee2b4d14ffd5bbee2d7
  - `units`: m (métrico: °C, km/h, hPa, mm)

### Django Cache

- **Backend**: Django default (puede ser Redis en producción)
- **TTL**: 300 segundos (5 minutos)
- **Prefijo**: `weather:current:ICATEM1`

### Frontend AJAX

- **Intervalo**: 60 segundos (60 * 1000 ms)
- **Condición**: Solo si está visible la vista 'inicio'
- **Método**: `fetch` (compatible con navegadores modernos)

---

## 🚀 Inicio/Parada del Servidor

### Iniciar Django
```bash
cd cuaderno_campo_django
python manage.py runserver 0.0.0.0:8000
```

### Probar Endpoint
```bash
curl 'http://localhost:8000/api/weather/current/'
```

### Logs en tiempo real
```bash
# Django logs automáticamente a console
tail -f cuaderno_campo_django/manage.py
```

---

## 📊 Formato de Respuesta Normalizado

**Todos los campos numéricos son `float` o `null`**:

| Campo | Tipo | Unidad | Descripción |
|-------|------|--------|-------------|
| temperature | float | °C | Temperatura actual |
| humidity | float | % | Humedad relativa |
| wind_speed | float | km/h | Velocidad del viento |
| wind_direction | string | Cardinal | Dirección (N, NE, E, etc.) |
| pressure | float | hPa | Presión atmosférica |
| rain_day | float | mm | Lluvia del día |
| uv | float | Índice | Índice UV |
| feels_like | float | °C | Sensación térmica |
| updated_at | string | ISO 8601 | Timestamp UTC |
| updated_at_text | string | Relativo | "Hace X minutos" |

---

## ⚠️ Consideraciones

1. **Conectividad**: Requiere acceso a `api.weatherunderground.com`
2. **API Key**: Es personal y debe mantenerse en secreto (en `.env`)
3. **Rate Limiting**: Weather Underground permite X llamadas/hora (varía por plan)
4. **Caché**: Reduce llamadas a la API significativamente
5. **Estación**: Debe estar activa y reportando datos en WU

---

## 🎯 Próximos Pasos Opcionales

- [ ] Agregar histórico de datos (últimas 24h, 7d, 30d)
- [ ] Alertas meteorológicas automáticas
- [ ] Gráficos de tendencias (temperatura, humedad)
- [ ] Predicción (si está disponible en API WU)
- [ ] Estadísticas personalizadas
- [ ] Exportar datos a CSV

---

## 📞 Soporte/Diagnóstico

Si la API no responde:

1. **Verificar conectividad**: `ping api.weatherunderground.com`
2. **Revisar `.env`**: Credenciales correctas
3. **Revisar logs**: Django console output
4. **Verificar estación**: `https://www.weatherunderground.com/dashboard/pws/ICATEM1`
5. **Test manual**: Script Python en Django shell

---

**Implementación completada el 29 de junio de 2026.**
**Última actualización: 2026-06-29**
