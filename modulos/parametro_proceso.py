from app import db
from sqlalchemy import text


def obtener_parametro(centro_id, variable, estado='activo'):
    # Objetivo y limites de especificacion de una variable en un centro de trabajo.
    # Si el centro no tiene parametro, no tiene sensor.

    resultado = db.session.execute(
        text("""
            SELECT
                id_parametro,
                centro_id,
                variable,
                unidad,
                valor_objetivo,
                limite_inferior,
                limite_superior
            FROM PARAMETRO_PROCESO
            WHERE centro_id = :centro_id
              AND variable = :variable
              AND estado = :estado
            ORDER BY id_parametro DESC
            LIMIT 1
        """),
        {
            'centro_id': centro_id,
            'variable': variable,
            'estado': estado
        }
    )

    parametro = resultado.fetchone()

    return parametro