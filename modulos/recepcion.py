from app import db
from sqlalchemy import text


def insertar_recepcion(
    codigo,
    fecha_creacion,
    fecha_modificacion,
    ordenc_id,
    almacen_id
):

    resultado = db.session.execute(
        text("""
            INSERT INTO RECEPCION
            (
                codigo,
                fecha_creacion,
                fecha_modificacion,
                ordenc_id,
                almacen_id
            )
            VALUES
            (
                :codigo,
                :fecha_creacion,
                :fecha_modificacion,
                :ordenc_id,
                :almacen_id
            )
            RETURNING id_recepcion
        """),
        {
            'codigo': codigo,
            'fecha_creacion': fecha_creacion,
            'fecha_modificacion': fecha_modificacion,
            'ordenc_id': ordenc_id,
            'almacen_id': almacen_id
        }
    )

    id_recepcion = resultado.scalar()

    db.session.commit()

    return id_recepcion


def obtener_recepciones():

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_recepcion,
                t.codigo,
                t.fecha_creacion,
                t.fecha_modificacion,
                t.ordenc_id,
                t.almacen_id,
                al.codigo AS almacen_codigo,
                al.nombre AS almacen_nombre
            FROM RECEPCION t
            INNER JOIN ALMACEN al ON al.id_almacen = t.almacen_id
        """)
    )

    recepciones = resultado.fetchall()

    return recepciones


def obtener_un_recepcion(id_recepcion):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_recepcion,
                t.codigo,
                t.fecha_creacion,
                t.fecha_modificacion,
                t.ordenc_id,
                t.almacen_id,
                al.codigo AS almacen_codigo,
                al.nombre AS almacen_nombre
            FROM RECEPCION t
            INNER JOIN ALMACEN al ON al.id_almacen = t.almacen_id
            WHERE t.id_recepcion = :id_recepcion
        """),
        {
            'id_recepcion': id_recepcion
        }
    )

    recepcion = resultado.fetchone()

    return recepcion


def obtener_recepciones_por_ordenc(ordenc_id):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_recepcion,
                t.codigo,
                t.fecha_creacion,
                t.fecha_modificacion,
                t.ordenc_id,
                t.almacen_id,
                al.codigo AS almacen_codigo,
                al.nombre AS almacen_nombre
            FROM RECEPCION t
            INNER JOIN ALMACEN al ON al.id_almacen = t.almacen_id
            WHERE t.ordenc_id = :ordenc_id
        """),
        {
            'ordenc_id': ordenc_id
        }
    )

    recepciones = resultado.fetchall()

    return recepciones


def obtener_recepciones_por_almacen(almacen_id):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_recepcion,
                t.codigo,
                t.fecha_creacion,
                t.fecha_modificacion,
                t.ordenc_id,
                t.almacen_id,
                al.codigo AS almacen_codigo,
                al.nombre AS almacen_nombre
            FROM RECEPCION t
            INNER JOIN ALMACEN al ON al.id_almacen = t.almacen_id
            WHERE t.almacen_id = :almacen_id
        """),
        {
            'almacen_id': almacen_id
        }
    )

    recepciones = resultado.fetchall()

    return recepciones


def obtener_recepcion_por_codigo(codigo):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_recepcion,
                t.codigo,
                t.fecha_creacion,
                t.fecha_modificacion,
                t.ordenc_id,
                t.almacen_id,
                al.codigo AS almacen_codigo,
                al.nombre AS almacen_nombre
            FROM RECEPCION t
            INNER JOIN ALMACEN al ON al.id_almacen = t.almacen_id
            WHERE t.codigo = :codigo
        """),
        {
            'codigo': codigo
        }
    )

    recepcion = resultado.fetchone()

    return recepcion



def actualizar_recepcion(
    id_recepcion,
    codigo,
    fecha_modificacion,
    ordenc_id,
    almacen_id
):

    db.session.execute(
        text("""
            UPDATE RECEPCION
            SET
                codigo = :codigo,
                fecha_modificacion = :fecha_modificacion,
                ordenc_id = :ordenc_id,
                almacen_id = :almacen_id
            WHERE id_recepcion = :id_recepcion
        """),
        {
            'id_recepcion': id_recepcion,
            'codigo': codigo,
            'fecha_modificacion': fecha_modificacion,
            'ordenc_id': ordenc_id,
            'almacen_id': almacen_id
        }
    )

    db.session.commit()

