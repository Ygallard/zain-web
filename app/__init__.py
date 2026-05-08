from flask import Flask
from app.utils import config

# Cargar configuración
settings = config.load_config()

app = Flask(__name__)

# Configurar SECRET_KEY para sesiones
app.config['SECRET_KEY'] = settings.get('SECRET_KEY')