from app import db
from sqlalchemy import text


def insertar_lecturas(ejecucion_op_id, lecturas):
    # lecturas: lista de dicts {'variable', 'valor', 'unidad', 'minuto_proceso', 'fecha_hora'}
    # Si dos solicitudes intentan guardar el mismo minuto, el indice unico evita duplicados

    for l in lecturas:
        db.session.execute(
            text("""
                INSERT INTO LECTURA_SENSOR
                (
                    ejecucion_op_id,
                    variable,
                    valor,
                    unidad,
                    minuto_proceso,
                    fecha_hora,
                    simulada
                )
                VALUES
                (
                    :ejecucion_op_id,
                    :variable,
                    :valor,
                    :unidad,
                    :minuto_proceso,
                    :fecha_hora,
                    true
                )
                ON CONFLICT DO NOTHING
            """),
            {
                'ejecucion_op_id': ejecucion_op_id,
                'variable': l['variable'],
                'valor': l['valor'],
                'unidad': l['unidad'],
                'minuto_proceso': l['minuto_proceso'],
                'fecha_hora': l['fecha_hora']
            }
        )

    db.session.commit()


def obtener_lecturas(ejecucion_op_id):

    resultado = db.session.execute(
        text("""
            SELECT
                id_lectura,
                ejecucion_op_id,
                variable,
                valor,
                unidad,
                minuto_proceso,
                fecha_hora
            FROM LECTURA_SENSOR
            WHERE ejecucion_op_id = :ejecucion_op_id
            ORDER BY minuto_proceso, id_lectura
        """),
        {
            'ejecucion_op_id': ejecucion_op_id
        }
    )

    lecturas = resultado.fetchall()

    return lecturas


def obtener_ultimo_minuto(ejecucion_op_id):
    # Ultimo minuto simulado ya guardado; None si todavia no hay lecturas

    resultado = db.session.execute(
        text("""
            SELECT MAX(minuto_proceso)
            FROM LECTURA_SENSOR
            WHERE ejecucion_op_id = :ejecucion_op_id
        """),
        {
            'ejecucion_op_id': ejecucion_op_id
        }
    )

    ultimo = resultado.scalar()

    return ultimo