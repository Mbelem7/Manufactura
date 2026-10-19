"""Administración backend de cuentas del ERP.

Las pantallas HTML actuales se mantienen sin cambios. Las API JSON son para el
frontend y las pruebas. Crear la cuenta en Supabase Auth es, por ahora, un paso
manual autorizado en Authentication > Users; aquí se vincula esa cuenta.
"""

import re
import secrets
from hmac import compare_digest

from flask import Blueprint, jsonify, render_template, request, session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from modulos import usuario as usuarios_db
from modulos.seguridad import requiere_roles

configuracion_bp = Blueprint("configuracion", __name__, url_prefix="/configuracion")
ROLES = frozenset({"administrador", "operador"})
NOMBRES_MAX = 100


def _cuerpo_json():
    if not request.is_json:
        return None
    datos = request.get_json(silent=True)
    return datos if isinstance(datos, dict) else None


def _requiere_csrf():
    esperado = session.get("_csrf_admin")
    recibido = request.headers.get("X-CSRF-Token", "")
    return bool(esperado and recibido and compare_digest(esperado, recibido))


def _limpiar_datos(datos, *, nuevo=False, actual=None):
    """Valida campos permitidos: no acepta contraseñas ni cambio de correo."""
    permitidos = {"nombre_1", "nombre_2", "apellido_1", "apellido_2", "telefono", "rol_codigo"}
    if nuevo:
        permitidos.add("correo")
    if set(datos) - permitidos:
        raise ValueError("Hay campos no permitidos. El correo no puede editarse desde el ERP.")

    limpio = {}
    for campo in ("nombre_1", "nombre_2", "apellido_1", "apellido_2", "telefono"):
        valor = datos.get(campo, (actual or {}).get(campo, ""))
        if valor is not None and not isinstance(valor, str):
            raise ValueError("Los datos personales deben ser texto.")
        valor = (valor or "").strip()
        limite = 20 if campo == "telefono" else NOMBRES_MAX
        if len(valor) > limite:
            raise ValueError(f"{campo} supera el largo permitido.")
        limpio[campo] = valor or None

    if not limpio["nombre_1"] or not limpio["apellido_1"]:
        raise ValueError("El primer nombre y el primer apellido son obligatorios.")
    rol = datos.get("rol_codigo", (actual or {}).get("rol_codigo"))
    if rol not in ROLES:
        raise ValueError("El rol debe ser administrador u operador.")
    limpio["rol_codigo"] = rol

    if nuevo:
        correo = datos.get("correo")
        if not isinstance(correo, str):
            raise ValueError("Ingresá el correo de la cuenta existente en Supabase Auth.")
        correo = correo.strip().lower()
        if len(correo) > 255 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", correo):
            raise ValueError("El correo no tiene un formato válido.")
        limpio["correo"] = correo
    return limpio


# Pantallas existentes (su contenido HTML sigue siendo responsabilidad del frontend).
@configuracion_bp.get("/usuarios")
@requiere_roles("administrador")
def usuarios():
    return render_template("configuracion/usuarios/index.html")


@configuracion_bp.get("/usuarios/nuevo")
@requiere_roles("administrador")
def usuario_nuevo():
    return render_template("configuracion/usuarios/form.html")


@configuracion_bp.get("/api/csrf")
@requiere_roles("administrador")
def csrf_api():
    if not session.get("_csrf_admin"):
        session["_csrf_admin"] = secrets.token_urlsafe(32)
    return jsonify(csrf_token=session["_csrf_admin"])


@configuracion_bp.get("/api/roles")
@requiere_roles("administrador")
def roles_api():
    return jsonify(roles=usuarios_db.listar_roles_erp())


@configuracion_bp.get("/api/usuarios")
@requiere_roles("administrador")
def usuarios_api():
    filas = usuarios_db.listar_usuarios_erp()
    for fila in filas:
        if fila.get("fecha_creacion") is not None:
            fila["fecha_creacion"] = fila["fecha_creacion"].isoformat()
    return jsonify(usuarios=filas)


