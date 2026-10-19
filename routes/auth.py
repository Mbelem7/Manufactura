import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from uuid import UUID

from flask import Blueprint, jsonify, request, session
from modulos.seguridad import obtener_usuario_actual

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def _autenticar_en_supabase(correo, contrasena):
    url = (os.getenv("SUPABASE_URL") or "").strip().rstrip("/")
    api_key = (os.getenv("SUPABASE_PUBLISHABLE_KEY") or "").strip()

    datos_url = urlsplit(url)
    if datos_url.scheme != "https" or not datos_url.netloc or not api_key:
        raise RuntimeError("Faltan SUPABASE_URL o SUPABASE_PUBLISHABLE_KEY válidas en .env")

    payload = json.dumps({"email": correo, "password": contrasena}).encode("utf-8")
    peticion = Request(
        url + "/auth/v1/token?grant_type=password",
        data=payload,
        headers={"apikey": api_key, "Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(peticion, timeout=12) as respuesta:
        datos = json.load(respuesta)

    
    id_auth = (datos.get("user") or {}).get("id")
    return str(UUID(str(id_auth)))


@auth_bp.post("/login")
def login():
    if not request.is_json:
        return jsonify(error="Enviá JSON con email y password."), 415
    cuerpo = request.get_json(silent=True) or {}
    correo = str(cuerpo.get("email") or "").strip()
    clave = cuerpo.get("password")
    if not correo or not isinstance(clave, str) or not clave:
        return jsonify(error="Ingresá correo y contraseña."), 400
    if len(correo) > 255 or len(clave) > 1024:
        return jsonify(error="Datos de acceso inválidos."), 400

    try:
        uuid_auth = _autenticar_en_supabase(correo, clave)
    except HTTPError as exc:
        if exc.code in (400, 401, 403, 422):
            return jsonify(error="Correo o contraseña incorrectos, o cuenta no habilitada."), 401
        return jsonify(error="No fue posible verificar las credenciales."), 502
    except (URLError, TimeoutError):
        return jsonify(error="No se pudo contactar con Supabase Auth."), 502
    except RuntimeError:
        return jsonify(error="Falta configurar Supabase Auth en el servidor."), 503
    except (ValueError, KeyError, TypeError):
        return jsonify(error="Respuesta de autenticación inesperada."), 502

    
    session.clear()
    session["id_usuario"] = uuid_auth
    usuario = obtener_usuario_actual()
    if usuario is None:
        session.clear()
        return jsonify(error="Cuenta autenticada, pero sin usuario activo y rol en Manufactura."), 403
    session.permanent = True
    return jsonify(
        mensaje="Sesión iniciada.",
        id_usuario=str(usuario["id_usuario"]),
        nombre=usuario["nombre_1"],
        rol=usuario["rol_codigo"],
    ), 200


@auth_bp.post("/logout")
def logout():
    if not request.is_json:
        return jsonify(error="Esta operación requiere una petición JSON POST."), 415
    session.clear()
    return jsonify(mensaje="Sesión cerrada."), 200


@auth_bp.get("/me")
def me():
    if not session.get("id_usuario"):
        return jsonify(error="No hay sesión iniciada."), 401
    usuario = obtener_usuario_actual()
    if usuario is None:
        session.clear()
        return jsonify(error="Cuenta no habilitada o sin rol."), 403
    return jsonify(
        id_usuario=str(usuario["id_usuario"]),
        nombre=usuario["nombre_1"],
        apellido=usuario["apellido_1"],
        correo=usuario["correo"],
        rol=usuario["rol_codigo"],
    ), 200
