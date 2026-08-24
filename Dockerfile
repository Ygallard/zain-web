# Django deployment image. The repository root is the build context in UrraHosting.
FROM python:3.11-slim AS builder

WORKDIR /app

COPY requirements.txt ./requirements.txt

RUN python -m venv /opt/venv \
	&& /opt/venv/bin/pip install --no-cache-dir --upgrade pip \
	&& /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

COPY cuaderno_campo_django/ ./

RUN /opt/venv/bin/python manage.py collectstatic --noinput

FROM python:3.11-slim AS runtime

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY cuaderno_campo_django/ ./
COPY --from=builder /app/staticfiles ./staticfiles
COPY gunicorn.conf.py ./gunicorn.conf.py

RUN groupadd --gid 10001 appuser \
	&& useradd --uid 10001 --gid 10001 --create-home --shell /usr/sbin/nologin appuser \
	&& chown -R 10001:10001 /app

ENV PATH=/opt/venv/bin:$PATH \
	HOME=/tmp \
	XDG_CONFIG_HOME=/tmp

EXPOSE 8000

USER 10001:10001

CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py bootstrap_admin && exec gunicorn -c gunicorn.conf.py cuaderno_campo_django.wsgi:application"]
