
from app import app
from flask import jsonify, request, make_response, session
import requests
from app.utils import config
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
from datetime import datetime, timedelta

settings = config.load_config()


def get_auth_credentials():
    """Obtiene credenciales de login desde variables de entorno."""
    runtime_settings = config.load_config()
    username = runtime_settings.get('AUTH_USERNAME') or 'admin'
    password = runtime_settings.get('AUTH_PASSWORD') or 'admin123'
    return username, password


def is_authenticated():
    return bool(session.get('authenticated'))


@app.before_request
def protect_api_routes():
    """Protege la API para que requiera sesión activa."""
    if not request.path.startswith('/api/'):
        return None

    allowed_paths = {
        '/api/auth/login',
        '/api/auth/logout',
        '/api/auth/status'
    }

    if request.path in allowed_paths:
        return None

    if not is_authenticated():
        return jsonify({
            'error': 'No autenticado',
            'details': 'Debes iniciar sesión para usar la API.'
        }), 401

    return None


@app.route('/api/auth/status', methods=['GET'])
def auth_status():
    return jsonify({
        'authenticated': is_authenticated(),
        'username': session.get('username') if is_authenticated() else None
    }), 200


@app.route('/api/auth/login', methods=['POST'])
def auth_login():
    payload = request.get_json(silent=True) or {}
    username = (payload.get('username') or '').strip()
    password = payload.get('password') or ''

    if not username or not password:
        return jsonify({
            'success': False,
            'error': 'Usuario y contraseña son obligatorios.'
        }), 400

    expected_user, expected_password = get_auth_credentials()

    if username != expected_user or password != expected_password:
        return jsonify({
            'success': False,
            'error': 'Credenciales inválidas.'
        }), 401

    session['authenticated'] = True
    session['username'] = username
    session.permanent = True

    return jsonify({
        'success': True,
        'username': username
    }), 200


@app.route('/api/auth/logout', methods=['POST'])
def auth_logout():
    session.pop('authenticated', None)
    session.pop('username', None)

    return jsonify({
        'success': True
    }), 200

# Cache para reducir llamadas a la API de Arduino
flowmeter_cache = {
    'data': None,
    'timestamp': None,
    'ttl': 8  # Time to live en segundos (8 segundos de caché)
}

def get_cached_flowmeter_data():
    """Retorna datos en caché si son válidos, None si no"""
    if flowmeter_cache['data'] and flowmeter_cache['timestamp']:
        elapsed = (datetime.now() - flowmeter_cache['timestamp']).total_seconds()
        if elapsed < flowmeter_cache['ttl']:
            return flowmeter_cache['data']
    return None

def set_flowmeter_cache(data):
    """Guarda datos en caché"""
    flowmeter_cache['data'] = data
    flowmeter_cache['timestamp'] = datetime.now()

def get_arduino_token():
    """Obtiene un token de acceso para la API de Arduino IoT Cloud"""
    client_id = settings.get('CLIENT_ID')
    client_secret = settings.get('CLIENT_SECRET')
    
    if not client_id or not client_secret:
        return None, "CLIENT_ID o CLIENT_SECRET no configurados"
    
    token_url = "https://api2.arduino.cc/iot/v1/clients/token"
    
    try:
        # Configurar el cliente OAuth2
        oauth_client = BackendApplicationClient(client_id=client_id)
        oauth = OAuth2Session(client=oauth_client)
        
        # Obtener el token
        token = oauth.fetch_token(
            token_url=token_url,
            client_id=client_id,
            client_secret=client_secret,
            include_client_id=True,
            audience="https://api2.arduino.cc/iot"
        )
        # Obtener el access token
        access_token = token.get("access_token")
        
        if not access_token:
            return None, "No se encontró access_token en la respuesta"
        
        return access_token, None
        
    except Exception as e:
        return None, f"Error de autenticación: {str(e)}"

