from app import db
from sqlalchemy import text


# ---------- FACTORES DE EMISION ----------

def obtener_factores(categoria=None):

    resultado = db.session.execute(
        text("""
            SELECT
                id_factor,
                categoria,
                concepto,
                unidad,
                valor,
                fuente,
                anio,
                estado
            FROM FACTOR_EMISION
            WHERE estado = 'activo'
              AND (CAST(:categoria AS varchar) IS NULL OR categoria = CAST(:categoria AS varchar))
            ORDER BY categoria, id_factor
        """),
        {
            'categoria': categoria
        }
    )

    factores = resultado.fetchall()

    return factores


def obtener_factor_activo(categoria):
    # El factor mas reciente de la categoria (electricidad o transporte)

    resultado = db.session.execute(
        text("""
            SELECT
                id_factor,
                categoria,
                concepto,
                unidad,
                valor,
                fuente,
                anio
            FROM FACTOR_EMISION
            WHERE categoria = :categoria
              AND estado = 'activo'
            ORDER BY id_factor DESC
            LIMIT 1
        """),
        {
            'categoria': categoria
        }
    )

    factor = resultado.fetchone()

    return factor


def insertar_factor(categoria, concepto, unidad, valor, fuente, anio, fecha):

    resultado = db.session.execute(
        text("""
            INSERT INTO FACTOR_EMISION
            (
                categoria,
                concepto,
                unidad,
                valor,
                fuente,
                anio,
                estado,
                fecha_creacion,
                fecha_modificacion
            )
            VALUES
            (
                :categoria,
                :concepto,
                :unidad,
                :valor,
                :fuente,
                :anio,
                'activo',
                :fecha,
                :fecha
            )
            RETURNING id_factor
        """),
        {
            'categoria': categoria,
            'concepto': concepto,
            'unidad': unidad,
            'valor': valor,
            'fuente': fuente,
            'anio': anio,
            'fecha': fecha
        }
    )

    id_factor = resultado.scalar()

    db.session.commit()

    return id_factor


# ---------- POTENCIA DE LOS CENTROS DE TRABAJO ----------

def obtener_centros(solo_activos=False):

    resultado = db.session.execute(
        text("""
            SELECT
                id_centro,
                codigo,
                nombre,
                maquina,
                estado,
                potencia_kw
            FROM CENTRO_TRABAJO
            WHERE (CAST(:solo_activos AS boolean) = false OR estado = 'activo')
            ORDER BY codigo
        """),
        {
            'solo_activos': solo_activos
        }
    )

    centros = resultado.fetchall()

    return centros


def actualizar_potencia(id_centro, potencia_kw, fecha):

    db.session.execute(
        text("""
            UPDATE CENTRO_TRABAJO
            SET
                potencia_kw = :potencia_kw,
                fecha_modificacion = :fecha
            WHERE id_centro = :id_centro
        """),
        {
            'potencia_kw': potencia_kw,
            'fecha': fecha,
            'id_centro': id_centro
        }
    )

    db.session.commit()


# ---------- PESO DE LOS PRODUCTOS ----------

def obtener_productos_terminados():

    resultado = db.session.execute(
        text("""
            SELECT
                id_producto,
                codigo,
                nombre,
                unidad_medida,
                peso_kg
            FROM PRODUCTO
            WHERE tipo_producto = 'producto_terminado'
              AND estado = 'activo'
            ORDER BY codigo
        """)
    )

    productos = resultado.fetchall()

    return productos


def actualizar_peso(id_producto, peso_kg, fecha):

    db.session.execute(
        text("""
            UPDATE PRODUCTO
            SET
                peso_kg = :peso_kg,
                fecha_modificacion = :fecha
            WHERE id_producto = :id_producto
        """),
        {
            'peso_kg': peso_kg,
            'fecha': fecha,
            'id_producto': id_producto
        }
    )

    db.session.commit()


# ---------- TRANSPORTE DE LOS DESPACHOS ----------

def obtener_despachos_para_transporte():

    resultado = db.session.execute(
        text("""
            SELECT
                de.id_despacho,
                de.codigo,
                de.estado,
                de.fecha_creacion,
                de.distancia_km,
                de.vehiculo,
                de.factor_transporte_id,
                ov.id_ordenv
            FROM DESPACHO de
            INNER JOIN ORDEN_VENTA ov ON ov.id_ordenv = de.ordenv_id
            ORDER BY de.fecha_creacion DESC, de.id_despacho DESC
        """)
    )

    despachos = resultado.fetchall()

    return despachos


def actualizar_transporte(id_despacho, distancia_km, vehiculo, factor_transporte_id, fecha):

    db.session.execute(
        text("""
            UPDATE DESPACHO
            SET
                distancia_km = :distancia_km,
                vehiculo = :vehiculo,
                factor_transporte_id = :factor_transporte_id,
                fecha_modificacion = :fecha
            WHERE id_despacho = :id_despacho
        """),
        {
            'distancia_km': distancia_km,
            'vehiculo': vehiculo,
            'factor_transporte_id': factor_transporte_id,
            'fecha': fecha,
            'id_despacho': id_despacho
        }
    )

    db.session.commit()


def obtener_despachos_por_lote(lote_id):
    # Despachos activos que sacaron unidades de un lote, con su peso, distancia y factor

    resultado = db.session.execute(
        text("""
            SELECT
                de.id_despacho,
                de.codigo,
                de.vehiculo,
                de.distancia_km,
                fe.valor AS factor_valor,
                SUM(dd.cantidad) AS unidades,
                pr.peso_kg
            FROM DESPACHO de
            INNER JOIN DETALLE_DESPACHO dd ON dd.despacho_id = de.id_despacho
            INNER JOIN LOTE lo ON lo.id_lote = dd.lote_id
            INNER JOIN PRODUCTO pr ON pr.id_producto = lo.producto_id
            LEFT JOIN FACTOR_EMISION fe ON fe.id_factor = de.factor_transporte_id
            WHERE dd.lote_id = :lote_id
              AND de.estado = 'despachado'
            GROUP BY de.id_despacho, de.codigo, de.vehiculo, de.distancia_km, fe.valor, pr.peso_kg
            ORDER BY de.id_despacho
        """),
        {
            'lote_id': lote_id
        }
    )

    despachos = resultado.fetchall()

    return despachos