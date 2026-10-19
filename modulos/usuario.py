from app import db
from sqlalchemy import text


def insertar_usuario(
    id_usuario,
    persona_id,
    estado,
    fecha_creacion,
    fecha_modificacion
):

    resultado = db.session.execute(
        text("""
            INSERT INTO USUARIO
            (
                id_usuario,
                persona_id,
                estado,
                fecha_creacion,
                fecha_modificacion
            )
            VALUES
            (
                :id_usuario,
                :persona_id,
                :estado,
                :fecha_creacion,
                :fecha_modificacion
            )
            RETURNING id_usuario
        """),
        {
            'id_usuario': id_usuario,
            'persona_id': persona_id,
            'estado': estado,
            'fecha_creacion': fecha_creacion,
            'fecha_modificacion': fecha_modificacion
        }
    )

    id_usuario = resultado.scalar()

    db.session.commit()

    return id_usuario


def obtener_usuarios():

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_usuario,
                t.persona_id,
                t.estado,
                t.fecha_creacion,
                t.fecha_modificacion,
                pe.nombre_1 AS persona_nombre_1,
                pe.nombre_2 AS persona_nombre_2,
                pe.apellido_1 AS persona_apellido_1,
                pe.apellido_2 AS persona_apellido_2,
                pe.correo AS persona_correo,
                pe.telefono AS persona_telefono,
                pe.estado AS persona_estado
            FROM USUARIO t
            INNER JOIN PERSONA pe ON pe.id_persona = t.persona_id
        """)
    )

    usuarios = resultado.fetchall()

    return usuarios


def obtener_un_usuario(id_usuario):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_usuario,
                t.persona_id,
                t.estado,
                t.fecha_creacion,
                t.fecha_modificacion,
                pe.nombre_1 AS persona_nombre_1,
                pe.nombre_2 AS persona_nombre_2,
                pe.apellido_1 AS persona_apellido_1,
                pe.apellido_2 AS persona_apellido_2,
                pe.correo AS persona_correo,
                pe.telefono AS persona_telefono,
                pe.estado AS persona_estado
            FROM USUARIO t
            INNER JOIN PERSONA pe ON pe.id_persona = t.persona_id
            WHERE t.id_usuario = :id_usuario
        """),
        {
            'id_usuario': id_usuario
        }
    )

    usuario = resultado.fetchone()

    return usuario


def obtener_usuario_por_persona(persona_id):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_usuario,
                t.persona_id,
                t.estado,
                t.fecha_creacion,
                t.fecha_modificacion,
                pe.nombre_1 AS persona_nombre_1,
                pe.nombre_2 AS persona_nombre_2,
                pe.apellido_1 AS persona_apellido_1,
                pe.apellido_2 AS persona_apellido_2,
                pe.correo AS persona_correo,
                pe.telefono AS persona_telefono,
                pe.estado AS persona_estado
            FROM USUARIO t
            INNER JOIN PERSONA pe ON pe.id_persona = t.persona_id
            WHERE t.persona_id = :persona_id
        """),
        {
            'persona_id': persona_id
        }
    )

    usuario = resultado.fetchone()

    return usuario


def obtener_usuarios_por_estado(estado):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_usuario,
                t.persona_id,
                t.estado,
                t.fecha_creacion,
                t.fecha_modificacion,
                pe.nombre_1 AS persona_nombre_1,
                pe.nombre_2 AS persona_nombre_2,
                pe.apellido_1 AS persona_apellido_1,
                pe.apellido_2 AS persona_apellido_2,
                pe.correo AS persona_correo,
                pe.telefono AS persona_telefono,
                pe.estado AS persona_estado
            FROM USUARIO t
            INNER JOIN PERSONA pe ON pe.id_persona = t.persona_id
            WHERE t.estado = :estado
        """),
        {
            'estado': estado
        }
    )

    usuarios = resultado.fetchall()

    return usuarios


