from app import db
from sqlalchemy import text


def insertar_orden_venta(
    estado,
    fecha_creacion,
    fecha_modificacion,
    cliente_id
):

    resultado = db.session.execute(
        text("""
            INSERT INTO ORDEN_VENTA
            (
                estado,
                fecha_creacion,
                fecha_modificacion,
                cliente_id
            )
            VALUES
            (
                :estado,
                :fecha_creacion,
                :fecha_modificacion,
                :cliente_id
            )
            RETURNING id_ordenv
        """),
        {
            'estado': estado,
            'fecha_creacion': fecha_creacion,
            'fecha_modificacion': fecha_modificacion,
            'cliente_id': cliente_id
        }
    )

    id_ordenv = resultado.scalar()

    db.session.commit()

    return id_ordenv


def obtener_ordenes_venta():

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_ordenv,
                t.estado,
                t.fecha_creacion,
                t.fecha_modificacion,
                t.cliente_id,
                cl.codigo AS cliente_codigo,
                cl.empresa AS cliente_empresa
            FROM ORDEN_VENTA t
            INNER JOIN CLIENTE cl ON cl.id_cliente = t.cliente_id
        """)
    )

    ordenes_venta = resultado.fetchall()

    return ordenes_venta


def obtener_un_orden_venta(id_ordenv):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_ordenv,
                t.estado,
                t.fecha_creacion,
                t.fecha_modificacion,
                t.cliente_id,
                cl.codigo AS cliente_codigo,
                cl.empresa AS cliente_empresa
            FROM ORDEN_VENTA t
            INNER JOIN CLIENTE cl ON cl.id_cliente = t.cliente_id
            WHERE t.id_ordenv = :id_ordenv
        """),
        {
            'id_ordenv': id_ordenv
        }
    )

    orden_venta = resultado.fetchone()

    return orden_venta


def obtener_ordenes_venta_por_cliente(cliente_id):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_ordenv,
                t.estado,
                t.fecha_creacion,
                t.fecha_modificacion,
                t.cliente_id,
                cl.codigo AS cliente_codigo,
                cl.empresa AS cliente_empresa
            FROM ORDEN_VENTA t
            INNER JOIN CLIENTE cl ON cl.id_cliente = t.cliente_id
            WHERE t.cliente_id = :cliente_id
        """),
        {
            'cliente_id': cliente_id
        }
    )

    ordenes_venta = resultado.fetchall()

    return ordenes_venta


def obtener_ordenes_venta_por_estado(estado):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_ordenv,
                t.estado,
                t.fecha_creacion,
                t.fecha_modificacion,
                t.cliente_id,
                cl.codigo AS cliente_codigo,
                cl.empresa AS cliente_empresa
            FROM ORDEN_VENTA t
            INNER JOIN CLIENTE cl ON cl.id_cliente = t.cliente_id
            WHERE t.estado = :estado
        """),
        {
            'estado': estado
        }
    )

    ordenes_venta = resultado.fetchall()

    return ordenes_venta


def actualizar_orden_venta(
    id_ordenv,
    estado,
    fecha_modificacion,
    cliente_id
):

    db.session.execute(
        text("""
            UPDATE ORDEN_VENTA
            SET
                estado = :estado,
                fecha_modificacion = :fecha_modificacion,
                cliente_id = :cliente_id
            WHERE id_ordenv = :id_ordenv
        """),
        {
            'id_ordenv': id_ordenv,
            'estado': estado,
            'fecha_modificacion': fecha_modificacion,
            'cliente_id': cliente_id
        }
    )

    db.session.commit()


def actualizar_estado_orden_venta(id_ordenv, estado, fecha_modificacion):
    # Baja logica: no se borra, solo cambia el estado

    db.session.execute(
        text("""
            UPDATE ORDEN_VENTA
            SET
                estado = :estado,
                fecha_modificacion = :fecha_modificacion
            WHERE id_ordenv = :id_ordenv
        """),
        {
            'id_ordenv': id_ordenv,
            'estado': estado,
            'fecha_modificacion': fecha_modificacion
        }
    )

    db.session.commit()


def obtener_total_orden_venta(ordenv_id):

    resultado = db.session.execute(
        text("""
            SELECT COALESCE(SUM(cantidad * precio_unitario), 0)
            FROM DETALLE_ORDEN_VENTA
            WHERE ordenv_id = :ordenv_id
        """),
        {
            'ordenv_id': ordenv_id
        }
    )

    total = resultado.scalar()

    return total


def obtener_reporte_ventas(fecha_inicio, fecha_fin):
    # Reporte de ventas por periodo (fecha_fin exclusiva: pasar el dia siguiente)

    resultado = db.session.execute(
        text("""
            SELECT
                ov.id_ordenv,
                ov.estado,
                ov.fecha_creacion,
                cl.codigo AS cliente_codigo,
                cl.empresa AS cliente_empresa,
                COALESCE(SUM(d.cantidad * d.precio_unitario), 0) AS total
            FROM ORDEN_VENTA ov
            INNER JOIN CLIENTE cl ON cl.id_cliente = ov.cliente_id
            LEFT JOIN DETALLE_ORDEN_VENTA d ON d.ordenv_id = ov.id_ordenv
            WHERE ov.fecha_creacion >= :fecha_inicio
              AND ov.fecha_creacion < :fecha_fin
            GROUP BY ov.id_ordenv, ov.estado, ov.fecha_creacion, cl.codigo, cl.empresa
            ORDER BY ov.fecha_creacion
        """),
        {
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin
        }
    )

    reporte = resultado.fetchall()

    return reporte
