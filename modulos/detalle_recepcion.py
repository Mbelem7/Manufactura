from app import db
from sqlalchemy import text


def insertar_detalle_recepcion(
    recepcion_id,
    producto_id,
    lote_id,
    cantidad
):

    resultado = db.session.execute(
        text("""
            INSERT INTO DETALLE_RECEPCION
            (
                recepcion_id,
                producto_id,
                lote_id,
                cantidad
            )
            VALUES
            (
                :recepcion_id,
                :producto_id,
                :lote_id,
                :cantidad
            )
            RETURNING id_detalle_recepcion
        """),
        {
            'recepcion_id': recepcion_id,
            'producto_id': producto_id,
            'lote_id': lote_id,
            'cantidad': cantidad
        }
    )

    id_detalle_recepcion = resultado.scalar()

    db.session.commit()

    return id_detalle_recepcion


def obtener_detalles_recepcion():

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_detalle_recepcion,
                t.recepcion_id,
                t.producto_id,
                t.lote_id,
                t.cantidad,
                pr.codigo AS producto_codigo,
                pr.nombre AS producto_nombre,
                pr.unidad_medida AS producto_unidad_medida,
                lo.codigo AS lote_codigo
            FROM DETALLE_RECEPCION t
            INNER JOIN PRODUCTO pr ON pr.id_producto = t.producto_id
            LEFT JOIN LOTE lo ON lo.id_lote = t.lote_id
        """)
    )

    detalles_recepcion = resultado.fetchall()

    return detalles_recepcion


def obtener_un_detalle_recepcion(id_detalle_recepcion):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_detalle_recepcion,
                t.recepcion_id,
                t.producto_id,
                t.lote_id,
                t.cantidad,
                pr.codigo AS producto_codigo,
                pr.nombre AS producto_nombre,
                pr.unidad_medida AS producto_unidad_medida,
                lo.codigo AS lote_codigo
            FROM DETALLE_RECEPCION t
            INNER JOIN PRODUCTO pr ON pr.id_producto = t.producto_id
            LEFT JOIN LOTE lo ON lo.id_lote = t.lote_id
            WHERE t.id_detalle_recepcion = :id_detalle_recepcion
        """),
        {
            'id_detalle_recepcion': id_detalle_recepcion
        }
    )

    detalle_recepcion = resultado.fetchone()

    return detalle_recepcion


def obtener_detalles_recepcion_por_recepcion(recepcion_id):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_detalle_recepcion,
                t.recepcion_id,
                t.producto_id,
                t.lote_id,
                t.cantidad,
                pr.codigo AS producto_codigo,
                pr.nombre AS producto_nombre,
                pr.unidad_medida AS producto_unidad_medida,
                lo.codigo AS lote_codigo
            FROM DETALLE_RECEPCION t
            INNER JOIN PRODUCTO pr ON pr.id_producto = t.producto_id
            LEFT JOIN LOTE lo ON lo.id_lote = t.lote_id
            WHERE t.recepcion_id = :recepcion_id
        """),
        {
            'recepcion_id': recepcion_id
        }
    )

    detalles_recepcion = resultado.fetchall()

    return detalles_recepcion


def obtener_detalles_recepcion_por_producto(producto_id):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_detalle_recepcion,
                t.recepcion_id,
                t.producto_id,
                t.lote_id,
                t.cantidad,
                pr.codigo AS producto_codigo,
                pr.nombre AS producto_nombre,
                pr.unidad_medida AS producto_unidad_medida,
                lo.codigo AS lote_codigo
            FROM DETALLE_RECEPCION t
            INNER JOIN PRODUCTO pr ON pr.id_producto = t.producto_id
            LEFT JOIN LOTE lo ON lo.id_lote = t.lote_id
            WHERE t.producto_id = :producto_id
        """),
        {
            'producto_id': producto_id
        }
    )

    detalles_recepcion = resultado.fetchall()

    return detalles_recepcion


def obtener_detalles_recepcion_por_lote(lote_id):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_detalle_recepcion,
                t.recepcion_id,
                t.producto_id,
                t.lote_id,
                t.cantidad,
                pr.codigo AS producto_codigo,
                pr.nombre AS producto_nombre,
                pr.unidad_medida AS producto_unidad_medida,
                lo.codigo AS lote_codigo
            FROM DETALLE_RECEPCION t
            INNER JOIN PRODUCTO pr ON pr.id_producto = t.producto_id
            LEFT JOIN LOTE lo ON lo.id_lote = t.lote_id
            WHERE t.lote_id = :lote_id
        """),
        {
            'lote_id': lote_id
        }
    )

    detalles_recepcion = resultado.fetchall()

    return detalles_recepcion


def actualizar_detalle_recepcion(
    id_detalle_recepcion,
    recepcion_id,
    producto_id,
    lote_id,
    cantidad
):

    db.session.execute(
        text("""
            UPDATE DETALLE_RECEPCION
            SET
                recepcion_id = :recepcion_id,
                producto_id = :producto_id,
                lote_id = :lote_id,
                cantidad = :cantidad
            WHERE id_detalle_recepcion = :id_detalle_recepcion
        """),
        {
            'id_detalle_recepcion': id_detalle_recepcion,
            'recepcion_id': recepcion_id,
            'producto_id': producto_id,
            'lote_id': lote_id,
            'cantidad': cantidad
        }
    )

    db.session.commit()


def eliminar_detalle_recepcion(id_detalle_recepcion):
    # Las lineas de detalle si se pueden borrar (no tienen estado)

    db.session.execute(
        text("""
            DELETE FROM DETALLE_RECEPCION
            WHERE id_detalle_recepcion = :id_detalle_recepcion
        """),
        {
            'id_detalle_recepcion': id_detalle_recepcion
        }
    )

    db.session.commit()