def actualizar_usuario(
    id_usuario,
    persona_id,
    estado,
    fecha_modificacion
):

    db.session.execute(
        text("""
            UPDATE USUARIO
            SET
                persona_id = :persona_id,
                estado = :estado,
                fecha_modificacion = :fecha_modificacion
            WHERE id_usuario = :id_usuario
        """),
        {
            'id_usuario': id_usuario,
            'persona_id': persona_id,
            'estado': estado,
            'fecha_modificacion': fecha_modificacion
        }
    )

    db.session.commit()


def actualizar_estado_usuario(id_usuario, estado, fecha_modificacion):
    # Baja logica: no se borra, solo cambia el estado

    db.session.execute(
        text("""
            UPDATE USUARIO
            SET
                estado = :estado,
                fecha_modificacion = :fecha_modificacion
            WHERE id_usuario = :id_usuario
        """),
        {
            'id_usuario': id_usuario,
            'estado': estado,
            'fecha_modificacion': fecha_modificacion
        }
    )

    db.session.commit()


def obtener_usuario_por_correo(correo):
    # Para saber que usuario del ERP es la persona que inicio sesion

    resultado = db.session.execute(
        text("""
            SELECT
                u.id_usuario,
                u.estado,
                p.id_persona,
                p.nombre_1,
                p.apellido_1,
                p.correo
            FROM USUARIO u
            INNER JOIN PERSONA p ON p.id_persona = u.persona_id
            WHERE p.correo = :correo
        """),
        {
            'correo': correo
        }
    )

    usuario = resultado.fetchone()

    return usuario


# ----- Administración del ERP vinculada con Supabase Auth -----
# Se mantienen las funciones anteriores para no romper importaciones existentes.
# La contraseña SIEMPRE pertenece a Supabase Auth: nunca se almacena aquí.


def listar_usuarios_erp():
    filas = db.session.execute(text("""
        SELECT u.id_usuario::text AS id_usuario,
               p.nombre_1, p.nombre_2, p.apellido_1, p.apellido_2,
               p.correo, p.telefono,
               u.estado, p.estado AS persona_estado,
               r.codigo AS rol_codigo, r.nombre AS rol_nombre,
               u.fecha_creacion
        FROM public.usuario u
        JOIN public.persona p ON p.id_persona = u.persona_id
        LEFT JOIN public.rol r ON r.id_rol = u.rol_id
        ORDER BY p.nombre_1, p.apellido_1, u.fecha_creacion
    """)).mappings().all()
    return [dict(f) for f in filas]


def obtener_usuario_erp(id_usuario):
    fila = db.session.execute(text("""
        SELECT u.id_usuario::text AS id_usuario,
               u.persona_id,
               p.nombre_1, p.nombre_2, p.apellido_1, p.apellido_2,
               p.correo, p.telefono,
               u.estado, p.estado AS persona_estado,
               r.codigo AS rol_codigo, r.nombre AS rol_nombre
        FROM public.usuario u
        JOIN public.persona p ON p.id_persona = u.persona_id
        LEFT JOIN public.rol r ON r.id_rol = u.rol_id
        WHERE u.id_usuario = CAST(:uid AS uuid)
    """), {"uid": str(id_usuario)}).mappings().first()
    return dict(fila) if fila else None


def listar_roles_erp():
    filas = db.session.execute(text("""
        SELECT id_rol, codigo, nombre
        FROM public.rol
        WHERE codigo IN ('administrador', 'operador')
        ORDER BY id_rol
    """)).mappings().all()
    return [dict(f) for f in filas]


def _rol_id(codigo):
    return db.session.execute(
        text("SELECT id_rol FROM public.rol WHERE codigo = :codigo"),
        {"codigo": codigo},
    ).scalar()


