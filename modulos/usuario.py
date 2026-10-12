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
