from app import db
from sqlalchemy import text


def insertar_centro_trabajo(
    codigo,
    nombre,
    maquina,
    estado,
    fecha_creacion,
    fecha_modificacion
):

    resultado = db.session.execute(
        text("""
            INSERT INTO CENTRO_TRABAJO
            (
                codigo,
                nombre,
                maquina,
                estado,
                fecha_creacion,
                fecha_modificacion
            )
            VALUES
            (
                :codigo,
                :nombre,
                :maquina,
                :estado,
                :fecha_creacion,
                :fecha_modificacion
            )
            RETURNING id_centro
        """),
        {
            'codigo': codigo,
            'nombre': nombre,
            'maquina': maquina,
            'estado': estado,
            'fecha_creacion': fecha_creacion,
            'fecha_modificacion': fecha_modificacion
        }
    )

    id_centro = resultado.scalar()

    db.session.commit()

    return id_centro


def obtener_centros_trabajo():

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_centro,
                t.codigo,
                t.nombre,
                t.maquina,
                t.estado,
                t.fecha_creacion,
                t.fecha_modificacion
            FROM CENTRO_TRABAJO t
        """)
    )

    centros_trabajo = resultado.fetchall()

    return centros_trabajo


def obtener_un_centro_trabajo(id_centro):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_centro,
                t.codigo,
                t.nombre,
                t.maquina,
                t.estado,
                t.fecha_creacion,
                t.fecha_modificacion
            FROM CENTRO_TRABAJO t
            WHERE t.id_centro = :id_centro
        """),
        {
            'id_centro': id_centro
        }
    )

    centro_trabajo = resultado.fetchone()

    return centro_trabajo


def obtener_centro_trabajo_por_codigo(codigo):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_centro,
                t.codigo,
                t.nombre,
                t.maquina,
                t.estado,
                t.fecha_creacion,
                t.fecha_modificacion
            FROM CENTRO_TRABAJO t
            WHERE t.codigo = :codigo
        """),
        {
            'codigo': codigo
        }
    )

    centro_trabajo = resultado.fetchone()

    return centro_trabajo


def obtener_centros_trabajo_por_estado(estado):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_centro,
                t.codigo,
                t.nombre,
                t.maquina,
                t.estado,
                t.fecha_creacion,
                t.fecha_modificacion
            FROM CENTRO_TRABAJO t
            WHERE t.estado = :estado
        """),
        {
            'estado': estado
        }
    )

    centros_trabajo = resultado.fetchall()

    return centros_trabajo


def actualizar_centro_trabajo(
    id_centro,
    codigo,
    nombre,
    maquina,
    estado,
    fecha_modificacion
):

    db.session.execute(
        text("""
            UPDATE CENTRO_TRABAJO
            SET
                codigo = :codigo,
                nombre = :nombre,
                maquina = :maquina,
                estado = :estado,
                fecha_modificacion = :fecha_modificacion
            WHERE id_centro = :id_centro
        """),
        {
            'id_centro': id_centro,
            'codigo': codigo,
            'nombre': nombre,
            'maquina': maquina,
            'estado': estado,
            'fecha_modificacion': fecha_modificacion
        }
    )

    db.session.commit()


def actualizar_estado_centro_trabajo(id_centro, estado, fecha_modificacion):
    # Baja logica: no se borra, solo cambia el estado

    db.session.execute(
        text("""
            UPDATE CENTRO_TRABAJO
            SET
                estado = :estado,
                fecha_modificacion = :fecha_modificacion
            WHERE id_centro = :id_centro
        """),
        {
            'id_centro': id_centro,
            'estado': estado,
            'fecha_modificacion': fecha_modificacion
        }
    )

    db.session.commit()
