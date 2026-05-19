from django.urls import path

from . import views
from . import api

urlpatterns = [
    # Autenticación
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("api/dashboard/stats/", views.dashboard_stats_api, name="dashboard_stats_api"),
    path("acceso-denegado/", views.acceso_denegado_view, name="acceso_denegado"),
    path("auditoria/logs/", views.auditoria_logs_view, name="auditoria_logs"),

    # API endpoints para autenticación centralizada
    path("api/auth/login/", api.auth_login, name="api_auth_login"),
    path("api/auth/validate/", api.auth_validate, name="api_auth_validate"),
    path("api/auth/user-info/", api.auth_user_info, name="api_auth_user_info"),
    path("api/auth/logout/", api.auth_logout, name="api_auth_logout"),
    path("api/auth/sso/", api.auth_sso, name="api_auth_sso"),
    path("api/auth/activity/", api.auth_activity_log, name="api_auth_activity"),

    # Usuarios
    path("usuarios/", views.usuario_list_view, name="usuarios_lista"),
    path("usuarios/crear/", views.usuario_create_view, name="usuarios_crear"),
    path("usuarios/<int:pk>/", views.usuario_detail_view, name="usuarios_detalle"),
    path("usuarios/<int:pk>/editar/", views.usuario_update_view, name="usuarios_editar"),
    path("usuarios/<int:pk>/toggle-estado/", views.usuario_toggle_estado_view, name="usuarios_toggle_estado"),
    path("usuarios/<int:pk>/eliminar/", views.usuario_delete_view, name="usuarios_eliminar"),

    # Predios
    path("predios/", views.predio_list_view, name="predios_lista"),
    path("predios/crear/", views.predio_create_view, name="predios_crear"),
    path("predios/<int:pk>/", views.predio_detail_view, name="predios_detalle"),
    path("predios/<int:pk>/editar/", views.predio_update_view, name="predios_editar"),
    path("predios/<int:pk>/toggle-estado/", views.predio_toggle_estado_view, name="predios_toggle_estado"),
    path("predios/<int:pk>/eliminar/", views.predio_delete_view, name="predios_eliminar"),

    # Cuarteles
    path("cuarteles/", views.cuartel_list_view, name="cuarteles_lista"),
    path("cuarteles/crear/", views.cuartel_create_view, name="cuarteles_crear"),
    path("cuarteles/<int:pk>/", views.cuartel_detail_view, name="cuarteles_detalle"),
    path("cuarteles/<int:pk>/editar/", views.cuartel_update_view, name="cuarteles_editar"),
    path("cuarteles/<int:pk>/toggle-estado/", views.cuartel_toggle_estado_view, name="cuarteles_toggle_estado"),
    path("cuarteles/<int:pk>/eliminar/", views.cuartel_delete_view, name="cuarteles_eliminar"),

    # Riegos
    path("riegos/", views.riego_list_view, name="riegos_lista"),
    path("riegos/gestion/", views.riego_gestion_view, name="riegos_gestion"),
    path("riegos/analitica/", views.riego_analitica_view, name="riegos_analitica"),
    path("api/riegos/analitica/", views.riego_analytics_api, name="riegos_analytics_api"),
    path("riegos/exportar/pdf/", views.riego_export_pdf_view, name="riegos_export_pdf"),
    path("riegos/exportar/excel/", views.riego_export_excel_view, name="riegos_export_excel"),
    path("riegos/crear/", views.riego_create_view, name="riegos_crear"),
    path("riegos/<int:pk>/", views.riego_detail_view, name="riegos_detalle"),
    path("riegos/<int:pk>/editar/", views.riego_update_view, name="riegos_editar"),
    path("riegos/<int:pk>/toggle-estado/", views.riego_toggle_estado_view, name="riegos_toggle_estado"),
    path("riegos/<int:pk>/eliminar/", views.riego_delete_view, name="riegos_eliminar"),

    # Fertilizaciones
    path("fertilizaciones/", views.fertilizaciones_list_view, name="fertilizaciones_lista"),
    path("fertilizaciones/analitica/", views.fertilizaciones_list_view, name="fertilizaciones_analitica"),
    path("api/fertilizaciones/analitica/", views.fertilizacion_analytics_api, name="fertilizacion_analytics_api"),
    path("fertilizaciones/crear/", views.fertilizacion_create_view, name="fertilizaciones_crear"),
    path("fertilizaciones/<int:pk>/", views.fertilizacion_detail_view, name="fertilizaciones_detalle"),
    path("fertilizaciones/<int:pk>/editar/", views.fertilizacion_update_view, name="fertilizaciones_editar"),
    path("fertilizaciones/<int:pk>/toggle-estado/", views.fertilizacion_toggle_estado_view, name="fertilizaciones_toggle_estado"),
    path("fertilizaciones/<int:pk>/eliminar/", views.fertilizacion_delete_view, name="fertilizaciones_eliminar"),

    # Cosechas
    path("cosechas/", views.cosechas_list_view, name="cosechas_lista"),
    path("cosechas/analitica/", views.cosechas_list_view, name="cosechas_analitica"),
    path("api/cosechas/analitica/", views.cosecha_analytics_api, name="cosecha_analytics_api"),
    path("cosechas/crear/", views.cosecha_create_view, name="cosechas_crear"),
    path("cosechas/<int:pk>/", views.cosecha_detail_view, name="cosechas_detalle"),
    path("cosechas/<int:pk>/editar/", views.cosecha_update_view, name="cosechas_editar"),
    path("cosechas/<int:pk>/toggle-estado/", views.cosecha_toggle_estado_view, name="cosechas_toggle_estado"),
    path("cosechas/<int:pk>/eliminar/", views.cosecha_delete_view, name="cosechas_eliminar"),

    # Aplicaciones Químicas
    path("aplicaciones-quimicas/", views.aplicaciones_quimicas_list_view, name="aplicaciones_quimicas_lista"),
    path("aplicaciones-quimicas/analitica/", views.aplicaciones_quimicas_list_view, name="aplicaciones_quimicas_analitica"),
    path("api/aplicaciones-quimicas/analitica/", views.aplicacion_quimica_analytics_api, name="aplicacion_quimica_analytics_api"),
    path("aplicaciones-quimicas/crear/", views.aplicacion_quimica_create_view, name="aplicaciones_quimicas_crear"),
    path("aplicaciones-quimicas/<int:pk>/", views.aplicacion_quimica_detail_view, name="aplicaciones_quimicas_detalle"),
    path("aplicaciones-quimicas/<int:pk>/editar/", views.aplicacion_quimica_update_view, name="aplicaciones_quimicas_editar"),
    path("aplicaciones-quimicas/<int:pk>/toggle-estado/", views.aplicacion_quimica_toggle_estado_view, name="aplicaciones_quimicas_toggle_estado"),
    path("aplicaciones-quimicas/<int:pk>/eliminar/", views.aplicacion_quimica_delete_view, name="aplicaciones_quimicas_eliminar"),

    # Predios - Cuarteles
    path("predios/<int:predio_id>/cuarteles/", views.cuarteles_por_predio_view, name="predios_cuarteles"),
]