@app.route("/api/arduino/flowmeter", methods=['GET'])
def get_flowmeter_data():
    """Obtiene los datos del flujómetro desde Arduino IoT Cloud con caché"""
    try:
        # Verificar si hay datos en caché válidos
        cached_data = get_cached_flowmeter_data()
        if cached_data:
            return jsonify({
                "success": True,
                "data": cached_data,
                "cached": True
            }), 200
        access_token, error = get_arduino_token()

        if error:
            return jsonify({
                "error": "Error de autenticación",
                "details": error
            }), 401

        # Obtener todos los things
        api_url = "https://api2.arduino.cc/iot/v2/things"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        response = requests.get(api_url, headers=headers)
        
        # Manejar rate limiting
        if response.status_code == 429:
            # Si hay datos en caché aunque sean viejos, usarlos
            if flowmeter_cache['data']:
                return jsonify({
                    "success": True,
                    "data": flowmeter_cache['data'],
                    "cached": True,
                    "warning": "Rate limit alcanzado, usando datos en caché"
                }), 200
            return jsonify({
                "error": "Rate limit alcanzado",
                "details": "Demasiadas peticiones. Intenta de nuevo en unos segundos."
            }), 429
        
        if response.status_code != 200:
            return jsonify({
                "error": "Error al obtener things",
                "status_code": response.status_code,
                "details": response.text
            }), response.status_code

        things_data = response.json()
        
        # Buscar el thing llamado "Medidor de Flujo"
        flowmeter_thing = None
        for thing in things_data:
            if thing.get('name') == 'Medidor de Flujo':
                flowmeter_thing = thing
                break
        
        if not flowmeter_thing:
            return jsonify({
                "error": "No se encontró el thing 'Medidor de Flujo'",
                "available_things": [t.get('name') for t in things_data]
            }), 404

        # Obtener las propiedades del thing
        thing_id = flowmeter_thing.get('id')
        properties_url = f"https://api2.arduino.cc/iot/v2/things/{thing_id}/properties"
        
        properties_response = requests.get(properties_url, headers=headers)
        
        if properties_response.status_code != 200:
            return jsonify({
                "error": "Error al obtener propiedades",
                "status_code": properties_response.status_code
            }), properties_response.status_code

        properties = properties_response.json()
        
        # Extraer instflow y constflow
        flowmeter_data = {
            "thing_name": flowmeter_thing.get('name'),
            "thing_id": thing_id,
            "instflow": None,
            "constflow": None,
            "last_update": None
        }
        
        for prop in properties:
            prop_name = prop.get('name', '').lower()
            if 'instflow' in prop_name:
                flowmeter_data['instflow'] = {
                    "value": prop.get('last_value'),
                    "updated_at": prop.get('value_updated_at')
                }
            elif 'constflow' in prop_name:
                flowmeter_data['constflow'] = {
                    "value": prop.get('last_value'),
                    "updated_at": prop.get('value_updated_at')
                }
        
        # Guardar en caché
        set_flowmeter_cache(flowmeter_data)
        
        return jsonify({
            "success": True,
            "data": flowmeter_data,
            "cached": False
        }), 200

    except Exception as e:
        print(f"\nError inesperado: {e}")
        # En caso de error, intentar usar caché aunque sea viejo
        if flowmeter_cache['data']:
            return jsonify({
                "success": True,
                "data": flowmeter_cache['data'],
                "cached": True,
                "warning": "Error en la API, usando datos en caché"
            }), 200
        return jsonify({
            "error": "Error inesperado",
            "details": str(e)
        }), 500


@app.route("/api/weather")
def get_weather_empty():
    """Obtiene datos meteorológicos usando la estación por defecto configurada en .env"""
    from app.utils.weathercloud_py import WeathercloudAPI
    
    # Obtener la ID de estación desde las variables de entorno
    default_station = settings.get('WEATHERCLOUD_DEVICEID')
    if not default_station:
        return jsonify({
            "error": "No se ha configurado una estación por defecto en WEATHER_CLOUD_DEVICEID"
        }), 400
        
    try:
        weather_api = WeathercloudAPI()
    except ValueError as e:
        return jsonify({"error": str(e)}), 401
        
    data = weather_api.get_weather(default_station)

    if "error" in data:
        if "autenticación" in data["error"].lower():
            return jsonify(data), 401
        elif "ID inválido" in data["error"]:
            return jsonify(data), 400
        return jsonify(data), 500
        
    return jsonify(data)


@app.route("/api/weather/<station_id>")
def get_weather_station(station_id):
    """Obtiene datos meteorológicos de una estación específica de Weathercloud"""
    from app.utils.weathercloud_py import WeathercloudAPI
    weather_api = WeathercloudAPI()
    
    data = weather_api.get_weather(station_id)
    return jsonify(data)


