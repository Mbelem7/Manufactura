from app import db
from sqlalchemy import text


def insertar_persona(
    nombre_1,
    nombre_2,
    apellido_1,
    apellido_2,
    correo,
    telefono,
    estado,
    fecha_creacion,
    fecha_modificacion
):

    resultado = db.session.execute(
        text("""
            INSERT INTO PERSONA
            (
                nombre_1,
                nombre_2,
                apellido_1,
                apellido_2,
                correo,
                telefono,
                estado,
                fecha_creacion,
                fecha_modificacion
            )
            VALUES
            (
                :nombre_1,
                :nombre_2,
                :apellido_1,
                :apellido_2,
                :correo,
                :telefono,
                :estado,
                :fecha_creacion,
                :fecha_modificacion
            )
            RETURNING id_persona
        """),
        {
            'nombre_1': nombre_1,
            'nombre_2': nombre_2,
            'apellido_1': apellido_1,
            'apellido_2': apellido_2,
            'correo': correo,
            'telefono': telefono,
            'estado': estado,
            'fecha_creacion': fecha_creacion,
            'fecha_modificacion': fecha_modificacion
        }
    )

    id_persona = resultado.scalar()

    db.session.commit()

    return id_persona


def obtener_personas():

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_persona,
                t.nombre_1,
                t.nombre_2,
                t.apellido_1,
                t.apellido_2,
                t.correo,
                t.telefono,
                t.estado,
                t.fecha_creacion,
                t.fecha_modificacion
            FROM PERSONA t
        """)
    )

    personas = resultado.fetchall()

    return personas


def obtener_un_persona(id_persona):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_persona,
                t.nombre_1,
                t.nombre_2,
                t.apellido_1,
                t.apellido_2,
                t.correo,
                t.telefono,
                t.estado,
                t.fecha_creacion,
                t.fecha_modificacion
            FROM PERSONA t
            WHERE t.id_persona = :id_persona
        """),
        {
            'id_persona': id_persona
        }
    )

    persona = resultado.fetchone()

    return persona


def obtener_personas_por_estado(estado):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_persona,
                t.nombre_1,
                t.nombre_2,
                t.apellido_1,
                t.apellido_2,
                t.correo,
                t.telefono,
                t.estado,
                t.fecha_creacion,
                t.fecha_modificacion
            FROM PERSONA t
            WHERE t.estado = :estado
        """),
        {
            'estado': estado
        }
    )

    personas = resultado.fetchall()

    return personas


def actualizar_persona(
    id_persona,
    nombre_1,
    nombre_2,
    apellido_1,
    apellido_2,
    correo,
    telefono,
    estado,
    fecha_modificacion
):

    db.session.execute(
        text("""
            UPDATE PERSONA
            SET
                nombre_1 = :nombre_1,
                nombre_2 = :nombre_2,
                apellido_1 = :apellido_1,
                apellido_2 = :apellido_2,
                correo = :correo,
                telefono = :telefono,
                estado = :estado,
                fecha_modificacion = :fecha_modificacion
            WHERE id_persona = :id_persona
        """),
        {
            'id_persona': id_persona,
            'nombre_1': nombre_1,
            'nombre_2': nombre_2,
            'apellido_1': apellido_1,
            'apellido_2': apellido_2,
            'correo': correo,
            'telefono': telefono,
            'estado': estado,
            'fecha_modificacion': fecha_modificacion
        }
    )

    db.session.commit()


def actualizar_estado_persona(id_persona, estado, fecha_modificacion):
    # Baja logica: no se borra, solo cambia el estado

    db.session.execute(
        text("""
            UPDATE PERSONA
            SET
                estado = :estado,
                fecha_modificacion = :fecha_modificacion
            WHERE id_persona = :id_persona
        """),
        {
            'id_persona': id_persona,
            'estado': estado,
            'fecha_modificacion': fecha_modificacion
        }
    )

    db.session.commit()


def obtener_persona_por_correo(correo):

    resultado = db.session.execute(
        text("""
            SELECT
                id_persona,
                nombre_1,
                nombre_2,
                apellido_1,
                apellido_2,
                correo,
                telefono,
                estado
            FROM PERSONA
            WHERE correo = :correo
        """),
        {
            'correo': correo
        }
    )

    persona = resultado.fetchone()

    return persona
