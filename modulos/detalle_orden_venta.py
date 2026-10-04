from app import db
from sqlalchemy import text


def insertar_detalle_orden_venta(
    ordenv_id,
    producto_id,
    cantidad,
    precio_unitario
):

    resultado = db.session.execute(
        text("""
            INSERT INTO DETALLE_ORDEN_VENTA
            (
                ordenv_id,
                producto_id,
                cantidad,
                precio_unitario
            )
            VALUES
            (
                :ordenv_id,
                :producto_id,
                :cantidad,
                :precio_unitario
            )
            RETURNING id_detalle_venta
        """),
        {
            'ordenv_id': ordenv_id,
            'producto_id': producto_id,
            'cantidad': cantidad,
            'precio_unitario': precio_unitario
        }
    )

    id_detalle_venta = resultado.scalar()

    db.session.commit()

    return id_detalle_venta


def obtener_detalles_orden_venta():

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_detalle_venta,
                t.ordenv_id,
                t.producto_id,
                t.cantidad,
                t.precio_unitario,
                pr.codigo AS producto_codigo,
                pr.nombre AS producto_nombre,
                pr.unidad_medida AS producto_unidad_medida
            FROM DETALLE_ORDEN_VENTA t
            INNER JOIN PRODUCTO pr ON pr.id_producto = t.producto_id
        """)
    )

    detalles_orden_venta = resultado.fetchall()

    return detalles_orden_venta


def obtener_un_detalle_orden_venta(id_detalle_venta):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_detalle_venta,
                t.ordenv_id,
                t.producto_id,
                t.cantidad,
                t.precio_unitario,
                pr.codigo AS producto_codigo,
                pr.nombre AS producto_nombre,
                pr.unidad_medida AS producto_unidad_medida
            FROM DETALLE_ORDEN_VENTA t
            INNER JOIN PRODUCTO pr ON pr.id_producto = t.producto_id
            WHERE t.id_detalle_venta = :id_detalle_venta
        """),
        {
            'id_detalle_venta': id_detalle_venta
        }
    )

    detalle_orden_venta = resultado.fetchone()

    return detalle_orden_venta


def obtener_detalles_orden_venta_por_ordenv(ordenv_id):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_detalle_venta,
                t.ordenv_id,
                t.producto_id,
                t.cantidad,
                t.precio_unitario,
                pr.codigo AS producto_codigo,
                pr.nombre AS producto_nombre,
                pr.unidad_medida AS producto_unidad_medida
            FROM DETALLE_ORDEN_VENTA t
            INNER JOIN PRODUCTO pr ON pr.id_producto = t.producto_id
            WHERE t.ordenv_id = :ordenv_id
        """),
        {
            'ordenv_id': ordenv_id
        }
    )

    detalles_orden_venta = resultado.fetchall()

    return detalles_orden_venta


def obtener_detalles_orden_venta_por_producto(producto_id):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_detalle_venta,
                t.ordenv_id,
                t.producto_id,
                t.cantidad,
                t.precio_unitario,
                pr.codigo AS producto_codigo,
                pr.nombre AS producto_nombre,
                pr.unidad_medida AS producto_unidad_medida
            FROM DETALLE_ORDEN_VENTA t
            INNER JOIN PRODUCTO pr ON pr.id_producto = t.producto_id
            WHERE t.producto_id = :producto_id
        """),
        {
            'producto_id': producto_id
        }
    )

    detalles_orden_venta = resultado.fetchall()

    return detalles_orden_venta


def actualizar_detalle_orden_venta(
    id_detalle_venta,
    ordenv_id,
    producto_id,
    cantidad,
    precio_unitario
):

    db.session.execute(
        text("""
            UPDATE DETALLE_ORDEN_VENTA
            SET
                ordenv_id = :ordenv_id,
                producto_id = :producto_id,
                cantidad = :cantidad,
                precio_unitario = :precio_unitario
            WHERE id_detalle_venta = :id_detalle_venta
        """),
        {
            'id_detalle_venta': id_detalle_venta,
            'ordenv_id': ordenv_id,
            'producto_id': producto_id,
            'cantidad': cantidad,
            'precio_unitario': precio_unitario
        }
    )

    db.session.commit()


def eliminar_detalle_orden_venta(id_detalle_venta):
    # Las lineas de detalle si se pueden borrar (no tienen estado)

    db.session.execute(
        text("""
            DELETE FROM DETALLE_ORDEN_VENTA
            WHERE id_detalle_venta = :id_detalle_venta
        """),
        {
            'id_detalle_venta': id_detalle_venta
        }
    )

    db.session.commit()
