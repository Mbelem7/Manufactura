from app import db
from sqlalchemy import text


# Consultas agregadas para los tableros por rubro. Todas aceptan un periodo opcional
# (inicio incluido, fin excluido); si no se indica, cuentan todo el historial.

def _periodo(columna, inicio, fin):
    # Devuelve el trozo de SQL y los parametros del filtro de fechas
    sql = ""
    params = {}

    if inicio is not None:
        sql += " AND " + columna + " >= :inicio"
        params['inicio'] = inicio

    if fin is not None:
        sql += " AND " + columna + " < :fin"
        params['fin'] = fin

    return sql, params


def _consultar(sql, params=None):
    return db.session.execute(text(sql), params or {})


# ---------- VENTAS ----------

def ventas_resumen(inicio, fin):
    filtro, p = _periodo("ov.fecha_creacion", inicio, fin)

    return _consultar("""
        SELECT
            COUNT(DISTINCT ov.id_ordenv) AS ordenes,
            COALESCE(SUM(d.cantidad * d.precio_unitario), 0) AS total
        FROM ORDEN_VENTA ov
        LEFT JOIN DETALLE_ORDEN_VENTA d ON d.ordenv_id = ov.id_ordenv
        WHERE ov.estado <> 'cancelada'""" + filtro, p).fetchone()


def ventas_por_estado(inicio, fin):
    filtro, p = _periodo("ov.fecha_creacion", inicio, fin)

    return _consultar("""
        SELECT ov.estado, COUNT(*) AS total
        FROM ORDEN_VENTA ov
        WHERE 1 = 1""" + filtro + """
        GROUP BY ov.estado
        ORDER BY ov.estado""", p).fetchall()


def ventas_por_mes(inicio, fin):
    filtro, p = _periodo("ov.fecha_creacion", inicio, fin)

    return _consultar("""
        SELECT
            DATE_TRUNC('month', ov.fecha_creacion) AS mes,
            SUM(d.cantidad * d.precio_unitario) AS total
        FROM ORDEN_VENTA ov
        INNER JOIN DETALLE_ORDEN_VENTA d ON d.ordenv_id = ov.id_ordenv
        WHERE ov.estado <> 'cancelada'""" + filtro + """
        GROUP BY 1
        ORDER BY 1""", p).fetchall()


def ventas_por_producto(inicio, fin, limite=5):
    filtro, p = _periodo("ov.fecha_creacion", inicio, fin)
    p['limite'] = limite

    return _consultar("""
        SELECT
            pr.codigo,
            pr.nombre,
            SUM(d.cantidad) AS unidades,
            SUM(d.cantidad * d.precio_unitario) AS monto
        FROM ORDEN_VENTA ov
        INNER JOIN DETALLE_ORDEN_VENTA d ON d.ordenv_id = ov.id_ordenv
        INNER JOIN PRODUCTO pr ON pr.id_producto = d.producto_id
        WHERE ov.estado <> 'cancelada'""" + filtro + """
        GROUP BY pr.codigo, pr.nombre
        ORDER BY monto DESC
        LIMIT :limite""", p).fetchall()


def ventas_por_cliente(inicio, fin, limite=5):
    filtro, p = _periodo("ov.fecha_creacion", inicio, fin)
    p['limite'] = limite

    return _consultar("""
        SELECT
            cl.codigo,
            cl.empresa,
            SUM(d.cantidad * d.precio_unitario) AS monto
        FROM ORDEN_VENTA ov
        INNER JOIN DETALLE_ORDEN_VENTA d ON d.ordenv_id = ov.id_ordenv
        INNER JOIN CLIENTE cl ON cl.id_cliente = ov.cliente_id
        WHERE ov.estado <> 'cancelada'""" + filtro + """
        GROUP BY cl.codigo, cl.empresa
        ORDER BY monto DESC
        LIMIT :limite""", p).fetchall()


