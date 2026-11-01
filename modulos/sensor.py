from app import db
from sqlalchemy import text


# Consulta base: el sensor con su centro de trabajo y su ultimo diagnostico
_SELECT = """
    SELECT
        s.id_sensor,
        s.codigo,
        s.nombre,
        s.centro_id,
        s.variable,
        s.unidad,
        s.fecha_instalacion,
        s.fecha_ultima_calibracion,
        s.estado,
        ct.codigo AS centro_codigo,
        ct.nombre AS centro_nombre,
        (
            SELECT d.diagnostico
            FROM DIAGNOSTICO_SENSOR d
            WHERE d.sensor_id = s.id_sensor
            ORDER BY d.fecha_creacion DESC, d.id_diagnostico DESC
            LIMIT 1
        ) AS ultimo_diagnostico
    FROM SENSOR s
    LEFT JOIN CENTRO_TRABAJO ct ON ct.id_centro = s.centro_id
"""


def obtener_sensores():

    resultado = db.session.execute(
        text(_SELECT + " WHERE s.estado = 'activo' ORDER BY s.codigo")
    )

    sensores = resultado.fetchall()

    return sensores


def obtener_un_sensor(id_sensor):

    resultado = db.session.execute(
        text(_SELECT + " WHERE s.id_sensor = :id_sensor"),
        {
            'id_sensor': id_sensor
        }
    )

    sensor = resultado.fetchone()

    return sensor


def obtener_sensor_por_centro(centro_id):
    # El sensor activo instalado en un centro de trabajo; None si el centro no tiene

    resultado = db.session.execute(
        text(_SELECT + """
            WHERE s.centro_id = :centro_id
              AND s.estado = 'activo'
            ORDER BY s.id_sensor
            LIMIT 1
        """),
        {
            'centro_id': centro_id
        }
    )

    sensor = resultado.fetchone()

    return sensor


def actualizar_calibracion(id_sensor, fecha_calibracion, fecha_modificacion):

    db.session.execute(
        text("""
            UPDATE SENSOR
            SET
                fecha_ultima_calibracion = :fecha_calibracion,
                fecha_modificacion = :fecha_modificacion
            WHERE id_sensor = :id_sensor
        """),
        {
            'fecha_calibracion': fecha_calibracion,
            'fecha_modificacion': fecha_modificacion,
            'id_sensor': id_sensor
        }
    )

    db.session.commit()


def insertar_diagnostico(sensor_id, ejecucion_op_id, caracteristicas_json, diagnostico, regla, probabilidad):
    # caracteristicas_json: texto JSON con las caracteristicas usadas

    resultado = db.session.execute(
        text("""
            INSERT INTO DIAGNOSTICO_SENSOR
            (
                sensor_id,
                ejecucion_op_id,
                caracteristicas,
                diagnostico,
                regla,
                probabilidad
            )
            VALUES
            (
                :sensor_id,
                :ejecucion_op_id,
                CAST(:caracteristicas AS jsonb),
                :diagnostico,
                :regla,
                :probabilidad
            )
            RETURNING id_diagnostico
        """),
        {
            'sensor_id': sensor_id,
            'ejecucion_op_id': ejecucion_op_id,
            'caracteristicas': caracteristicas_json,
            'diagnostico': diagnostico,
            'regla': regla,
            'probabilidad': probabilidad
        }
    )

    id_diagnostico = resultado.scalar()

    db.session.commit()

    return id_diagnostico


def obtener_diagnostico_por_operacion(ejecucion_op_id):

    resultado = db.session.execute(
        text("""
            SELECT
                id_diagnostico,
                sensor_id,
                ejecucion_op_id,
                caracteristicas,
                diagnostico,
                regla,
                probabilidad,
                fecha_creacion
            FROM DIAGNOSTICO_SENSOR
            WHERE ejecucion_op_id = :ejecucion_op_id
            ORDER BY id_diagnostico DESC
            LIMIT 1
        """),
        {
            'ejecucion_op_id': ejecucion_op_id
        }
    )

    diagnostico = resultado.fetchone()

    return diagnostico


def obtener_diagnosticos_por_sensor(sensor_id):

    resultado = db.session.execute(
        text("""
            SELECT
                id_diagnostico,
                sensor_id,
                ejecucion_op_id,
                caracteristicas,
                diagnostico,
                regla,
                probabilidad,
                fecha_creacion
            FROM DIAGNOSTICO_SENSOR
            WHERE sensor_id = :sensor_id
            ORDER BY fecha_creacion DESC, id_diagnostico DESC
        """),
        {
            'sensor_id': sensor_id
        }
    )

    diagnosticos = resultado.fetchall()

    return diagnosticos