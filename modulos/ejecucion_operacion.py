from app import db
from sqlalchemy import text


# Consulta base: la operacion ejecutada con los datos de su ruta, centro y orden
_SELECT = """
    SELECT
        e.id_ejecucion_op,
        e.produccion_id,
        e.ruta_id,
        e.usuario_id,
        e.fecha_inicio,
        e.fecha_fin,
        e.tiempo_estandar_min,
        e.factor_aceleracion,
        e.escenario,
        e.estado,
        r.codigo AS ruta_codigo,
        r.secuencia,
        r.centro_id,
        r.tipo AS ruta_tipo,
        ct.codigo AS centro_codigo,
        ct.nombre AS centro_nombre,
        ct.maquina,
        p.ordenp_id
    FROM EJECUCION_OPERACION e
    INNER JOIN RUTA_OPERACION r ON r.id_ruta = e.ruta_id
    INNER JOIN CENTRO_TRABAJO ct ON ct.id_centro = r.centro_id
    INNER JOIN PRODUCCION p ON p.id_produccion = e.produccion_id
"""


def iniciar_operacion(
    produccion_id,
    ruta_id,
    usuario_id,
    fecha_inicio,
    tiempo_estandar_min,
    factor_aceleracion,
    escenario
):

    resultado = db.session.execute(
        text("""
            INSERT INTO EJECUCION_OPERACION
            (
                produccion_id,
                ruta_id,
                usuario_id,
                fecha_inicio,
                tiempo_estandar_min,
                factor_aceleracion,
                escenario,
                estado,
                fecha_creacion,
                fecha_modificacion
            )
            VALUES
            (
                :produccion_id,
                :ruta_id,
                :usuario_id,
                :fecha_inicio,
                :tiempo_estandar_min,
                :factor_aceleracion,
                :escenario,
                'en_curso',
                :fecha_inicio,
                :fecha_inicio
            )
            RETURNING id_ejecucion_op
        """),
        {
            'produccion_id': produccion_id,
            'ruta_id': ruta_id,
            'usuario_id': usuario_id,
            'fecha_inicio': fecha_inicio,
            'tiempo_estandar_min': tiempo_estandar_min,
            'factor_aceleracion': factor_aceleracion,
            'escenario': escenario
        }
    )

    id_ejecucion_op = resultado.scalar()

    db.session.commit()

    return id_ejecucion_op


def terminar_operacion(id_ejecucion_op, fecha_fin):

    db.session.execute(
        text("""
            UPDATE EJECUCION_OPERACION
            SET
                fecha_fin = :fecha_fin,
                estado = 'terminada',
                fecha_modificacion = :fecha_fin
            WHERE id_ejecucion_op = :id_ejecucion_op
        """),
        {
            'fecha_fin': fecha_fin,
            'id_ejecucion_op': id_ejecucion_op
        }
    )

    db.session.commit()


def obtener_una_ejecucion(id_ejecucion_op):

    resultado = db.session.execute(
        text(_SELECT + " WHERE e.id_ejecucion_op = :id_ejecucion_op"),
        {
            'id_ejecucion_op': id_ejecucion_op
        }
    )

    ejecucion = resultado.fetchone()

    return ejecucion


def obtener_ejecuciones_por_produccion(produccion_id):

    resultado = db.session.execute(
        text(_SELECT + """
            WHERE e.produccion_id = :produccion_id
            ORDER BY r.secuencia
        """),
        {
            'produccion_id': produccion_id
        }
    )

    ejecuciones = resultado.fetchall()

    return ejecuciones


def contar_operaciones_pendientes(produccion_id):
    # Operaciones activas de la ruta de la orden que aun no estan terminadas

    resultado = db.session.execute(
        text("""
            SELECT COUNT(*)
            FROM RUTA_OPERACION r
            WHERE r.ordenp_id = (
                    SELECT ordenp_id FROM PRODUCCION WHERE id_produccion = :produccion_id
                  )
              AND r.estado = 'activo'
              AND NOT EXISTS (
                    SELECT 1
                    FROM EJECUCION_OPERACION e
                    WHERE e.produccion_id = :produccion_id
                      AND e.ruta_id = r.id_ruta
                      AND e.estado = 'terminada'
                  )
        """),
        {
            'produccion_id': produccion_id
        }
    )

    pendientes = resultado.scalar()

    return pendientes