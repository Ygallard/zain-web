import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def load_env_file(path):
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


# The shared integrations live in the repository-root .env; Django-specific
# settings may override them in cuaderno_campo_django/.env.
load_env_file(BASE_DIR.parent / ".env")
load_env_file(BASE_DIR / ".env")

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "django-insecure-change-this-in-production")
DEBUG = os.getenv("DJANGO_DEBUG", "True").lower() == "true"
WEATHERCLOUD_EMAIL = os.getenv("WEATHERCLOUD_EMAIL", "")
WEATHERCLOUD_PASSWORD = os.getenv("WEATHERCLOUD_PASSWORD", "")
WEATHERCLOUD_DEVICEID = os.getenv("WEATHERCLOUD_DEVICEID", "d5189955137")

# Configuración de Hosts permitidos (acepta variables de entorno o '*' por defecto para PaaS)
raw_hosts = os.getenv("DJANGO_ALLOWED_HOSTS", "*")
ALLOWED_HOSTS = [h.strip() for h in raw_hosts.split(",") if h.strip()]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "usuarios",
    "flujometro",
]

MIDDLEWARE = [
    "cuaderno_campo_django.middleware.PlatformHealthMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "usuarios.middleware.RoleBasedAccessMiddleware",
]

ROOT_URLCONF = "cuaderno_campo_django.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "cuaderno_campo_django.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "cuaderno_campo"),
        "USER": os.getenv("DB_USER", "postgres"),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es-cl"
TIME_ZONE = "America/Santiago"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "login"
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False
SESSION_COOKIE_AGE = int(os.getenv("DJANGO_SESSION_COOKIE_AGE", "43200"))
SESSION_EXPIRE_AT_BROWSER_CLOSE = os.getenv("DJANGO_SESSION_EXPIRE_AT_BROWSER_CLOSE", "True").lower() == "true"

# Permitir iframes para integraciones externas autorizadas.
X_FRAME_OPTIONS = 'ALLOWALL'

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Confiar en solicitudes CSRF desde entorno local y subdominios de UrraHosting
raw_csrf = os.getenv(
    "CSRF_TRUSTED_ORIGINS",
    "http://127.0.0.1:5000,http://localhost:5000,https://*.urrahosting.com,https://*.urrahosting.cl",
)
CSRF_TRUSTED_ORIGINS = []
for origin in raw_csrf.split(","):
    origin = origin.strip()
    if not origin:
        continue
    if origin.startswith(("http//", "https//")):
        origin = origin.replace("//", "://", 1)
    elif "://" not in origin:
        origin = f"https://{origin}"
    CSRF_TRUSTED_ORIGINS.append(origin)

