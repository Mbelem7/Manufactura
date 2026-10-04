from app import db
from sqlalchemy import text
from decimal import Decimal


def insertar_inventario(
    cantidad,
    fecha_creacion,
    fecha_modificacion,
    almacen_id,
    producto_id,
    lote_id
):

    resultado = db.session.execute(
        text("""
            INSERT INTO INVENTARIO
            (
                cantidad,
                fecha_creacion,
                fecha_modificacion,
                almacen_id,
                producto_id,
                lote_id
            )
            VALUES
            (
                :cantidad,
                :fecha_creacion,
                :fecha_modificacion,
                :almacen_id,
                :producto_id,
                :lote_id
            )
            RETURNING id_inventario
        """),
        {
            'cantidad': cantidad,
            'fecha_creacion': fecha_creacion,
            'fecha_modificacion': fecha_modificacion,
            'almacen_id': almacen_id,
            'producto_id': producto_id,
            'lote_id': lote_id
        }
    )

    id_inventario = resultado.scalar()

    db.session.commit()

    return id_inventario


def obtener_inventario():

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_inventario,
                t.cantidad,
                t.fecha_creacion,
                t.fecha_modificacion,
                t.almacen_id,
                t.producto_id,
                t.lote_id,
                al.codigo AS almacen_codigo,
                al.nombre AS almacen_nombre,
                pr.codigo AS producto_codigo,
                pr.nombre AS producto_nombre,
                pr.unidad_medida AS producto_unidad_medida,
                lo.codigo AS lote_codigo
            FROM INVENTARIO t
            INNER JOIN ALMACEN al ON al.id_almacen = t.almacen_id
            INNER JOIN PRODUCTO pr ON pr.id_producto = t.producto_id
            LEFT JOIN LOTE lo ON lo.id_lote = t.lote_id
        """)
    )

    inventario = resultado.fetchall()

    return inventario


def obtener_un_inventario(id_inventario):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_inventario,
                t.cantidad,
                t.fecha_creacion,
                t.fecha_modificacion,
                t.almacen_id,
                t.producto_id,
                t.lote_id,
                al.codigo AS almacen_codigo,
                al.nombre AS almacen_nombre,
                pr.codigo AS producto_codigo,
                pr.nombre AS producto_nombre,
                pr.unidad_medida AS producto_unidad_medida,
                lo.codigo AS lote_codigo
            FROM INVENTARIO t
            INNER JOIN ALMACEN al ON al.id_almacen = t.almacen_id
            INNER JOIN PRODUCTO pr ON pr.id_producto = t.producto_id
            LEFT JOIN LOTE lo ON lo.id_lote = t.lote_id
            WHERE t.id_inventario = :id_inventario
        """),
        {
            'id_inventario': id_inventario
        }
    )

    inventario = resultado.fetchone()

    return inventario


def obtener_inventario_por_almacen(almacen_id):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_inventario,
                t.cantidad,
                t.fecha_creacion,
                t.fecha_modificacion,
                t.almacen_id,
                t.producto_id,
                t.lote_id,
                al.codigo AS almacen_codigo,
                al.nombre AS almacen_nombre,
                pr.codigo AS producto_codigo,
                pr.nombre AS producto_nombre,
                pr.unidad_medida AS producto_unidad_medida,
                lo.codigo AS lote_codigo
            FROM INVENTARIO t
            INNER JOIN ALMACEN al ON al.id_almacen = t.almacen_id
            INNER JOIN PRODUCTO pr ON pr.id_producto = t.producto_id
            LEFT JOIN LOTE lo ON lo.id_lote = t.lote_id
            WHERE t.almacen_id = :almacen_id
        """),
        {
            'almacen_id': almacen_id
        }
    )

    inventario = resultado.fetchall()

    return inventario


def obtener_inventario_por_producto(producto_id):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_inventario,
                t.cantidad,
                t.fecha_creacion,
                t.fecha_modificacion,
                t.almacen_id,
                t.producto_id,
                t.lote_id,
                al.codigo AS almacen_codigo,
                al.nombre AS almacen_nombre,
                pr.codigo AS producto_codigo,
                pr.nombre AS producto_nombre,
                pr.unidad_medida AS producto_unidad_medida,
                lo.codigo AS lote_codigo
            FROM INVENTARIO t
            INNER JOIN ALMACEN al ON al.id_almacen = t.almacen_id
            INNER JOIN PRODUCTO pr ON pr.id_producto = t.producto_id
            LEFT JOIN LOTE lo ON lo.id_lote = t.lote_id
            WHERE t.producto_id = :producto_id
        """),
        {
            'producto_id': producto_id
        }
    )

    inventario = resultado.fetchall()

    return inventario


