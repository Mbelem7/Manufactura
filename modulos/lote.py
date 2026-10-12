from app import db
from sqlalchemy import text


def insertar_lote(
    codigo,
    fecha_creacion,
    fecha_modificacion,
    producto_id
):

    resultado = db.session.execute(
        text("""
            INSERT INTO LOTE
            (
                codigo,
                fecha_creacion,
                fecha_modificacion,
                producto_id
            )
            VALUES
            (
                :codigo,
                :fecha_creacion,
                :fecha_modificacion,
                :producto_id
            )
            RETURNING id_lote
        """),
        {
            'codigo': codigo,
            'fecha_creacion': fecha_creacion,
            'fecha_modificacion': fecha_modificacion,
            'producto_id': producto_id
        }
    )

    id_lote = resultado.scalar()

    db.session.commit()

    return id_lote


def obtener_lotes():

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_lote,
                t.codigo,
                t.fecha_creacion,
                t.fecha_modificacion,
                t.producto_id,
                pr.codigo AS producto_codigo,
                pr.nombre AS producto_nombre,
                pr.unidad_medida AS producto_unidad_medida
            FROM LOTE t
            INNER JOIN PRODUCTO pr ON pr.id_producto = t.producto_id
        """)
    )

    lotes = resultado.fetchall()

    return lotes


def obtener_un_lote(id_lote):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_lote,
                t.codigo,
                t.fecha_creacion,
                t.fecha_modificacion,
                t.producto_id,
                pr.codigo AS producto_codigo,
                pr.nombre AS producto_nombre,
                pr.unidad_medida AS producto_unidad_medida
            FROM LOTE t
            INNER JOIN PRODUCTO pr ON pr.id_producto = t.producto_id
            WHERE t.id_lote = :id_lote
        """),
        {
            'id_lote': id_lote
        }
    )

    lote = resultado.fetchone()

    return lote


def obtener_lotes_por_producto(producto_id):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_lote,
                t.codigo,
                t.fecha_creacion,
                t.fecha_modificacion,
                t.producto_id,
                pr.codigo AS producto_codigo,
                pr.nombre AS producto_nombre,
                pr.unidad_medida AS producto_unidad_medida
            FROM LOTE t
            INNER JOIN PRODUCTO pr ON pr.id_producto = t.producto_id
            WHERE t.producto_id = :producto_id
        """),
        {
            'producto_id': producto_id
        }
    )

    lotes = resultado.fetchall()

    return lotes


def obtener_lote_por_codigo(codigo):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_lote,
                t.codigo,
                t.fecha_creacion,
                t.fecha_modificacion,
                t.producto_id,
                pr.codigo AS producto_codigo,
                pr.nombre AS producto_nombre,
                pr.unidad_medida AS producto_unidad_medida
            FROM LOTE t
            INNER JOIN PRODUCTO pr ON pr.id_producto = t.producto_id
            WHERE t.codigo = :codigo
        """),
        {
            'codigo': codigo
        }
    )

    lote = resultado.fetchone()

    return lote


def actualizar_lote(
    id_lote,
    codigo,
    fecha_modificacion,
    producto_id
):

    db.session.execute(
        text("""
            UPDATE LOTE
            SET
                codigo = :codigo,
                fecha_modificacion = :fecha_modificacion,
                producto_id = :producto_id
            WHERE id_lote = :id_lote
        """),
        {
            'id_lote': id_lote,
            'codigo': codigo,
            'fecha_modificacion': fecha_modificacion,
            'producto_id': producto_id
        }
    )

    db.session.commit()


def obtener_lotes_con_existencia():

    resultado = db.session.execute(
        text("""
            SELECT
                lo.id_lote,
                lo.codigo,
                pr.id_producto,
                pr.nombre AS producto_nombre,
                pr.unidad_medida,
                COALESCE(SUM(i.cantidad), 0) AS existencia
            FROM LOTE lo
            INNER JOIN PRODUCTO pr ON pr.id_producto = lo.producto_id
            LEFT JOIN INVENTARIO i ON i.lote_id = lo.id_lote
            GROUP BY lo.id_lote, lo.codigo, pr.id_producto, pr.nombre, pr.unidad_medida
            ORDER BY lo.codigo
        """)
    )

    lotes = resultado.fetchall()

    return lotes
