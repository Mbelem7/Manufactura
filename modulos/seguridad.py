from functools import wraps
from uuid import UUID

from flask import jsonify, session
from sqlalchemy import text

from app import db


def obtener_usuario_actual():
    """Obtiene el usuario y su rol desde PostgreSQL en cada petición."""
    uid = session.get("id_usuario")
    if not uid:
        return None
    try:
        uid = str(UUID(str(uid)))
    except (ValueError, TypeError, AttributeError):
        return None

    registro = db.session.execute(
        text("""
            SELECT
                u.id_usuario,
                u.estado AS usuario_estado,
                p.estado AS persona_estado,
                p.nombre_1,
                p.apellido_1,
                p.correo,
                r.codigo AS rol_codigo,
                r.nombre AS rol_nombre
            FROM public.usuario AS u
            INNER JOIN public.persona AS p ON p.id_persona = u.persona_id
            LEFT JOIN public.rol AS r ON r.id_rol = u.rol_id
            WHERE u.id_usuario = CAST(:uid AS uuid)
        """), {"uid": uid}
    ).mappings().first()

    if not registro:
        return None
    if str(registro["usuario_estado"] or "").lower() != "activo":
        return None
    if str(registro["persona_estado"] or "").lower() != "activo":
        return None
    if not registro["rol_codigo"]:
        return None
    return dict(registro)


def requiere_roles(*roles_permitidos):
    """Usar como @requiere_roles('administrador', ...), tras @bp.route."""
    def decorar(funcion):
        @wraps(funcion)
        def verificar(*args, **kwargs):
            if not session.get("id_usuario"):
                return jsonify(error="Iniciá sesión para continuar."), 401
            usuario = obtener_usuario_actual()
            if usuario is None:
                session.clear()
                return jsonify(error="Cuenta no habilitada o sin rol asignado."), 403
            if usuario["rol_codigo"] not in roles_permitidos:
                return jsonify(error="No tenés permiso para esta operación."), 403
            return funcion(*args, **kwargs)
        return verificar
    return decorar