def unidades_despachadas(inicio, fin):
    filtro, p = _periodo("de.fecha_creacion", inicio, fin)

    return _consultar("""
        SELECT COALESCE(SUM(dd.cantidad), 0)
        FROM DETALLE_DESPACHO dd
        INNER JOIN DESPACHO de ON de.id_despacho = dd.despacho_id
        WHERE de.estado = 'despachado'""" + filtro, p).scalar()


# ---------- COMPRAS ----------

def compras_resumen(inicio, fin):
    filtro, p = _periodo("oc.fecha_creacion", inicio, fin)

    return _consultar("""
        SELECT
            COUNT(DISTINCT oc.id_ordenc) AS ordenes,
            COALESCE(SUM(d.cantidad * d.costo_unitario), 0) AS total
        FROM ORDEN_COMPRA oc
        LEFT JOIN DETALLE_ORDEN_COMPRA d ON d.ordenc_id = oc.id_ordenc
        WHERE oc.estado <> 'cancelada'""" + filtro, p).fetchone()


def compras_por_estado(inicio, fin):
    filtro, p = _periodo("oc.fecha_creacion", inicio, fin)

    return _consultar("""
        SELECT oc.estado, COUNT(*) AS total
        FROM ORDEN_COMPRA oc
        WHERE 1 = 1""" + filtro + """
        GROUP BY oc.estado
        ORDER BY oc.estado""", p).fetchall()


def compras_por_mes(inicio, fin):
    filtro, p = _periodo("oc.fecha_creacion", inicio, fin)

    return _consultar("""
        SELECT
            DATE_TRUNC('month', oc.fecha_creacion) AS mes,
            SUM(d.cantidad * d.costo_unitario) AS total
        FROM ORDEN_COMPRA oc
        INNER JOIN DETALLE_ORDEN_COMPRA d ON d.ordenc_id = oc.id_ordenc
        WHERE oc.estado <> 'cancelada'""" + filtro + """
        GROUP BY 1
        ORDER BY 1""", p).fetchall()


def compras_por_proveedor(inicio, fin, limite=5):
    filtro, p = _periodo("oc.fecha_creacion", inicio, fin)
    p['limite'] = limite

    return _consultar("""
        SELECT
            pv.codigo,
            pv.empresa,
            SUM(d.cantidad * d.costo_unitario) AS monto
        FROM ORDEN_COMPRA oc
        INNER JOIN DETALLE_ORDEN_COMPRA d ON d.ordenc_id = oc.id_ordenc
        INNER JOIN PROVEEDOR pv ON pv.id_proveedor = oc.proveedor_id
        WHERE oc.estado <> 'cancelada'""" + filtro + """
        GROUP BY pv.codigo, pv.empresa
        ORDER BY monto DESC
        LIMIT :limite""", p).fetchall()


def compras_por_material(inicio, fin, limite=5):
    filtro, p = _periodo("oc.fecha_creacion", inicio, fin)
    p['limite'] = limite

    return _consultar("""
        SELECT
            pr.codigo,
            pr.nombre,
            SUM(d.cantidad * d.costo_unitario) AS monto
        FROM ORDEN_COMPRA oc
        INNER JOIN DETALLE_ORDEN_COMPRA d ON d.ordenc_id = oc.id_ordenc
        INNER JOIN PRODUCTO pr ON pr.id_producto = d.producto_id
        WHERE oc.estado <> 'cancelada'""" + filtro + """
        GROUP BY pr.codigo, pr.nombre
        ORDER BY monto DESC
        LIMIT :limite""", p).fetchall()


def horas_hasta_recepcion(inicio, fin):
    # Tiempo medio entre crear una orden de compra y recibirla
    filtro, p = _periodo("oc.fecha_creacion", inicio, fin)

    return _consultar("""
        SELECT AVG(EXTRACT(EPOCH FROM (re.fecha_creacion - oc.fecha_creacion)) / 3600)
        FROM ORDEN_COMPRA oc
        INNER JOIN RECEPCION re ON re.ordenc_id = oc.id_ordenc
        WHERE re.estado = 'activo'""" + filtro, p).scalar()


# ---------- PRODUCCION Y CALIDAD ----------

