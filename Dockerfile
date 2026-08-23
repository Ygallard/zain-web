# Django deployment image. The repository root is the build context in UrraHosting.
FROM python:3.11-slim

WORKDIR /app

COPY cuaderno_campo_django/requirements.txt ./requirements.txt

RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY cuaderno_campo_django/ ./

RUN groupadd --gid 10001 appuser \
	&& useradd --uid 10001 --gid 10001 --create-home --shell /usr/sbin/nologin appuser \
	&& chown -R 10001:10001 /app

EXPOSE 8000

USER 10001:10001

CMD ["sh", "-c", "gunicorn cuaderno_campo_django.wsgi:application --bind 0.0.0.0:${PORT}"]
