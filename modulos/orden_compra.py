from app import db
from sqlalchemy import text


def insertar_orden_compra(
    estado,
    fecha_creacion,
    fecha_modificacion,
    proveedor_id
):

    resultado = db.session.execute(
        text("""
            INSERT INTO ORDEN_COMPRA
            (
                estado,
                fecha_creacion,
                fecha_modificacion,
                proveedor_id
            )
            VALUES
            (
                :estado,
                :fecha_creacion,
                :fecha_modificacion,
                :proveedor_id
            )
            RETURNING id_ordenc
        """),
        {
            'estado': estado,
            'fecha_creacion': fecha_creacion,
            'fecha_modificacion': fecha_modificacion,
            'proveedor_id': proveedor_id
        }
    )

    id_ordenc = resultado.scalar()

    db.session.commit()

    return id_ordenc


def obtener_ordenes_compra():

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_ordenc,
                t.estado,
                t.fecha_creacion,
                t.fecha_modificacion,
                t.proveedor_id,
                pv.codigo AS proveedor_codigo,
                pv.empresa AS proveedor_empresa
            FROM ORDEN_COMPRA t
            INNER JOIN PROVEEDOR pv ON pv.id_proveedor = t.proveedor_id
        """)
    )

    ordenes_compra = resultado.fetchall()

    return ordenes_compra


def obtener_un_orden_compra(id_ordenc):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_ordenc,
                t.estado,
                t.fecha_creacion,
                t.fecha_modificacion,
                t.proveedor_id,
                pv.codigo AS proveedor_codigo,
                pv.empresa AS proveedor_empresa
            FROM ORDEN_COMPRA t
            INNER JOIN PROVEEDOR pv ON pv.id_proveedor = t.proveedor_id
            WHERE t.id_ordenc = :id_ordenc
        """),
        {
            'id_ordenc': id_ordenc
        }
    )

    orden_compra = resultado.fetchone()

    return orden_compra


def obtener_ordenes_compra_por_proveedor(proveedor_id):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_ordenc,
                t.estado,
                t.fecha_creacion,
                t.fecha_modificacion,
                t.proveedor_id,
                pv.codigo AS proveedor_codigo,
                pv.empresa AS proveedor_empresa
            FROM ORDEN_COMPRA t
            INNER JOIN PROVEEDOR pv ON pv.id_proveedor = t.proveedor_id
            WHERE t.proveedor_id = :proveedor_id
        """),
        {
            'proveedor_id': proveedor_id
        }
    )

    ordenes_compra = resultado.fetchall()

    return ordenes_compra


def obtener_ordenes_compra_por_estado(estado):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_ordenc,
                t.estado,
                t.fecha_creacion,
                t.fecha_modificacion,
                t.proveedor_id,
                pv.codigo AS proveedor_codigo,
                pv.empresa AS proveedor_empresa
            FROM ORDEN_COMPRA t
            INNER JOIN PROVEEDOR pv ON pv.id_proveedor = t.proveedor_id
            WHERE t.estado = :estado
        """),
        {
            'estado': estado
        }
    )

    ordenes_compra = resultado.fetchall()

    return ordenes_compra


def actualizar_orden_compra(
    id_ordenc,
    estado,
    fecha_modificacion,
    proveedor_id
):

    db.session.execute(
        text("""
            UPDATE ORDEN_COMPRA
            SET
                estado = :estado,
                fecha_modificacion = :fecha_modificacion,
                proveedor_id = :proveedor_id
            WHERE id_ordenc = :id_ordenc
        """),
        {
            'id_ordenc': id_ordenc,
            'estado': estado,
            'fecha_modificacion': fecha_modificacion,
            'proveedor_id': proveedor_id
        }
    )

    db.session.commit()


def actualizar_estado_orden_compra(id_ordenc, estado, fecha_modificacion):
    # Baja logica: no se borra, solo cambia el estado

    db.session.execute(
        text("""
            UPDATE ORDEN_COMPRA
            SET
                estado = :estado,
                fecha_modificacion = :fecha_modificacion
            WHERE id_ordenc = :id_ordenc
        """),
        {
            'id_ordenc': id_ordenc,
            'estado': estado,
            'fecha_modificacion': fecha_modificacion
        }
    )

    db.session.commit()


def obtener_total_orden_compra(ordenc_id):

    resultado = db.session.execute(
        text("""
            SELECT COALESCE(SUM(cantidad * costo_unitario), 0)
            FROM DETALLE_ORDEN_COMPRA
            WHERE ordenc_id = :ordenc_id
        """),
        {
            'ordenc_id': ordenc_id
        }
    )

    total = resultado.scalar()

    return total


def obtener_reporte_compras(fecha_inicio, fecha_fin):
    # Reporte de compras por periodo (fecha_fin exclusiva: pasar el dia siguiente)

    resultado = db.session.execute(
        text("""
            SELECT
                oc.id_ordenc,
                oc.estado,
                oc.fecha_creacion,
                pv.codigo AS proveedor_codigo,
                pv.empresa AS proveedor_empresa,
                COALESCE(SUM(d.cantidad * d.costo_unitario), 0) AS total
            FROM ORDEN_COMPRA oc
            INNER JOIN PROVEEDOR pv ON pv.id_proveedor = oc.proveedor_id
            LEFT JOIN DETALLE_ORDEN_COMPRA d ON d.ordenc_id = oc.id_ordenc
            WHERE oc.fecha_creacion >= :fecha_inicio
              AND oc.fecha_creacion < :fecha_fin
            GROUP BY oc.id_ordenc, oc.estado, oc.fecha_creacion, pv.codigo, pv.empresa
            ORDER BY oc.fecha_creacion
        """),
        {
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin
        }
    )

    reporte = resultado.fetchall()

    return reporte
