from app import db
from sqlalchemy import text


def insertar_alerta(tipo, nivel, ordenp_id, lectura_id, regla, mensaje, valor, probabilidad, fecha):

    resultado = db.session.execute(
        text("""
            INSERT INTO ALERTA_PROCESO
            (
                tipo,
                nivel,
                ordenp_id,
                lectura_id,
                regla,
                mensaje,
                valor,
                probabilidad,
                estado,
                fecha_creacion,
                fecha_modificacion
            )
            VALUES
            (
                :tipo,
                :nivel,
                :ordenp_id,
                :lectura_id,
                :regla,
                :mensaje,
                :valor,
                :probabilidad,
                'abierta',
                :fecha,
                :fecha
            )
            RETURNING id_alerta
        """),
        {
            'tipo': tipo,
            'nivel': nivel,
            'ordenp_id': ordenp_id,
            'lectura_id': lectura_id,
            'regla': regla,
            'mensaje': mensaje,
            'valor': valor,
            'probabilidad': probabilidad,
            'fecha': fecha
        }
    )

    id_alerta = resultado.scalar()

    db.session.commit()

    return id_alerta


def existe_alerta_en_operacion(ejecucion_op_id, regla):
    # Para guardar solo la primera alerta de cada regla en una operacion

    resultado = db.session.execute(
        text("""
            SELECT COUNT(*)
            FROM ALERTA_PROCESO a
            INNER JOIN LECTURA_SENSOR l ON l.id_lectura = a.lectura_id
            WHERE l.ejecucion_op_id = :ejecucion_op_id
              AND a.regla = :regla
        """),
        {
            'ejecucion_op_id': ejecucion_op_id,
            'regla': regla
        }
    )

    cantidad = resultado.scalar()

    return cantidad > 0


def obtener_alertas_por_operacion(ejecucion_op_id):

    resultado = db.session.execute(
        text("""
            SELECT
                a.id_alerta,
                a.tipo,
                a.nivel,
                a.regla,
                a.mensaje,
                a.valor,
                a.estado,
                a.fecha_creacion,
                l.minuto_proceso
            FROM ALERTA_PROCESO a
            INNER JOIN LECTURA_SENSOR l ON l.id_lectura = a.lectura_id
            WHERE l.ejecucion_op_id = :ejecucion_op_id
            ORDER BY l.minuto_proceso, a.id_alerta
        """),
        {
            'ejecucion_op_id': ejecucion_op_id
        }
    )

    alertas = resultado.fetchall()

    return alertas