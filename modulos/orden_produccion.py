from app import db
from sqlalchemy import text


def insertar_orden_produccion(
    cantidad,
    estado,
    fecha_creacion,
    fecha_modificacion,
    producto_id,
    lote_id,
    bom_id
):

    resultado = db.session.execute(
        text("""
            INSERT INTO ORDEN_PRODUCCION
            (
                cantidad,
                estado,
                fecha_creacion,
                fecha_modificacion,
                producto_id,
                lote_id,
                bom_id
            )
            VALUES
            (
                :cantidad,
                :estado,
                :fecha_creacion,
                :fecha_modificacion,
                :producto_id,
                :lote_id,
                :bom_id
            )
            RETURNING id_ordenp
        """),
        {
            'cantidad': cantidad,
            'estado': estado,
            'fecha_creacion': fecha_creacion,
            'fecha_modificacion': fecha_modificacion,
            'producto_id': producto_id,
            'lote_id': lote_id,
            'bom_id': bom_id
        }
    )

    id_ordenp = resultado.scalar()

    db.session.commit()

    return id_ordenp


def obtener_ordenes_produccion():

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_ordenp,
                t.cantidad,
                t.estado,
                t.fecha_creacion,
                t.fecha_modificacion,
                t.producto_id,
                t.lote_id,
                t.bom_id,
                pr.codigo AS producto_codigo,
                pr.nombre AS producto_nombre,
                pr.unidad_medida AS producto_unidad_medida,
                lo.codigo AS lote_codigo,
                bo.codigo AS bom_codigo,
                bo.nombre AS bom_nombre
            FROM ORDEN_PRODUCCION t
            INNER JOIN PRODUCTO pr ON pr.id_producto = t.producto_id
            LEFT JOIN LOTE lo ON lo.id_lote = t.lote_id
            INNER JOIN BOM bo ON bo.id_bom = t.bom_id
        """)
    )

    ordenes_produccion = resultado.fetchall()

    return ordenes_produccion


def obtener_un_orden_produccion(id_ordenp):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_ordenp,
                t.cantidad,
                t.estado,
                t.fecha_creacion,
                t.fecha_modificacion,
                t.producto_id,
                t.lote_id,
                t.bom_id,
                pr.codigo AS producto_codigo,
                pr.nombre AS producto_nombre,
                pr.unidad_medida AS producto_unidad_medida,
                lo.codigo AS lote_codigo,
                bo.codigo AS bom_codigo,
                bo.nombre AS bom_nombre
            FROM ORDEN_PRODUCCION t
            INNER JOIN PRODUCTO pr ON pr.id_producto = t.producto_id
            LEFT JOIN LOTE lo ON lo.id_lote = t.lote_id
            INNER JOIN BOM bo ON bo.id_bom = t.bom_id
            WHERE t.id_ordenp = :id_ordenp
        """),
        {
            'id_ordenp': id_ordenp
        }
    )

    orden_produccion = resultado.fetchone()

    return orden_produccion


def obtener_ordenes_produccion_por_producto(producto_id):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_ordenp,
                t.cantidad,
                t.estado,
                t.fecha_creacion,
                t.fecha_modificacion,
                t.producto_id,
                t.lote_id,
                t.bom_id,
                pr.codigo AS producto_codigo,
                pr.nombre AS producto_nombre,
                pr.unidad_medida AS producto_unidad_medida,
                lo.codigo AS lote_codigo,
                bo.codigo AS bom_codigo,
                bo.nombre AS bom_nombre
            FROM ORDEN_PRODUCCION t
            INNER JOIN PRODUCTO pr ON pr.id_producto = t.producto_id
            LEFT JOIN LOTE lo ON lo.id_lote = t.lote_id
            INNER JOIN BOM bo ON bo.id_bom = t.bom_id
            WHERE t.producto_id = :producto_id
        """),
        {
            'producto_id': producto_id
        }
    )

    ordenes_produccion = resultado.fetchall()

    return ordenes_produccion


def obtener_ordenes_produccion_por_lote(lote_id):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_ordenp,
                t.cantidad,
                t.estado,
                t.fecha_creacion,
                t.fecha_modificacion,
                t.producto_id,
                t.lote_id,
                t.bom_id,
                pr.codigo AS producto_codigo,
                pr.nombre AS producto_nombre,
                pr.unidad_medida AS producto_unidad_medida,
                lo.codigo AS lote_codigo,
                bo.codigo AS bom_codigo,
                bo.nombre AS bom_nombre
            FROM ORDEN_PRODUCCION t
            INNER JOIN PRODUCTO pr ON pr.id_producto = t.producto_id
            LEFT JOIN LOTE lo ON lo.id_lote = t.lote_id
            INNER JOIN BOM bo ON bo.id_bom = t.bom_id
            WHERE t.lote_id = :lote_id
        """),
        {
            'lote_id': lote_id
        }
    )

    ordenes_produccion = resultado.fetchall()

    return ordenes_produccion


