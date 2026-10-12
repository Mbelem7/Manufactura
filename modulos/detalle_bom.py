from app import db
from sqlalchemy import text


def insertar_detalle_bom(bom_id, producto_component_id, cantidad):

    resultado = db.session.execute(
        text("""
            INSERT INTO DETALLE_BOM
            (
                bom_id,
                producto_component_id,
                cantidad
            )
            VALUES
            (
                :bom_id,
                :producto_component_id,
                :cantidad
            )
            RETURNING id_detalle_bom
        """),
        {
            'bom_id': bom_id,
            'producto_component_id': producto_component_id,
            'cantidad': cantidad
        }
    )

    id_detalle_bom = resultado.scalar()

    db.session.commit()

    return id_detalle_bom


def obtener_detalles_bom():

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_detalle_bom,
                t.bom_id,
                t.producto_component_id,
                t.cantidad,
                bo.codigo AS bom_codigo,
                bo.nombre AS bom_nombre,
                pr.codigo AS producto_codigo,
                pr.nombre AS producto_nombre,
                pr.unidad_medida AS producto_unidad_medida
            FROM DETALLE_BOM t
            INNER JOIN BOM bo ON bo.id_bom = t.bom_id
            INNER JOIN PRODUCTO pr ON pr.id_producto = t.producto_component_id
        """)
    )

    detalles_bom = resultado.fetchall()

    return detalles_bom


def obtener_un_detalle_bom(id_detalle_bom):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_detalle_bom,
                t.bom_id,
                t.producto_component_id,
                t.cantidad,
                bo.codigo AS bom_codigo,
                bo.nombre AS bom_nombre,
                pr.codigo AS producto_codigo,
                pr.nombre AS producto_nombre,
                pr.unidad_medida AS producto_unidad_medida
            FROM DETALLE_BOM t
            INNER JOIN BOM bo ON bo.id_bom = t.bom_id
            INNER JOIN PRODUCTO pr ON pr.id_producto = t.producto_component_id
            WHERE t.id_detalle_bom = :id_detalle_bom
        """),
        {
            'id_detalle_bom': id_detalle_bom
        }
    )

    detalle_bom = resultado.fetchone()

    return detalle_bom


def obtener_detalles_bom_por_bom(bom_id):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_detalle_bom,
                t.bom_id,
                t.producto_component_id,
                t.cantidad,
                bo.codigo AS bom_codigo,
                bo.nombre AS bom_nombre,
                pr.codigo AS producto_codigo,
                pr.nombre AS producto_nombre,
                pr.unidad_medida AS producto_unidad_medida
            FROM DETALLE_BOM t
            INNER JOIN BOM bo ON bo.id_bom = t.bom_id
            INNER JOIN PRODUCTO pr ON pr.id_producto = t.producto_component_id
            WHERE t.bom_id = :bom_id
        """),
        {
            'bom_id': bom_id
        }
    )

    detalles_bom = resultado.fetchall()

    return detalles_bom


def obtener_detalles_bom_por_producto_component(producto_component_id):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_detalle_bom,
                t.bom_id,
                t.producto_component_id,
                t.cantidad,
                bo.codigo AS bom_codigo,
                bo.nombre AS bom_nombre,
                pr.codigo AS producto_codigo,
                pr.nombre AS producto_nombre,
                pr.unidad_medida AS producto_unidad_medida
            FROM DETALLE_BOM t
            INNER JOIN BOM bo ON bo.id_bom = t.bom_id
            INNER JOIN PRODUCTO pr ON pr.id_producto = t.producto_component_id
            WHERE t.producto_component_id = :producto_component_id
        """),
        {
            'producto_component_id': producto_component_id
        }
    )

    detalles_bom = resultado.fetchall()

    return detalles_bom


def actualizar_detalle_bom(
    id_detalle_bom,
    bom_id,
    producto_component_id,
    cantidad
):

    db.session.execute(
        text("""
            UPDATE DETALLE_BOM
            SET
                bom_id = :bom_id,
                producto_component_id = :producto_component_id,
                cantidad = :cantidad
            WHERE id_detalle_bom = :id_detalle_bom
        """),
        {
            'id_detalle_bom': id_detalle_bom,
            'bom_id': bom_id,
            'producto_component_id': producto_component_id,
            'cantidad': cantidad
        }
    )

    db.session.commit()


def eliminar_detalle_bom(id_detalle_bom):
    # Las lineas de detalle si se pueden borrar (no tienen estado)

    db.session.execute(
        text("""
            DELETE FROM DETALLE_BOM
            WHERE id_detalle_bom = :id_detalle_bom
        """),
        {
            'id_detalle_bom': id_detalle_bom
        }
    )

    db.session.commit()
