import django
from django.conf import settings
from django.test import Client

# manage.py shell already configures Django, but this keeps the script self-contained.
# If Django isn't configured yet, set it up explicitly.
try:
    django.setup()
except RuntimeError:
    pass

from usuarios.models import Usuario, Notificacion

print('DJANGO_SETUP_OK')

tecnico = Usuario.objects.filter(rol='tecnico', estado=True).order_by('id').first()
productor = Usuario.objects.filter(rol='productor', estado=True).order_by('id').first()

if tecnico is None or productor is None:
    print('NO HAY USUARIO tecnico/estado=True O productor/estado=True')
    raise SystemExit

print('TECNICO', {'id': tecnico.id, 'usuario': tecnico.usuario, 'nombre': tecnico.nombre, 'rol': tecnico.rol})
print('PRODUCTOR', {'id': productor.id, 'usuario': productor.usuario, 'nombre': productor.nombre, 'rol': productor.rol})

c = Client()
s = c.session
s['usuario_id'] = tecnico.id
s['rol'] = 'tecnico'
s['nombre'] = tecnico.nombre
s['usuario'] = tecnico.usuario
s.save()
c.cookies[settings.SESSION_COOKIE_NAME] = s.session_key
print('SESSION_TEcnico', {'session_key': s.session_key, 'session_data': dict(s)})

resp = c.post(
    '/notificaciones/crear/',
    {'productor_id': productor.id, 'titulo': 'Test titulo', 'mensaje': 'Test mensaje completo'},
    HTTP_X_REQUESTED_WITH='XMLHttpRequest',
)
print('POST_STATUS', resp.status_code)
print('POST_CONTENT', resp.content.decode('utf-8', 'replace'))

c2 = Client()
s2 = c2.session
s2['usuario_id'] = productor.id
s2['rol'] = 'productor'
s2['nombre'] = productor.nombre
s2['usuario'] = productor.usuario
s2.save()
c2.cookies[settings.SESSION_COOKIE_NAME] = s2.session_key
print('SESSION_Productor', {'session_key': s2.session_key, 'session_data': dict(s2)})

resp2 = c2.get('/notificaciones/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
print('GET_STATUS', resp2.status_code)
print('GET_CONTENT', resp2.content.decode('utf-8', 'replace'))

qs = list(Notificacion.objects.filter(productor_id=productor.id).values())
print('DB_QUERY', qs)