@app.route("/api/weather/nearest")
def get_nearest_stations():
    """Obtiene estaciones meteorológicas cercanas a las coordenadas especificadas"""
    try:
        from app.utils.weathercloud_py import WeathercloudAPI
        weather_api = WeathercloudAPI()
        
        lat = float(request.args.get('lat', 0))
        lon = float(request.args.get('lon', 0))
        radius = int(request.args.get('radius', 10))
        
        stations = weather_api.get_nearest(lat, lon, radius)
        return jsonify(stations)
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/weather/profile/<station_id>")
def get_station_profile(station_id):
    """Obtiene el perfil de una estación meteorológica"""
    from app.utils.weathercloud_py import WeathercloudAPI
    weather_api = WeathercloudAPI()
    
    data = weather_api.get_profile(station_id)
    return jsonify(data)


@app.route("/api/weather/statistics/<station_id>")
def get_station_statistics(station_id):
    """Obtiene estadísticas de una estación meteorológica"""
    from app.utils.weathercloud_py import WeathercloudAPI
    weather_api = WeathercloudAPI()
    
    data = weather_api.get_statistics(station_id)
    return jsonify(data)


@app.route("/api/visitas", methods=['POST'])
def add_visitas():
    """Añade una visita"""
    num_visitas = config.incrementar_visitas()
    return jsonify({"num_visitas": num_visitas})


@app.route("/api/informes", methods=['GET'])
def get_informes():
    """Obtiene la lista de informes disponibles"""
    import os
    from datetime import datetime
    
    # Crear directorio de informes si no existe
    informes_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../informes')
    informes_dir = os.path.normpath(informes_dir)
    
    if not os.path.exists(informes_dir):
        os.makedirs(informes_dir)
    
    # Listar archivos de informes
    informes = []
    for filename in os.listdir(informes_dir):
        if filename.endswith('.json'):
            filepath = os.path.join(informes_dir, filename)
            # Obtener información del archivo
            file_stat = os.stat(filepath)
            file_time = datetime.fromtimestamp(file_stat.st_mtime)
            
            # Leer el contenido del informe
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    import json
                    informe_data = json.load(f)
                    
                informes.append({
                    'id': filename.replace('.json', ''),
                    'nombre': informe_data.get('nombre', filename),
                    'fecha': file_time.strftime('%d/%m/%Y'),
                    'fecha_completa': file_time.strftime('%d/%m/%Y %H:%M'),
                    'periodo': informe_data.get('periodo', 'N/A'),
                    'datos': informe_data
                })
            except:
                continue
    
    # Ordenar por fecha (más reciente primero)
    informes.sort(key=lambda x: x['fecha_completa'], reverse=True)
    
    return jsonify({
        "success": True,
        "informes": informes
    })