def ordenes_por_estado(inicio, fin):
    filtro, p = _periodo("op.fecha_creacion", inicio, fin)

    return _consultar("""
        SELECT op.estado, COUNT(*) AS total
        FROM ORDEN_PRODUCCION op
        WHERE 1 = 1""" + filtro + """
        GROUP BY op.estado
        ORDER BY op.estado""", p).fetchall()


def produccion_por_dia(inicio, fin):
    filtro, p = _periodo("pd.fecha_fin", inicio, fin)

    return _consultar("""
        SELECT
            DATE(pd.fecha_fin) AS dia,
            SUM(pd.cantidad_aceptada) AS aceptadas,
            SUM(pd.cantidad_rechazada) AS rechazadas
        FROM PRODUCCION pd
        WHERE pd.fecha_fin IS NOT NULL""" + filtro + """
        GROUP BY 1
        ORDER BY 1""", p).fetchall()


def controles_por_resultado(inicio, fin):
    filtro, p = _periodo("c.fecha_creacion", inicio, fin)

    return _consultar("""
        SELECT c.resultado, COUNT(*) AS total
        FROM CONTROL_CALIDAD c
        WHERE c.estado = 'activo'""" + filtro + """
        GROUP BY c.resultado
        ORDER BY c.resultado""", p).fetchall()


def controles_por_disposicion(inicio, fin):
    filtro, p = _periodo("c.fecha_creacion", inicio, fin)

    return _consultar("""
        SELECT COALESCE(c.disposicion, 'pendiente') AS disposicion, COUNT(*) AS total
        FROM CONTROL_CALIDAD c
        WHERE c.estado = 'activo'""" + filtro + """
        GROUP BY 1
        ORDER BY 1""", p).fetchall()


def alertas_por_nivel(inicio, fin):
    filtro, p = _periodo("a.fecha_creacion", inicio, fin)

    return _consultar("""
        SELECT a.nivel, COUNT(*) AS total
        FROM ALERTA_PROCESO a
        WHERE 1 = 1""" + filtro + """
        GROUP BY a.nivel
        ORDER BY a.nivel""", p).fetchall()


# ---------- INVENTARIO ----------

def productos_con_existencia():
    # Existencia total de cada producto activo (todos los almacenes y lotes)

    return _consultar("""
        SELECT
            pr.id_producto,
            pr.codigo,
            pr.nombre,
            pr.tipo_producto,
            pr.unidad_medida,
            COALESCE(SUM(i.cantidad), 0) AS existencia
        FROM PRODUCTO pr
        LEFT JOIN INVENTARIO i ON i.producto_id = pr.id_producto
        WHERE pr.estado = 'activo'
        GROUP BY pr.id_producto, pr.codigo, pr.nombre, pr.tipo_producto, pr.unidad_medida
        ORDER BY pr.codigo""").fetchall()


def existencias_por_almacen():

    return _consultar("""
        SELECT
            al.codigo,
            al.nombre,
            COUNT(DISTINCT i.producto_id) AS productos,
            COUNT(DISTINCT i.lote_id) AS lotes
        FROM ALMACEN al
        LEFT JOIN INVENTARIO i ON i.almacen_id = al.id_almacen AND i.cantidad > 0
        WHERE al.estado = 'activo'
        GROUP BY al.codigo, al.nombre
        ORDER BY al.codigo""").fetchall()


def lotes_mas_antiguos(limite=5):

    return _consultar("""
        SELECT
            lo.codigo AS lote,
            pr.codigo AS producto_codigo,
            pr.nombre AS producto_nombre,
            pr.unidad_medida,
            lo.fecha_creacion,
            SUM(i.cantidad) AS existencia
        FROM INVENTARIO i
        INNER JOIN LOTE lo ON lo.id_lote = i.lote_id
        INNER JOIN PRODUCTO pr ON pr.id_producto = lo.producto_id
        WHERE i.cantidad > 0
        GROUP BY lo.codigo, pr.codigo, pr.nombre, pr.unidad_medida, lo.fecha_creacion
        ORDER BY lo.fecha_creacion
        LIMIT :limite""", {'limite': limite}).fetchall()