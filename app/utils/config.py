import json
import os

from filelock import FileLock
from dotenv import load_dotenv


def get_visitas_path():
    visitas_path = os.path.abspath(
        os.path.expanduser(os.getenv("VISITAS_DATA_PATH", "/tmp/visitas.json"))
    )
    try:
        os.makedirs(os.path.dirname(visitas_path), exist_ok=True)
    except OSError:
        pass
    return visitas_path


def get_informes_dir():
    informes_dir = os.path.abspath(
        os.path.expanduser(os.getenv("INFORMES_DATA_DIR", "/tmp/informes"))
    )
    try:
        os.makedirs(informes_dir, exist_ok=True)
    except OSError:
        pass
    return informes_dir


def load_config():
    load_dotenv()

    secret_key = os.getenv("SECRET_KEY")
    if not secret_key:
        raise RuntimeError(
            "SECRET_KEY must be set through an environment variable before starting the application."
        )

    # Manejar el contador de visitas con tolerancia a fallos de archivo
    visitas_path = get_visitas_path()
    num_visitas = 0

    try:
        if not os.path.exists(visitas_path):
            with open(visitas_path, 'w') as f:
                json.dump({"num_visitas": 0}, f)

        with open(visitas_path, 'r') as f:
            visitas = json.load(f)
            num_visitas = visitas.get('num_visitas', 0)
    except OSError:
        # Si el sistema de archivos es read-only, arranca con 0 sin romper la app
        num_visitas = 0

    config = {
        "SECRET_KEY": secret_key,
        "CLIENT_ID": os.getenv("CLIENT_ID"),
        "CLIENT_SECRET": os.getenv("CLIENT_SECRET"),
        "AUTH_USERNAME": os.getenv("AUTH_USERNAME"),
        "AUTH_PASSWORD": os.getenv("AUTH_PASSWORD"),
        "WEATHERCLOUD_EMAIL": os.getenv("WEATHERCLOUD_EMAIL"),
        "WEATHERCLOUD_PASSWORD": os.getenv("WEATHERCLOUD_PASSWORD"),
        "WEATHERCLOUD_DEVICEID": os.getenv("WEATHERCLOUD_DEVICEID"),
        "NUM_VISITAS": num_visitas
    }
    
    return config

def get_port():
    load_dotenv()
    return int(os.getenv("PORT", 5000))

def incrementar_visitas():
    visitas_path = get_visitas_path()
    lock_path = visitas_path + '.lock'
    
    try:
        lock = FileLock(lock_path, timeout=10)
        with lock:
            if not os.path.exists(visitas_path):
                with open(visitas_path, 'w') as f:
                    json.dump({"num_visitas": 0}, f)
            with open(visitas_path, 'r') as f:
                visitas = json.load(f)
            visitas['num_visitas'] += 1
            with open(visitas_path, 'w') as f:
                json.dump(visitas, f)
            return visitas['num_visitas']
    except OSError:
        # Retorna un valor por defecto en caso de que no pueda escribir en el disco
        return 1