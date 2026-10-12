from app import db
from sqlalchemy import text


def obtener_conteo_ordenes_por_estado():
    # Tarjetas del dashboard: cuantas ordenes hay en cada estado

    resultado = db.session.execute(
        text("""
            SELECT 'orden_compra' AS modulo, estado, COUNT(*) AS total
            FROM ORDEN_COMPRA
            GROUP BY estado
            UNION ALL
            SELECT 'orden_venta' AS modulo, estado, COUNT(*) AS total
            FROM ORDEN_VENTA
            GROUP BY estado
            UNION ALL
            SELECT 'orden_produccion' AS modulo, estado, COUNT(*) AS total
            FROM ORDEN_PRODUCCION
            GROUP BY estado
        """)
    )

    conteo = resultado.fetchall()

    return conteo


def obtener_ventas_por_mes(anio, estado_excluido='cancelada'):
    # Grafica de ventas mensuales

    resultado = db.session.execute(
        text("""
            SELECT
                DATE_TRUNC('month', ov.fecha_creacion) AS mes,
                SUM(d.cantidad * d.precio_unitario) AS total
            FROM ORDEN_VENTA ov
            INNER JOIN DETALLE_ORDEN_VENTA d ON d.ordenv_id = ov.id_ordenv
            WHERE EXTRACT(YEAR FROM ov.fecha_creacion) = :anio
              AND ov.estado <> :estado_excluido
            GROUP BY 1
            ORDER BY 1
        """),
        {
            'anio': anio,
            'estado_excluido': estado_excluido
        }
    )

    ventas = resultado.fetchall()

    return ventas


def obtener_productos_bajo_stock(minimo):
    # Alerta del dashboard: productos con stock menor al minimo indicado

    resultado = db.session.execute(
        text("""
            SELECT
                pr.id_producto,
                pr.codigo,
                pr.nombre,
                pr.unidad_medida,
                COALESCE(SUM(i.cantidad), 0) AS stock_actual
            FROM PRODUCTO pr
            LEFT JOIN INVENTARIO i ON i.producto_id = pr.id_producto
            GROUP BY pr.id_producto, pr.codigo, pr.nombre, pr.unidad_medida
            HAVING COALESCE(SUM(i.cantidad), 0) < :minimo
            ORDER BY stock_actual
        """),
        {
            'minimo': minimo
        }
    )

    productos = resultado.fetchall()

    return productos
