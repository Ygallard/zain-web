from django.urls import path

from . import views


app_name = "flujometro"

urlpatterns = [
    path("", views.index, name="index"),
    path("health/", views.health, name="health"),
    path("api/arduino/flowmeter", views.flowmeter_data, name="flowmeter_data"),
    path("api/auth/status", views.auth_status, name="auth_status"),
    path("api/auth/login", views.auth_login, name="auth_login_no_slash"),
    path("api/auth/login/", views.auth_login, name="auth_login"),
    path("api/auth/logout", views.auth_logout, name="auth_logout_no_slash"),
    path("api/auth/logout/", views.auth_logout, name="auth_logout"),
    path("api/cuaderno/quick-stats", views.quick_stats, name="quick_stats"),
    path("api/weather", views.weather_current, name="weather"),
    path("api/weather/current/", views.weather_current, name="weather_current"),
    path("api/visitas", views.visitas, name="visitas"),
    path("api/informes", views.informes, name="informes"),
    path("api/informes/generar", views.generar_informe, name="generar_informe"),
    path("api/informes/<str:informe_id>", views.informe_detail, name="informe_detail"),
]