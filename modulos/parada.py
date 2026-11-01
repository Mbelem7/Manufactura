from app import db
from sqlalchemy import text


# Consulta base: la parada con el nombre de su centro de trabajo
_SELECT = """
    SELECT
        pa.id_parada,
        pa.ordenp_id,
        pa.centro_id,
        pa.usuario_id,
        pa.tipo,
        pa.motivo,
        pa.fecha_inicio,
        pa.fecha_fin,
        pa.estado,
        ct.codigo AS centro_codigo,
        ct.nombre AS centro_nombre
    FROM PARADA pa
    LEFT JOIN CENTRO_TRABAJO ct ON ct.id_centro = pa.centro_id
"""


def insertar_parada(ordenp_id, centro_id, usuario_id, tipo, motivo, fecha_inicio):
    # La parada queda abierta (sin fecha_fin) hasta que se reanude el trabajo

    resultado = db.session.execute(
        text("""
            INSERT INTO PARADA
            (
                ordenp_id,
                centro_id,
                usuario_id,
                tipo,
                motivo,
                fecha_inicio,
                estado,
                fecha_creacion,
                fecha_modificacion
            )
            VALUES
            (
                :ordenp_id,
                :centro_id,
                :usuario_id,
                :tipo,
                :motivo,
                :fecha_inicio,
                'activo',
                :fecha_inicio,
                :fecha_inicio
            )
            RETURNING id_parada
        """),
        {
            'ordenp_id': ordenp_id,
            'centro_id': centro_id,
            'usuario_id': usuario_id,
            'tipo': tipo,
            'motivo': motivo,
            'fecha_inicio': fecha_inicio
        }
    )

    id_parada = resultado.scalar()

    db.session.commit()

    return id_parada


def cerrar_parada(id_parada, fecha_fin):

    db.session.execute(
        text("""
            UPDATE PARADA
            SET
                fecha_fin = :fecha_fin,
                fecha_modificacion = :fecha_fin
            WHERE id_parada = :id_parada
        """),
        {
            'fecha_fin': fecha_fin,
            'id_parada': id_parada
        }
    )

    db.session.commit()


def obtener_una_parada(id_parada):

    resultado = db.session.execute(
        text(_SELECT + " WHERE pa.id_parada = :id_parada"),
        {
            'id_parada': id_parada
        }
    )

    parada = resultado.fetchone()

    return parada


def obtener_paradas_por_orden(ordenp_id, estado='activo'):

    resultado = db.session.execute(
        text(_SELECT + """
            WHERE pa.ordenp_id = :ordenp_id
              AND pa.estado = :estado
            ORDER BY pa.fecha_inicio
        """),
        {
            'ordenp_id': ordenp_id,
            'estado': estado
        }
    )

    paradas = resultado.fetchall()

    return paradas