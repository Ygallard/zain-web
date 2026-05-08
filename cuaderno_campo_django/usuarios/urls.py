from django.urls import path

from . import views

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard_view, name="dashboard"),

    path("usuarios/", views.usuario_list_view, name="usuarios_lista"),
    path("usuarios/crear/", views.usuario_create_view, name="usuarios_crear"),
    path("usuarios/<int:pk>/", views.usuario_detail_view, name="usuarios_detalle"),
    path("usuarios/<int:pk>/editar/", views.usuario_update_view, name="usuarios_editar"),
    path("usuarios/<int:pk>/toggle-estado/", views.usuario_toggle_estado_view, name="usuarios_toggle_estado"),
    path("usuarios/<int:pk>/eliminar/", views.usuario_delete_view, name="usuarios_eliminar"),
]