def vincular_usuario_auth_erp(datos):
    """Vincula una cuenta PREVIAMENTE creada en Auth con persona y usuario.

    Se valida el correo directamente en auth.users; por ello la conexión PostgreSQL
    debe tener permisos de SELECT en esa tabla (no basta la clave publishable).
    """
    correo = datos["correo"]
    auth = db.session.execute(text("""
        SELECT id::text AS id_usuario
        FROM auth.users
        WHERE lower(email) = :correo AND email_confirmed_at IS NOT NULL
        LIMIT 1
    """), {"correo": correo}).mappings().first()
    if auth is None:
        raise ValueError("No hay una cuenta confirmada en Supabase Auth para ese correo.")

    existente = db.session.execute(text("""
        SELECT 1 FROM public.usuario WHERE id_usuario = CAST(:uid AS uuid)
    """), {"uid": auth["id_usuario"]}).scalar()
    if existente:
        raise ValueError("Esta cuenta de Supabase Auth ya está vinculada al ERP.")

    persona_existente = db.session.execute(text("""
        SELECT 1 FROM public.persona WHERE lower(correo) = :correo LIMIT 1
    """), {"correo": correo}).scalar()
    if persona_existente:
        raise ValueError("Ya existe una persona con ese correo. Revisá la vinculación antes de continuar.")

    rol_id = _rol_id(datos["rol_codigo"])
    if rol_id is None:
        raise ValueError("El rol indicado no está configurado en Supabase.")

    try:
        persona_id = db.session.execute(text("""
            INSERT INTO public.persona
                (nombre_1, nombre_2, apellido_1, apellido_2, correo, telefono, estado)
            VALUES (:nombre_1, :nombre_2, :apellido_1, :apellido_2, :correo, :telefono, 'Activo')
            RETURNING id_persona
        """), {
            "nombre_1": datos["nombre_1"], "nombre_2": datos["nombre_2"],
            "apellido_1": datos["apellido_1"], "apellido_2": datos["apellido_2"],
            "correo": correo, "telefono": datos["telefono"],
        }).scalar_one()

        db.session.execute(text("""
            INSERT INTO public.usuario (id_usuario, persona_id, rol_id, estado)
            VALUES (CAST(:uid AS uuid), :persona_id, :rol_id, 'Activo')
        """), {"uid": auth["id_usuario"], "persona_id": persona_id, "rol_id": rol_id})
        db.session.commit()
        return auth["id_usuario"]
    except Exception:
        db.session.rollback()
        raise


def actualizar_datos_usuario_erp(id_usuario, datos):
    """Edita los datos de persona y el rol. El correo se cambia desde Auth primero,
    por lo que aquí se mantiene de solo lectura para no desincronizar identidades.
    """
    actual = obtener_usuario_erp(id_usuario)
    if not actual:
        return False
    rol_id = _rol_id(datos["rol_codigo"])
    if rol_id is None:
        raise ValueError("El rol solicitado no existe.")
    try:
        db.session.execute(text("""
            UPDATE public.persona SET
                nombre_1 = :nombre_1, nombre_2 = :nombre_2,
                apellido_1 = :apellido_1, apellido_2 = :apellido_2,
                telefono = :telefono, fecha_modificacion = CURRENT_TIMESTAMP
            WHERE id_persona = :persona_id
        """), {
            "persona_id": actual["persona_id"],
            "nombre_1": datos["nombre_1"], "nombre_2": datos["nombre_2"],
            "apellido_1": datos["apellido_1"], "apellido_2": datos["apellido_2"],
            "telefono": datos["telefono"],
        })
        db.session.execute(text("""
            UPDATE public.usuario SET rol_id = :rol_id,
                   fecha_modificacion = CURRENT_TIMESTAMP
            WHERE id_usuario = CAST(:uid AS uuid)
        """), {"rol_id": rol_id, "uid": str(id_usuario)})
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return True


def cambiar_estado_usuario_erp(id_usuario, estado):
    resultado = db.session.execute(text("""
        UPDATE public.usuario
        SET estado = :estado, fecha_modificacion = CURRENT_TIMESTAMP
        WHERE id_usuario = CAST(:uid AS uuid)
        RETURNING id_usuario
    """), {"uid": str(id_usuario), "estado": estado}).scalar()
    db.session.commit()
    return resultado is not None