def obtener_ordenes_produccion_por_bom(bom_id):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_ordenp,
                t.cantidad,
                t.estado,
                t.fecha_creacion,
                t.fecha_modificacion,
                t.producto_id,
                t.lote_id,
                t.bom_id,
                pr.codigo AS producto_codigo,
                pr.nombre AS producto_nombre,
                pr.unidad_medida AS producto_unidad_medida,
                lo.codigo AS lote_codigo,
                bo.codigo AS bom_codigo,
                bo.nombre AS bom_nombre
            FROM ORDEN_PRODUCCION t
            INNER JOIN PRODUCTO pr ON pr.id_producto = t.producto_id
            LEFT JOIN LOTE lo ON lo.id_lote = t.lote_id
            INNER JOIN BOM bo ON bo.id_bom = t.bom_id
            WHERE t.bom_id = :bom_id
        """),
        {
            'bom_id': bom_id
        }
    )

    ordenes_produccion = resultado.fetchall()

    return ordenes_produccion


def obtener_ordenes_produccion_por_estado(estado):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_ordenp,
                t.cantidad,
                t.estado,
                t.fecha_creacion,
                t.fecha_modificacion,
                t.producto_id,
                t.lote_id,
                t.bom_id,
                pr.codigo AS producto_codigo,
                pr.nombre AS producto_nombre,
                pr.unidad_medida AS producto_unidad_medida,
                lo.codigo AS lote_codigo,
                bo.codigo AS bom_codigo,
                bo.nombre AS bom_nombre
            FROM ORDEN_PRODUCCION t
            INNER JOIN PRODUCTO pr ON pr.id_producto = t.producto_id
            LEFT JOIN LOTE lo ON lo.id_lote = t.lote_id
            INNER JOIN BOM bo ON bo.id_bom = t.bom_id
            WHERE t.estado = :estado
        """),
        {
            'estado': estado
        }
    )

    ordenes_produccion = resultado.fetchall()

    return ordenes_produccion


def actualizar_orden_produccion(
    id_ordenp,
    cantidad,
    estado,
    fecha_modificacion,
    producto_id,
    lote_id,
    bom_id
):

    db.session.execute(
        text("""
            UPDATE ORDEN_PRODUCCION
            SET
                cantidad = :cantidad,
                estado = :estado,
                fecha_modificacion = :fecha_modificacion,
                producto_id = :producto_id,
                lote_id = :lote_id,
                bom_id = :bom_id
            WHERE id_ordenp = :id_ordenp
        """),
        {
            'id_ordenp': id_ordenp,
            'cantidad': cantidad,
            'estado': estado,
            'fecha_modificacion': fecha_modificacion,
            'producto_id': producto_id,
            'lote_id': lote_id,
            'bom_id': bom_id
        }
    )

    db.session.commit()


def actualizar_estado_orden_produccion(id_ordenp, estado, fecha_modificacion):
    # Baja logica: no se borra, solo cambia el estado

    db.session.execute(
        text("""
            UPDATE ORDEN_PRODUCCION
            SET
                estado = :estado,
                fecha_modificacion = :fecha_modificacion
            WHERE id_ordenp = :id_ordenp
        """),
        {
            'id_ordenp': id_ordenp,
            'estado': estado,
            'fecha_modificacion': fecha_modificacion
        }
    )

    db.session.commit()


def obtener_reporte_ordenes_produccion(fecha_inicio, fecha_fin):
    # Reporte de manufactura: cantidad planeada vs aceptada/rechazada
    # (fecha_fin exclusiva: pasar el dia siguiente)

    resultado = db.session.execute(
        text("""
            SELECT
                op.id_ordenp,
                op.estado,
                op.cantidad,
                op.fecha_creacion,
                pr.codigo AS producto_codigo,
                pr.nombre AS producto_nombre,
                COALESCE(SUM(p.cantidad_aceptada), 0) AS cantidad_aceptada,
                COALESCE(SUM(p.cantidad_rechazada), 0) AS cantidad_rechazada
            FROM ORDEN_PRODUCCION op
            INNER JOIN PRODUCTO pr ON pr.id_producto = op.producto_id
            LEFT JOIN PRODUCCION p ON p.ordenp_id = op.id_ordenp
            WHERE op.fecha_creacion >= :fecha_inicio
              AND op.fecha_creacion < :fecha_fin
            GROUP BY op.id_ordenp, op.estado, op.cantidad, op.fecha_creacion,
                     pr.codigo, pr.nombre
            ORDER BY op.fecha_creacion
        """),
        {
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin
        }
    )

    reporte = resultado.fetchall()

    return reporte
