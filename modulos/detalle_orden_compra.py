from app import db
from sqlalchemy import text


def insertar_detalle_orden_compra(
    ordenc_id,
    producto_id,
    cantidad,
    costo_unitario
):

    resultado = db.session.execute(
        text("""
            INSERT INTO DETALLE_ORDEN_COMPRA
            (
                ordenc_id,
                producto_id,
                cantidad,
                costo_unitario
            )
            VALUES
            (
                :ordenc_id,
                :producto_id,
                :cantidad,
                :costo_unitario
            )
            RETURNING id_detalle_compra
        """),
        {
            'ordenc_id': ordenc_id,
            'producto_id': producto_id,
            'cantidad': cantidad,
            'costo_unitario': costo_unitario
        }
    )

    id_detalle_compra = resultado.scalar()

    db.session.commit()

    return id_detalle_compra


def obtener_detalles_orden_compra():

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_detalle_compra,
                t.ordenc_id,
                t.producto_id,
                t.cantidad,
                t.costo_unitario,
                pr.codigo AS producto_codigo,
                pr.nombre AS producto_nombre,
                pr.unidad_medida AS producto_unidad_medida
            FROM DETALLE_ORDEN_COMPRA t
            INNER JOIN PRODUCTO pr ON pr.id_producto = t.producto_id
        """)
    )

    detalles_orden_compra = resultado.fetchall()

    return detalles_orden_compra


def obtener_un_detalle_orden_compra(id_detalle_compra):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_detalle_compra,
                t.ordenc_id,
                t.producto_id,
                t.cantidad,
                t.costo_unitario,
                pr.codigo AS producto_codigo,
                pr.nombre AS producto_nombre,
                pr.unidad_medida AS producto_unidad_medida
            FROM DETALLE_ORDEN_COMPRA t
            INNER JOIN PRODUCTO pr ON pr.id_producto = t.producto_id
            WHERE t.id_detalle_compra = :id_detalle_compra
        """),
        {
            'id_detalle_compra': id_detalle_compra
        }
    )

    detalle_orden_compra = resultado.fetchone()

    return detalle_orden_compra


def obtener_detalles_orden_compra_por_ordenc(ordenc_id):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_detalle_compra,
                t.ordenc_id,
                t.producto_id,
                t.cantidad,
                t.costo_unitario,
                pr.codigo AS producto_codigo,
                pr.nombre AS producto_nombre,
                pr.unidad_medida AS producto_unidad_medida
            FROM DETALLE_ORDEN_COMPRA t
            INNER JOIN PRODUCTO pr ON pr.id_producto = t.producto_id
            WHERE t.ordenc_id = :ordenc_id
        """),
        {
            'ordenc_id': ordenc_id
        }
    )

    detalles_orden_compra = resultado.fetchall()

    return detalles_orden_compra


def obtener_detalles_orden_compra_por_producto(producto_id):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_detalle_compra,
                t.ordenc_id,
                t.producto_id,
                t.cantidad,
                t.costo_unitario,
                pr.codigo AS producto_codigo,
                pr.nombre AS producto_nombre,
                pr.unidad_medida AS producto_unidad_medida
            FROM DETALLE_ORDEN_COMPRA t
            INNER JOIN PRODUCTO pr ON pr.id_producto = t.producto_id
            WHERE t.producto_id = :producto_id
        """),
        {
            'producto_id': producto_id
        }
    )

    detalles_orden_compra = resultado.fetchall()

    return detalles_orden_compra


def actualizar_detalle_orden_compra(
    id_detalle_compra,
    ordenc_id,
    producto_id,
    cantidad,
    costo_unitario
):

    db.session.execute(
        text("""
            UPDATE DETALLE_ORDEN_COMPRA
            SET
                ordenc_id = :ordenc_id,
                producto_id = :producto_id,
                cantidad = :cantidad,
                costo_unitario = :costo_unitario
            WHERE id_detalle_compra = :id_detalle_compra
        """),
        {
            'id_detalle_compra': id_detalle_compra,
            'ordenc_id': ordenc_id,
            'producto_id': producto_id,
            'cantidad': cantidad,
            'costo_unitario': costo_unitario
        }
    )

    db.session.commit()


def eliminar_detalle_orden_compra(id_detalle_compra):
    # Las lineas de detalle si se pueden borrar (no tienen estado)

    db.session.execute(
        text("""
            DELETE FROM DETALLE_ORDEN_COMPRA
            WHERE id_detalle_compra = :id_detalle_compra
        """),
        {
            'id_detalle_compra': id_detalle_compra
        }
    )

    db.session.commit()
