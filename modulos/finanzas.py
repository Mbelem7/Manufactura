from app import db
from sqlalchemy import text


def obtener_estado_resultados(fecha_inicio, fecha_fin, estado_excluido='cancelada'):
    # Estado de resultados por periodo (fecha_fin exclusiva: pasar el dia siguiente)
    #   ingresos       = ventas del periodo (ordenes que no estan canceladas)
    #   costo_ventas   = cantidad vendida x costo del producto
    #   compras        = ordenes de compra del periodo (informativo)
    #   utilidad_bruta = ingresos - costo_ventas

    p = {
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'estado_excluido': estado_excluido
    }

    ingresos = db.session.execute(
        text("""
            SELECT COALESCE(SUM(d.cantidad * d.precio_unitario), 0)
            FROM ORDEN_VENTA ov
            INNER JOIN DETALLE_ORDEN_VENTA d ON d.ordenv_id = ov.id_ordenv
            WHERE ov.estado <> :estado_excluido
              AND ov.fecha_creacion >= :fecha_inicio
              AND ov.fecha_creacion < :fecha_fin
        """), p
    ).scalar()

    costo_ventas = db.session.execute(
        text("""
            SELECT COALESCE(SUM(d.cantidad * pr.costo), 0)
            FROM ORDEN_VENTA ov
            INNER JOIN DETALLE_ORDEN_VENTA d ON d.ordenv_id = ov.id_ordenv
            INNER JOIN PRODUCTO pr ON pr.id_producto = d.producto_id
            WHERE ov.estado <> :estado_excluido
              AND ov.fecha_creacion >= :fecha_inicio
              AND ov.fecha_creacion < :fecha_fin
        """), p
    ).scalar()

    compras = db.session.execute(
        text("""
            SELECT COALESCE(SUM(d.cantidad * d.costo_unitario), 0)
            FROM ORDEN_COMPRA oc
            INNER JOIN DETALLE_ORDEN_COMPRA d ON d.ordenc_id = oc.id_ordenc
            WHERE oc.estado <> :estado_excluido
              AND oc.fecha_creacion >= :fecha_inicio
              AND oc.fecha_creacion < :fecha_fin
        """), p
    ).scalar()

    return {
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'ingresos': ingresos,
        'costo_ventas': costo_ventas,
        'utilidad_bruta': ingresos - costo_ventas,
        'compras': compras
    }


def obtener_ventas_por_producto(fecha_inicio, fecha_fin, estado_excluido='cancelada'):
    # Detalle del estado de resultados: ingresos y costo por producto

    resultado = db.session.execute(
        text("""
            SELECT
                pr.id_producto,
                pr.codigo,
                pr.nombre,
                SUM(d.cantidad) AS cantidad_vendida,
                SUM(d.cantidad * d.precio_unitario) AS ingresos,
                SUM(d.cantidad * pr.costo) AS costo,
                SUM(d.cantidad * d.precio_unitario) - SUM(d.cantidad * pr.costo) AS utilidad
            FROM ORDEN_VENTA ov
            INNER JOIN DETALLE_ORDEN_VENTA d ON d.ordenv_id = ov.id_ordenv
            INNER JOIN PRODUCTO pr ON pr.id_producto = d.producto_id
            WHERE ov.estado <> :estado_excluido
              AND ov.fecha_creacion >= :fecha_inicio
              AND ov.fecha_creacion < :fecha_fin
            GROUP BY pr.id_producto, pr.codigo, pr.nombre
            ORDER BY ingresos DESC
        """),
        {
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'estado_excluido': estado_excluido
        }
    )

    ventas = resultado.fetchall()

    return ventas
