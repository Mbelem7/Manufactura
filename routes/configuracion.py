"""Administración de usuarios del ERP: registro, edición y baja lógica.

Solo el Administrador accede a estas APIs. El nuevo rol asignable es Operador.
Las contraseñas quedan exclusivamente en Supabase Auth.
"""

import json
import logging
import os
import re
import secrets
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from uuid import UUID
from hmac import compare_digest

from flask import Blueprint, jsonify, render_template, request, session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from modulos import usuario as usuarios_db
from modulos.seguridad import requiere_roles

configuracion_bp = Blueprint("configuracion", __name__, url_prefix="/configuracion")
ROLES = frozenset({"administrador", "operador"})
ROL_REGISTRABLE = "operador"
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
        raise ValueError("Rol no válido.")
    if nuevo and rol != "operador":
        raise ValueError("Por ahora solamente se pueden registrar Operadores.")
    if not nuevo and "rol_codigo" in datos and rol != (actual or {}).get("rol_codigo"):
        raise ValueError("El rol de un usuario existente no se puede cambiar desde este formulario.")
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
    # El Administrador existe; no se asigna a nuevos usuarios desde el ERP.
    return jsonify(roles=[rol for rol in usuarios_db.listar_roles_erp()
                          if rol["codigo"] == ROL_REGISTRABLE])


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


def _supabase_admin_request(metodo, ruta, datos=None):
    """Llamada exclusiva del servidor; nunca expone ni devuelve la clave secreta."""
    url = (os.getenv("SUPABASE_URL") or "").strip().rstrip("/")
    llave = (os.getenv("SUPABASE_SECRET_KEY") or
             os.getenv("SUPABASE_SERVICE_ROLE_KEY") or "").strip()
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.netloc or not llave:
        raise RuntimeError("Falta SUPABASE_SECRET_KEY en el servidor.")

    headers = {"apikey": llave, "Content-Type": "application/json"}
    if not llave.startswith("sb_secret_"):
        # Compatibilidad con la llave antigua JWT service_role.
        headers["Authorization"] = "Bearer " + llave
    carga = json.dumps(datos).encode("utf-8") if datos is not None else None
    peticion = Request(url + "/auth/v1/admin/users" + ruta,
                       data=carga, headers=headers, method=metodo)
    with urlopen(peticion, timeout=15) as respuesta:
        contenido = respuesta.read()
        return json.loads(contenido) if contenido else {}


def _clave_registro(datos):
    clave = datos.get("password")
    if not isinstance(clave, str) or len(clave) < 10 or len(clave) > 128:
        raise ValueError("La contraseña debe tener entre 10 y 128 caracteres.")
    if not any(c.isalpha() for c in clave) or not any(c.isdigit() for c in clave):
        raise ValueError("La contraseña debe incluir letras y números.")
    return clave


@configuracion_bp.post("/api/usuarios")
@requiere_roles("administrador")
def vincular_usuario_api():
    """Registra una cuenta nueva en Auth y la vincula con PERSONA / USUARIO."""
    if not _requiere_csrf():
        return jsonify(error="Token CSRF inválido o ausente."), 403
    datos = _cuerpo_json()
    if datos is None:
        return jsonify(error="Enviá los datos como objeto JSON."), 400
    try:
        clave = _clave_registro(datos)
        campos = {k: v for k, v in datos.items() if k != "password"}
        limpio = _limpiar_datos(campos, nuevo=True)
        if usuarios_db.correo_usuario_erp_existe(limpio["correo"]):
            return jsonify(error="Ya existe una persona o usuario con ese correo."), 409
    except ValueError as exc:
        return jsonify(error=str(exc)), 400
    except SQLAlchemyError:
        from app import db
        db.session.rollback()
        return jsonify(error="No fue posible comprobar el correo en PostgreSQL."), 500

    try:
        creado = _supabase_admin_request("POST", "", {
            "email": limpio["correo"], "password": clave,
            # Para demostración con correos controlados por el equipo.
            # En producción, usar invitación o confirmación de email.
            "email_confirm": True,
        })
        uid = str(UUID(str((creado.get("user") or creado).get("id"))))
    except RuntimeError:
        return jsonify(error="Configurá SUPABASE_SECRET_KEY solo en el servidor para registrar cuentas."), 503
    except HTTPError as exc:
        if exc.code in (400, 409, 422):
            return jsonify(error="Supabase rechazó el registro: correo existente o contraseña inválida."), 409
        logging.exception("Supabase Auth rechazó alta de usuario (%s)", exc.code)
        return jsonify(error="Supabase Auth no pudo crear la cuenta."), 502
    except (URLError, TimeoutError):
        return jsonify(error="No se pudo conectar con Supabase Auth."), 502
    except (ValueError, TypeError, KeyError):
        return jsonify(error="Supabase Auth devolvió una respuesta inesperada."), 502

    try:
        usuarios_db.registrar_nuevo_usuario_erp(uid, limpio)
    except (IntegrityError, SQLAlchemyError, ValueError):
        from app import db
        db.session.rollback()
        # Compensación: no dejar identidad en Auth sin registro en nuestro ERP.
        try:
            _supabase_admin_request("DELETE", "/" + uid)
        except (HTTPError, URLError, TimeoutError, RuntimeError) as exc:
            logging.error("ATENCIÓN: usuario %s quedó creado en Auth, pero no vinculado en ERP: %s", uid, type(exc).__name__)
            return jsonify(error="Se creó en Auth pero falló la vinculación; revisá la cuenta en Supabase antes de reintentar."), 503
        return jsonify(error="No se pudo guardar la cuenta en PostgreSQL. No se registró el usuario."), 409
    return jsonify(mensaje="Usuario registrado correctamente.", id_usuario=uid), 201


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