@app.route("/api/informes/generar", methods=['POST'])
def generar_informe():
    """Genera un nuevo informe de caudal - SOLO MENSUAL"""
    import os
    import json
    from datetime import datetime, timedelta
    import calendar
    
    try:
        # Crear directorio de informes si no existe
        informes_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../informes')
        informes_dir = os.path.normpath(informes_dir)
        
        if not os.path.exists(informes_dir):
            os.makedirs(informes_dir)
        
        # VALIDAR: Verificar si ya existe un informe del mes actual
        fecha_actual = datetime.now()
        mes_actual = fecha_actual.month
        anio_actual = fecha_actual.year
        
        # Buscar informes existentes del mes actual
        for filename in os.listdir(informes_dir):
            if filename.endswith('.json'):
                try:
                    filepath = os.path.join(informes_dir, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        informe_existente = json.load(f)
                    
                    # Extraer fecha de generación del informe existente
                    fecha_gen_str = informe_existente.get('fecha_generacion', '')
                    if fecha_gen_str:
                        # Parsear fecha: "03/11/2025 02:14:51"
                        fecha_gen = datetime.strptime(fecha_gen_str, '%d/%m/%Y %H:%M:%S')
                        
                        # Verificar si es del mismo mes y año
                        if fecha_gen.month == mes_actual and fecha_gen.year == anio_actual:
                            # Calcular días transcurridos desde el informe
                            dias_transcurridos = (fecha_actual - fecha_gen).days
                            
                            # Obtener días del mes actual
                            dias_en_mes = calendar.monthrange(anio_actual, mes_actual)[1]
                            
                            # Si no han pasado los días del mes, no permitir generar
                            if dias_transcurridos < dias_en_mes:
                                return jsonify({
                                    "success": False,
                                    "error": f"Ya existe un informe del mes actual generado el {fecha_gen.strftime('%d/%m/%Y')}. Debe esperar {dias_en_mes - dias_transcurridos} días más para generar un nuevo informe mensual.",
                                    "dias_restantes": dias_en_mes - dias_transcurridos,
                                    "informe_existente": {
                                        'id': filename.replace('.json', ''),
                                        'fecha': fecha_gen.strftime('%d/%m/%Y'),
                                        'nombre': informe_existente.get('nombre', '')
                                    }
                                }), 400
                except Exception as e:
                    print(f"Error al verificar informe {filename}: {e}")
                    continue
        
        # Obtener datos del flujómetro
        flowmeter_data = None
        if flowmeter_cache['data']:
            flowmeter_data = flowmeter_cache['data']
        else:
            # Intentar obtener datos frescos
            access_token, error = get_arduino_token()
            if not error:
                # Simplificado: usar datos en caché o simulados
                flowmeter_data = {
                    'instflow': {'value': 0},
                    'constflow': {'value': 0}
                }
        
        # Solo permitir informes mensuales
        periodo_nombre = "Último Mes"
        fecha_fin = datetime.now()
        # Calcular el primer día del mes anterior
        if fecha_fin.month == 1:
            fecha_inicio = datetime(fecha_fin.year - 1, 12, 1)
        else:
            fecha_inicio = datetime(fecha_fin.year, fecha_fin.month - 1, 1)
        
        # Calcular días del período para promedios
        dias_periodo = (fecha_fin - fecha_inicio).days
        
        # Calcular días del período para promedios
        dias_periodo = (fecha_fin - fecha_inicio).days
        
        # Crear estructura del informe
        informe = {
            'nombre': f'Informe de Caudal - {periodo_nombre}',
            'fecha_generacion': fecha_fin.strftime('%d/%m/%Y %H:%M:%S'),
            'periodo': periodo_nombre,
            'fecha_inicio': fecha_inicio.strftime('%d/%m/%Y'),
            'fecha_fin': fecha_fin.strftime('%d/%m/%Y'),
            'mes_anio': f"{fecha_fin.month}/{fecha_fin.year}",  # Para validaciones futuras
            'datos': {
                'flujo_instantaneo': flowmeter_data.get('constflow', {}).get('value', 0) if flowmeter_data else 0,
                'flujo_acumulado': flowmeter_data.get('instflow', {}).get('value', 0) if flowmeter_data else 0,
                'promedio_diario': (flowmeter_data.get('instflow', {}).get('value', 0) / dias_periodo) if flowmeter_data and dias_periodo > 0 else 0,
            },
            'estadisticas': {
                'total_litros': flowmeter_data.get('instflow', {}).get('value', 0) if flowmeter_data else 0,
                'promedio_lmin': flowmeter_data.get('constflow', {}).get('value', 0) if flowmeter_data else 0,
            }
        }
        
        # Guardar informe
        filename = f"informe_{fecha_fin.strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(informes_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(informe, f, indent=2, ensure_ascii=False)
        
        return jsonify({
            "success": True,
            "message": "Informe generado exitosamente",
            "informe": {
                'id': filename.replace('.json', ''),
                'nombre': informe['nombre'],
                'fecha': fecha_fin.strftime('%d/%m/%Y'),
                'periodo': periodo_nombre
            }
        })
        
    except Exception as e:
        print(f"Error al generar informe: {e}")
        return jsonify({
            "error": "Error al generar informe",
            "details": str(e)
        }), 500


@app.route("/api/informes/<informe_id>", methods=['GET'])
def get_informe(informe_id):
    """Obtiene un informe específico"""
    import os
    import json
    
    try:
        informes_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../informes')
        informes_dir = os.path.normpath(informes_dir)
        
        filepath = os.path.join(informes_dir, f"{informe_id}.json")
        
        if not os.path.exists(filepath):
            return jsonify({
                "error": "Informe no encontrado"
            }), 404
        
        with open(filepath, 'r', encoding='utf-8') as f:
            informe = json.load(f)
        
        return jsonify({
            "success": True,
            "informe": informe
        })
        
    except Exception as e:
        return jsonify({
            "error": "Error al obtener informe",
            "details": str(e)
        }), 500


@app.route("/api/informes/<informe_id>", methods=['DELETE'])
def delete_informe(informe_id):
    """Elimina un informe"""
    import os
    
    try:
        informes_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../informes')
        informes_dir = os.path.normpath(informes_dir)
        
        filepath = os.path.join(informes_dir, f"{informe_id}.json")
        
        if not os.path.exists(filepath):
            return jsonify({
                "error": "Informe no encontrado"
            }), 404
        
        os.remove(filepath)
        
        return jsonify({
            "success": True,
            "message": "Informe eliminado exitosamente"
        })
        
    except Exception as e:
        return jsonify({
            "error": "Error al eliminar informe",
            "details": str(e)
        }), 500
