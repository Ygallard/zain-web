# weathercloud_py.py
import requests
import json
import os
from app.utils import config

class WeathercloudAPI:
    BASE_URL = "https://app.weathercloud.net"
    
    def __init__(self):
        settings = config.load_config()
        
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "X-Requested-With": "XMLHttpRequest"
        })
        self.cookie = None
        self.email = settings.get('WEATHERCLOUD_EMAIL', '')
        self.password = settings.get('WEATHERCLOUD_PASSWORD', '')
        self.is_authenticated = False
        
        if not self.email or not self.password:
            raise ValueError("WEATHERCLOUD_EMAIL y WEATHERCLOUD_PASSWORD son requeridos en .env")
    
    def is_authenticated_session(self):
        """
        Verifica si la sesión actual está autenticada
        
        Returns:
            bool: True si la sesión está autenticada
        """
        if not self.cookie:
            return False
            
        try:
            # Intenta hacer una petición simple para verificar la sesión
            response = self.session.get(f"{self.BASE_URL}/profile")
            return response.status_code == 200
        except:
            return False

    def login(self, email=None, password=None, store_credentials=True):
        """
        Inicia sesión en Weathercloud
        
        Args:
            email (str): Correo electrónico (opcional si ya se cargó del .env)
            password (str): Contraseña (opcional si ya se cargó del .env)
            store_credentials (bool): Almacenar credenciales para reautenticación
            
        Returns:
            dict: {"success": bool, "error": str or None}
        """
        try:
            email = email or self.email
            password = password or self.password
            
            if not email or not password:
                return {"success": False, "error": "Credenciales no proporcionadas"}
            
            data = {
                "entity": email,
                "password": password,
                "rememberMe": "1" if store_credentials else "0"
            }
            
            response = self.session.post(f"{self.BASE_URL}/signin", data=data, allow_redirects=False)
            
            if response.status_code == 200 or response.status_code == 302:
                self.cookie = response.cookies.get_dict()
                self.is_authenticated = True
                if store_credentials:
                    self.credentials = {"email": email, "password": password}
                return {"success": True, "error": None}
            
            return {"success": False, "error": "Credenciales inválidas"}
        except Exception as e:
            return {"success": False, "error": f"Error en login: {str(e)}"}
    
    def check_id(self, id_):
        """
        Verifica si el ID es válido y retorna el tipo
        
        Args:
            id_ (str): ID de la estación
            
        Returns:
            str: "device" o "metar" según corresponda
        """
        # ID de METAR son 4 letras (código OACI)
        if len(id_) == 4 and id_.isalpha():
            return "metar"
        # ID de dispositivos son números (normalmente 10 dígitos y inician con 'd')
        elif id_[0] == "d" and id_[1:].isdigit() and len(id_) >= 11 or id_.isdigit() and len(id_) >= 10:
            return "device"
        return None
    
    def ensure_authenticated(self):
        """
        Asegura que la sesión está autenticada, intenta re-autenticar si es necesario
        
        Returns:
            dict: {"success": bool, "error": str or None}
        """
        if self.is_authenticated and self.is_authenticated_session():
            return {"success": True, "error": None}
            
        # Intentar login
        return self.login()

    def get_weather(self, id_):
        """
        Obtiene datos meteorológicos actuales
        
        Args:
            id_ (str): ID de la estación o METAR
            
        Returns:
            dict: Datos meteorológicos o error
        """
        # Verificar autenticación
        auth_result = self.ensure_authenticated()
        if not auth_result["success"]:
            return {"error": f"Error de autenticación: {auth_result['error']}"}
            
        try:
            id_type = self.check_id(id_)
            if not id_type:
                return {"error": "ID inválido"}
            
            url = f"{self.BASE_URL}/{id_type}/values"
            response = self.session.post(url, params={"code": id_})
            
            if response.status_code == 200:
                data = response.json()
                
                # Calcular altura de nubes
                clouds_height = None
                if "temp" in data and "dew" in data and isinstance(data["temp"], (int, float)) and isinstance(data["dew"], (int, float)):
                    if data["temp"] > -40 and data["dew"] > -40:
                        clouds_height = max(0, 124.69 * (data["temp"] - data["dew"]))
                
                # Agregar datos calculados
                data["computed"] = {
                    "cloudsHeight": clouds_height,
                    "feel": None,  # Se podría implementar cálculos adicionales
                    "weatherAvg": None
                }
                
                # Corregir visibilidad si está presente
                if "vis" in data and isinstance(data["vis"], (int, float)):
                    data["vis"] = data["vis"] * 100
                
                return data
            elif response.status_code == 401:
                return {"error": "Sesión expirada o no autorizada"}
            return {"error": "Error al obtener datos"}
        except Exception as e:
            return {"error": str(e)}
    
    def get_profile(self, id_):
        """
        Obtiene el perfil de una estación
        
        Args:
            id_ (str): ID de la estación o METAR
            
        Returns:
            dict: Datos del perfil
        """
        try:
            id_type = self.check_id(id_)
            if not id_type:
                return {"error": "ID inválido"}
            
            url = f"{self.BASE_URL}/{id_type}/ajaxprofile"
            response = self.session.post(url, data={"d": id_})
            
            if response.status_code == 200:
                data = response.json()
                if "followers" not in data:
                    return {"error": "Error al obtener datos"}
                return data
            return {"error": "Error en la solicitud"}
        except Exception as e:
            return {"error": str(e)}
    
    def get_infos(self, id_):
        """
        Obtiene información general de una estación
        
        Args:
            id_ (str): ID de la estación o METAR
            
        Returns:
            dict: Información de la estación
        """
        try:
            id_type = self.check_id(id_)
            if not id_type:
                return {"error": "ID inválido"}
            
            url = f"{self.BASE_URL}/{id_type}/info/{id_}"
            response = self.session.post(url)
            
            if response.status_code == 200:
                return response.json()
            return {"error": "Error en la solicitud"}
        except Exception as e:
            return {"error": str(e)}
    
    def get_wind(self, id_):
        """
        Obtiene datos históricos de viento
        
        Args:
            id_ (str): ID de la estación o METAR
            
        Returns:
            dict: Datos de viento
        """
        try:
            id_type = self.check_id(id_)
            if not id_type:
                return {"error": "ID inválido"}
            
            url = f"{self.BASE_URL}/{id_type}/wind"
            response = self.session.post(url, params={"code": id_})
            
            if response.status_code == 200:
                data = response.json()
                
                # Procesar datos de viento
                wdirdist_data = [sum(item["values"]["scale"]) for item in data]
                total = sum(wdirdist_data) + 0.0001  # Evitar división por cero
                calm = wdirdist_data[0]
                
                # Calcular proporciones
                wdir_proportions = [(wdir / total) * 100 for wdir in wdirdist_data]
                
                return {
                    "date": data[0]["date"] if data else None,
                    "wdirproportions": wdir_proportions,
                    "calm": (calm/total) * 100,
                    "raw": data
                }
            return {"error": "Error en la solicitud"}
        except Exception as e:
            return {"error": str(e)}
    
    def get_statistics(self, id_):
        """
        Obtiene estadísticas de la estación
        
        Args:
            id_ (str): ID de la estación
            
        Returns:
            dict: Estadísticas
        """
        try:
            id_type = self.check_id(id_)
            if not id_type:
                return {"error": "ID inválido"}
            
            url = f"{self.BASE_URL}/{id_type}/stats"
            response = self.session.post(url, data={"code": id_})
            
            if response.status_code == 200:
                return response.json()
            return {"error": "Error en la solicitud"}
        except Exception as e:
            return {"error": str(e)}
    
    def get_nearest(self, lat, lon, radius):
        """
        Obtiene estaciones cercanas a una ubicación
        
        Args:
            lat (float): Latitud
            lon (float): Longitud
            radius (int): Radio en km
            
        Returns:
            list: Lista de estaciones cercanas
        """
        try:
            url = f"{self.BASE_URL}/page/coordinates/latitude/{lat}/longitude/{lon}/distance/{radius}"
            response = self.session.post(url)
            
            if response.status_code == 200:
                return response.json()
            return {"error": "Error en la solicitud"}
        except Exception as e:
            return {"error": str(e)}
