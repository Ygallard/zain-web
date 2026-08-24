import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cuaderno_campo_django.settings")

django_application = get_wsgi_application()


def application(environ, start_response):
	# UrraHosting ejecuta el health check con un Host interno no aceptado por Django.
	if environ.get("PATH_INFO") == "/":
		environ["HTTP_HOST"] = "localhost"
	return django_application(environ, start_response)
