# Modulo Gestion de Usuarios - Cuaderno de Campo Digital

Proyecto Django con PostgreSQL para gestionar usuarios con login, roles y CRUD.

## Stack
- Django
- PostgreSQL
- Django ORM
- Templates Django + Bootstrap

## Configuracion
1. Crea y activa entorno virtual.
2. Instala dependencias:
   - pip install django psycopg2-binary
3. Configura variables de entorno (ver `.env.example`).

## Base de datos
Configuracion esperada:
- host: localhost
- puerto: 5432
- base de datos: cuaderno_campo
- usuario: postgres
- password: desde variable DB_PASSWORD

## Migraciones
Si la tabla `usuarios` ya existe, ejecutar:
- python manage.py migrate --fake-initial

Si no existe:
- python manage.py migrate

## Ejecucion
- python manage.py runserver

## Roles
- admin: CRUD completo
- tecnico: visualizar y buscar usuarios
- productor: acceso limitado a su propia informacion

## Rutas principales
- /login/
- /dashboard/
- /usuarios/
- /usuarios/crear/
- /usuarios/<id>/editar/
- /usuarios/<id>/eliminar/
