import os
from datetime import datetime, timedelta

import requests
from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session


class ArduinoFlowmeterService:
    cache = {"data": None, "timestamp": None}
    cache_ttl = 8

    def get_data(self):
        cached = self._get_cached()
        if cached is not None:
            return {"success": True, "data": cached, "cached": True}, 200

        access_token, error = self._get_token()
        if error:
            return {"error": "Error de autenticación", "details": error}, 401

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        try:
            response = requests.get(
                "https://api2.arduino.cc/iot/v2/things",
                headers=headers,
                timeout=10,
            )
            if response.status_code == 429:
                if self.cache["data"] is not None:
                    return {
                        "success": True,
                        "data": self.cache["data"],
                        "cached": True,
                        "warning": "Rate limit alcanzado, usando datos en caché",
                    }, 200
                return {"error": "Rate limit alcanzado"}, 429
            response.raise_for_status()
            things = response.json()
            thing = next((item for item in things if item.get("name") == "Medidor de Flujo"), None)
            if not thing:
                return {
                    "error": "No se encontró el thing 'Medidor de Flujo'",
                    "available_things": [item.get("name") for item in things],
                }, 404

            properties_response = requests.get(
                f"https://api2.arduino.cc/iot/v2/things/{thing['id']}/properties",
                headers=headers,
                timeout=10,
            )
            properties_response.raise_for_status()
            data = {
                "thing_name": thing.get("name"),
                "thing_id": thing.get("id"),
                "instflow": None,
                "constflow": None,
                "last_update": None,
            }
            for prop in properties_response.json():
                name = prop.get("name", "").lower()
                if "instflow" in name:
                    data["instflow"] = {
                        "value": prop.get("last_value"),
                        "updated_at": prop.get("value_updated_at"),
                    }
                elif "constflow" in name:
                    data["constflow"] = {
                        "value": prop.get("last_value"),
                        "updated_at": prop.get("value_updated_at"),
                    }
            self.cache = {"data": data, "timestamp": datetime.now()}
            return {"success": True, "data": data, "cached": False}, 200
        except requests.RequestException as exc:
            if self.cache["data"] is not None:
                return {
                    "success": True,
                    "data": self.cache["data"],
                    "cached": True,
                    "warning": "Error en Arduino, usando datos en caché",
                }, 200
            return {"error": "No se pudo consultar Arduino", "details": str(exc)}, 502

    def _get_cached(self):
        if self.cache["data"] is None or self.cache["timestamp"] is None:
            return None
        if datetime.now() - self.cache["timestamp"] < timedelta(seconds=self.cache_ttl):
            return self.cache["data"]
        return None

    def _get_token(self):
        client_id = os.getenv("CLIENT_ID")
        client_secret = os.getenv("CLIENT_SECRET")
        if not client_id or not client_secret:
            return None, "CLIENT_ID o CLIENT_SECRET no configurados"
        try:
            client = BackendApplicationClient(client_id=client_id)
            oauth = OAuth2Session(client=client)
            token = oauth.fetch_token(
                token_url="https://api2.arduino.cc/iot/v1/clients/token",
                client_id=client_id,
                client_secret=client_secret,
                include_client_id=True,
                audience="https://api2.arduino.cc/iot",
            )
            access_token = token.get("access_token")
            return (access_token, None) if access_token else (None, "No se encontró access_token")
        except Exception as exc:
            return None, f"Error de autenticación: {exc}"