@configuracion_bp.get("/api/usuarios/<uuid:usuario_id>")
@requiere_roles("administrador")
def usuario_detalle_api(usuario_id):
    actual = usuarios_db.obtener_usuario_erp(usuario_id)
    if not actual:
        return jsonify(error="Usuario no encontrado."), 404
    return jsonify(usuario=actual)


@configuracion_bp.post("/api/usuarios")
@requiere_roles("administrador")
def vincular_usuario_api():
    if not _requiere_csrf():
        return jsonify(error="Token CSRF inválido o ausente."), 403
    datos = _cuerpo_json()
    if datos is None:
        return jsonify(error="Enviá los datos como objeto JSON."), 400
    try:
        limpio = _limpiar_datos(datos, nuevo=True)
        uid = usuarios_db.vincular_usuario_auth_erp(limpio)
    except ValueError as exc:
        return jsonify(error=str(exc)), 400
    except IntegrityError:
        from app import db
        db.session.rollback()
        return jsonify(error="Ya existe un registro relacionado con esta cuenta."), 409
    except SQLAlchemyError:
        from app import db
        db.session.rollback()
        return jsonify(error="No se pudo vincular la cuenta. Revisá los permisos de consulta a Auth."), 503
    return jsonify(mensaje="Cuenta de Auth vinculada al ERP.", id_usuario=uid), 201


@configuracion_bp.post("/api/usuarios/<uuid:usuario_id>/actualizar")
@requiere_roles("administrador")
def actualizar_usuario_api(usuario_id):
    if not _requiere_csrf():
        return jsonify(error="Token CSRF inválido o ausente."), 403
    datos = _cuerpo_json()
    if datos is None:
        return jsonify(error="Enviá los datos como objeto JSON."), 400
    actual = usuarios_db.obtener_usuario_erp(usuario_id)
    if not actual:
        return jsonify(error="Usuario no encontrado."), 404
    try:
        limpio = _limpiar_datos(datos, actual=actual)
        if str(usuario_id) == str(session.get("id_usuario")) and limpio["rol_codigo"] != "administrador":
            return jsonify(error="No podés quitarte tu propio rol administrador."), 403
        usuarios_db.actualizar_datos_usuario_erp(usuario_id, limpio)
    except ValueError as exc:
        return jsonify(error=str(exc)), 400
    except IntegrityError:
        from app import db
        db.session.rollback()
        return jsonify(error="Los datos entran en conflicto con un registro existente."), 409
    except SQLAlchemyError:
        from app import db
        db.session.rollback()
        return jsonify(error="No fue posible actualizar el usuario."), 500
    return jsonify(mensaje="Usuario actualizado."), 200


@configuracion_bp.post("/api/usuarios/<uuid:usuario_id>/estado")
@requiere_roles("administrador")
def cambiar_estado_usuario_api(usuario_id):
    if not _requiere_csrf():
        return jsonify(error="Token CSRF inválido o ausente."), 403
    datos = _cuerpo_json()
    if datos is None or set(datos) != {"estado"}:
        return jsonify(error="Indicá solamente el estado: Activo o Inactivo."), 400
    estado = datos.get("estado")
    if not isinstance(estado, str) or estado.lower() not in ("activo", "inactivo"):
        return jsonify(error="Estado inválido."), 400
    estado = "Activo" if estado.lower() == "activo" else "Inactivo"
    if str(usuario_id) == str(session.get("id_usuario")) and estado == "Inactivo":
        return jsonify(error="No podés desactivar tu propia cuenta."), 403
    try:
        cambiado = usuarios_db.cambiar_estado_usuario_erp(usuario_id, estado)
    except SQLAlchemyError:
        from app import db
        db.session.rollback()
        return jsonify(error="No se pudo cambiar el estado."), 500
    if not cambiado:
        return jsonify(error="Usuario no encontrado."), 404
    return jsonify(mensaje="Estado actualizado.", estado=estado), 200