def obtener_inventario_por_lote(lote_id):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_inventario,
                t.cantidad,
                t.fecha_creacion,
                t.fecha_modificacion,
                t.almacen_id,
                t.producto_id,
                t.lote_id,
                al.codigo AS almacen_codigo,
                al.nombre AS almacen_nombre,
                pr.codigo AS producto_codigo,
                pr.nombre AS producto_nombre,
                pr.unidad_medida AS producto_unidad_medida,
                lo.codigo AS lote_codigo
            FROM INVENTARIO t
            INNER JOIN ALMACEN al ON al.id_almacen = t.almacen_id
            INNER JOIN PRODUCTO pr ON pr.id_producto = t.producto_id
            LEFT JOIN LOTE lo ON lo.id_lote = t.lote_id
            WHERE t.lote_id = :lote_id
        """),
        {
            'lote_id': lote_id
        }
    )

    inventario = resultado.fetchall()

    return inventario


def actualizar_inventario(
    id_inventario,
    cantidad,
    fecha_modificacion,
    almacen_id,
    producto_id,
    lote_id
):

    db.session.execute(
        text("""
            UPDATE INVENTARIO
            SET
                cantidad = :cantidad,
                fecha_modificacion = :fecha_modificacion,
                almacen_id = :almacen_id,
                producto_id = :producto_id,
                lote_id = :lote_id
            WHERE id_inventario = :id_inventario
        """),
        {
            'id_inventario': id_inventario,
            'cantidad': cantidad,
            'fecha_modificacion': fecha_modificacion,
            'almacen_id': almacen_id,
            'producto_id': producto_id,
            'lote_id': lote_id
        }
    )

    db.session.commit()


def obtener_existencias_por_producto_almacen():
    # Existencias por producto y almacen

    resultado = db.session.execute(
        text("""
            SELECT
                pr.id_producto,
                pr.codigo AS producto_codigo,
                pr.nombre AS producto_nombre,
                pr.unidad_medida,
                al.id_almacen,
                al.codigo AS almacen_codigo,
                al.nombre AS almacen_nombre,
                SUM(i.cantidad) AS existencia
            FROM INVENTARIO i
            INNER JOIN PRODUCTO pr ON pr.id_producto = i.producto_id
            INNER JOIN ALMACEN al ON al.id_almacen = i.almacen_id
            GROUP BY pr.id_producto, pr.codigo, pr.nombre, pr.unidad_medida,
                     al.id_almacen, al.codigo, al.nombre
            ORDER BY pr.nombre, al.nombre
        """)
    )

    existencias = resultado.fetchall()

    return existencias


def obtener_stock_actual():
    # Stock total por producto (suma de todos los almacenes y lotes)

    resultado = db.session.execute(
        text("""
            SELECT
                pr.id_producto,
                pr.codigo,
                pr.nombre,
                pr.tipo_producto,
                pr.unidad_medida,
                COALESCE(SUM(i.cantidad), 0) AS stock_actual
            FROM PRODUCTO pr
            LEFT JOIN INVENTARIO i ON i.producto_id = pr.id_producto
            GROUP BY pr.id_producto, pr.codigo, pr.nombre, pr.tipo_producto, pr.unidad_medida
            ORDER BY pr.nombre
        """)
    )

    stock = resultado.fetchall()

    return stock


def obtener_stock_de_producto(producto_id):

    resultado = db.session.execute(
        text("""
            SELECT COALESCE(SUM(cantidad), 0)
            FROM INVENTARIO
            WHERE producto_id = :producto_id
        """),
        {
            'producto_id': producto_id
        }
    )

    stock = resultado.scalar()

    return stock


def aumentar_inventario(almacen_id, producto_id, lote_id, cantidad, fecha, commit=True):
    # Suma existencia; si no hay fila para ese almacen/producto/lote, la crea
    # commit=False sirve para agrupar varias operaciones en una sola transaccion

    resultado = db.session.execute(
        text("""
            UPDATE INVENTARIO
            SET
                cantidad = cantidad + :cantidad,
                fecha_modificacion = :fecha
            WHERE almacen_id = :almacen_id
              AND producto_id = :producto_id
              AND lote_id IS NOT DISTINCT FROM :lote_id
        """),
        {
            'cantidad': cantidad,
            'fecha': fecha,
            'almacen_id': almacen_id,
            'producto_id': producto_id,
            'lote_id': lote_id
        }
    )

    if resultado.rowcount == 0:
        db.session.execute(
            text("""
                INSERT INTO INVENTARIO
                (
                    cantidad,
                    fecha_creacion,
                    fecha_modificacion,
                    almacen_id,
                    producto_id,
                    lote_id
                )
                VALUES
                (
                    :cantidad,
                    :fecha,
                    :fecha,
                    :almacen_id,
                    :producto_id,
                    :lote_id
                )
            """),
            {
                'cantidad': cantidad,
                'fecha': fecha,
                'almacen_id': almacen_id,
                'producto_id': producto_id,
                'lote_id': lote_id
            }
        )

    if commit:
        db.session.commit()


def disminuir_inventario(almacen_id, producto_id, lote_id, cantidad, fecha, commit=True):
    # Resta existencia de un lote especifico; falla si no alcanza

    resultado = db.session.execute(
        text("""
            UPDATE INVENTARIO
            SET
                cantidad = cantidad - :cantidad,
                fecha_modificacion = :fecha
            WHERE almacen_id = :almacen_id
              AND producto_id = :producto_id
              AND lote_id IS NOT DISTINCT FROM :lote_id
              AND cantidad >= :cantidad
        """),
        {
            'cantidad': cantidad,
            'fecha': fecha,
            'almacen_id': almacen_id,
            'producto_id': producto_id,
            'lote_id': lote_id
        }
    )

    if resultado.rowcount == 0:
        db.session.rollback()
        raise ValueError('Existencia insuficiente en el inventario')

    if commit:
        db.session.commit()


def descontar_inventario_fifo(almacen_id, producto_id, cantidad, fecha, commit=True):
    # Resta de las existencias mas antiguas primero (para consumir materia prima)

    filas = db.session.execute(
        text("""
            SELECT id_inventario, cantidad
            FROM INVENTARIO
            WHERE almacen_id = :almacen_id
              AND producto_id = :producto_id
              AND cantidad > 0
            ORDER BY fecha_creacion, id_inventario
            FOR UPDATE
        """),
        {
            'almacen_id': almacen_id,
            'producto_id': producto_id
        }
    ).fetchall()

    pendiente = Decimal(str(cantidad))

    for fila in filas:
        if pendiente <= 0:
            break

        a_descontar = min(fila.cantidad, pendiente)

        db.session.execute(
            text("""
                UPDATE INVENTARIO
                SET
                    cantidad = cantidad - :a_descontar,
                    fecha_modificacion = :fecha
                WHERE id_inventario = :id_inventario
            """),
            {
                'a_descontar': a_descontar,
                'fecha': fecha,
                'id_inventario': fila.id_inventario
            }
        )

        pendiente -= a_descontar

    if pendiente > 0:
        db.session.rollback()
        raise ValueError('Existencia insuficiente para el producto ' + str(producto_id))

    if commit:
        db.session.commit()
