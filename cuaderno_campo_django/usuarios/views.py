from django.contrib import messages
from django.contrib.auth.hashers import check_password
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import redirect, render

from .decorators import AUTH_SESSION_KEY, login_required_custom, role_required
from .forms import LoginForm, UsuarioCreateForm, UsuarioUpdateForm
from .models import Usuario


def get_current_user(request):
    user_id = request.session.get(AUTH_SESSION_KEY)
    if not user_id:
        return None
    return Usuario.objects.filter(id=user_id, estado=True).first()


def login_view(request):
    if request.session.get(AUTH_SESSION_KEY):
        return redirect("dashboard")

    form = LoginForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        usuario_input = form.cleaned_data["usuario"].strip()
        password_input = form.cleaned_data["password"]

        usuario = Usuario.objects.filter(usuario=usuario_input, estado=True).first()

        if not usuario or not check_password(password_input, usuario.password):
            messages.error(request, "Credenciales inválidas.")
        else:
            request.session[AUTH_SESSION_KEY] = usuario.id
            request.session["rol"] = usuario.rol
            request.session["nombre"] = usuario.nombre
            request.session["usuario"] = usuario.usuario
            messages.success(request, "Sesión iniciada correctamente.")
            return redirect("dashboard")

    return render(request, "login.html", {"form": form})


@login_required_custom
def logout_view(request):
    request.session.flush()
    messages.success(request, "Sesión cerrada correctamente.")
    return redirect("login")


@login_required_custom
def dashboard_view(request):
    current_user = get_current_user(request)
    if not current_user:
        messages.error(request, "Tu sesión no es válida. Vuelve a iniciar sesión.")
        return redirect("login")

    context = {
        "current_user": current_user,
        "usuarios_count": Usuario.objects.count(),
        "total_usuarios": Usuario.objects.count() if current_user.rol == Usuario.ROL_ADMIN else None,
        "usuarios_activos": Usuario.objects.filter(estado=True).count() if current_user.rol == Usuario.ROL_ADMIN else None,
        "usuarios_inactivos": Usuario.objects.filter(estado=False).count() if current_user.rol == Usuario.ROL_ADMIN else None,
        "administradores": Usuario.objects.filter(rol=Usuario.ROL_ADMIN).count() if current_user.rol == Usuario.ROL_ADMIN else None,
    }
    return render(request, "dashboard.html", context)


@login_required_custom
def usuario_list_view(request):
    current_user = get_current_user(request)
    if not current_user:
        messages.error(request, "Tu sesión no es válida. Vuelve a iniciar sesión.")
        return redirect("login")

    # Solo administradores pueden ver la lista de usuarios
    if current_user.rol != Usuario.ROL_ADMIN:
        messages.error(request, "No tienes permisos para acceder a esta sección.")
        return redirect("dashboard")

    q = request.GET.get("q", "").strip()
    queryset = Usuario.objects.all()

    if q:
        queryset = queryset.filter(
            Q(rut__icontains=q)
            | Q(nombre__icontains=q)
            | Q(usuario__icontains=q)
            | Q(rol__icontains=q)
            | Q(sector__icontains=q)
        )

    return render(
        request,
        "usuarios_lista.html",
        {
            "usuarios": queryset,
            "q": q,
            "current_user": current_user,
        },
    )


@role_required(Usuario.ROL_ADMIN)
def usuario_create_view(request):
    if request.method == "POST":
        try:
            form = UsuarioCreateForm(request.POST)
            if form.is_valid():
                usuario = form.save()
                return JsonResponse({
                    "success": True,
                    "message": "Usuario creado correctamente.",
                    "usuario": {
                        "id": usuario.id,
                        "rut": usuario.rut,
                        "nombre": usuario.nombre,
                        "usuario": usuario.usuario,
                        "rol": usuario.rol,
                        "celular": usuario.celular,
                        "sector": usuario.sector,
                        "estado": usuario.estado,
                    }
                })
            else:
                errors = {field: error[0] for field, error in form.errors.items()}
                return JsonResponse({"success": False, "error": "Validación fallida", "errors": errors})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    
    return redirect("usuarios_lista")


@login_required_custom
def usuario_detail_view(request, pk):
    if request.session.get("rol") != Usuario.ROL_ADMIN:
        return JsonResponse({"success": False, "error": "No autorizado"}, status=403)

    try:
        usuario = Usuario.objects.get(pk=pk)
        return JsonResponse({
            "success": True,
            "usuario": {
                "id": usuario.id,
                "rut": usuario.rut,
                "nombre": usuario.nombre,
                "usuario": usuario.usuario,
                "rol": usuario.rol,
                "celular": usuario.celular,
                "sector": usuario.sector,
                "estado": usuario.estado,
                "created_at": usuario.created_at.strftime("%d/%m/%Y %H:%M"),
            }
        })
    except Usuario.DoesNotExist:
        return JsonResponse({"success": False, "error": "Usuario no encontrado"}, status=404)


@role_required(Usuario.ROL_ADMIN)
def usuario_update_view(request, pk):
    if request.method == "POST":
        try:
            usuario = Usuario.objects.get(pk=pk)
            form = UsuarioUpdateForm(request.POST, instance=usuario)
            if form.is_valid():
                usuario = form.save()
                return JsonResponse({
                    "success": True,
                    "message": "Usuario actualizado correctamente.",
                    "usuario": {
                        "id": usuario.id,
                        "rut": usuario.rut,
                        "nombre": usuario.nombre,
                        "usuario": usuario.usuario,
                        "rol": usuario.rol,
                        "celular": usuario.celular,
                        "sector": usuario.sector,
                        "estado": usuario.estado,
                    }
                })
            else:
                errors = {field: error[0] for field, error in form.errors.items()}
                return JsonResponse({"success": False, "error": "Validación fallida", "errors": errors})
        except Usuario.DoesNotExist:
            return JsonResponse({"success": False, "error": "Usuario no encontrado"}, status=404)
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    
    return redirect("usuarios_lista")


@role_required(Usuario.ROL_ADMIN)
def usuario_delete_view(request, pk):
    if request.method == "POST":
        try:
            usuario = Usuario.objects.get(pk=pk)
            nombre = usuario.nombre
            usuario.delete()
            return JsonResponse({
                "success": True,
                "message": f"Usuario {nombre} eliminado correctamente."
            })
        except Usuario.DoesNotExist:
            return JsonResponse({"success": False, "error": "Usuario no encontrado"}, status=404)
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    
    return JsonResponse({"success": False, "error": "Método no permitido"}, status=405)


@role_required(Usuario.ROL_ADMIN)
def usuario_toggle_estado_view(request, pk):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Método no permitido"}, status=405)

    try:
        usuario = Usuario.objects.get(pk=pk)

        if usuario.id == request.session.get(AUTH_SESSION_KEY):
            return JsonResponse({"success": False, "error": "No puedes desactivar tu propia cuenta."}, status=400)

        usuario.estado = not usuario.estado
        usuario.save(update_fields=["estado"])

        estado_txt = "activado" if usuario.estado else "desactivado"
        return JsonResponse(
            {
                "success": True,
                "message": f"Usuario {usuario.nombre} {estado_txt} correctamente.",
                "estado": usuario.estado,
            }
        )
    except Usuario.DoesNotExist:
        return JsonResponse({"success": False, "error": "Usuario no encontrado"}, status=404)
