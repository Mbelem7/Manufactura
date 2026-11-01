from app import db
from sqlalchemy import text


# Consulta base: el control con los datos legibles de su orden, producto, lote e inspector
_SELECT = """
    SELECT
        c.id_control,
        c.ordenp_id,
        c.lote_id,
        c.usuario_id,
        c.apariencia_ok,
        c.homogeneidad_ok,
        c.resultado,
        c.observaciones,
        c.disposicion,
        c.motivo_disposicion,
        c.fecha_disposicion,
        c.estado,
        c.fecha_creacion,
        c.fecha_modificacion,
        pr.codigo AS producto_codigo,
        pr.nombre AS producto_nombre,
        lo.codigo AS lote_codigo,
        pe.nombre_1 AS inspector_nombre_1,
        pe.apellido_1 AS inspector_apellido_1
    FROM CONTROL_CALIDAD c
    INNER JOIN ORDEN_PRODUCCION op ON op.id_ordenp = c.ordenp_id
    INNER JOIN PRODUCTO pr ON pr.id_producto = op.producto_id
    LEFT JOIN LOTE lo ON lo.id_lote = c.lote_id
    LEFT JOIN USUARIO u ON u.id_usuario = c.usuario_id
    LEFT JOIN PERSONA pe ON pe.id_persona = u.persona_id
"""


def insertar_control(
    ordenp_id,
    lote_id,
    usuario_id,
    apariencia_ok,
    homogeneidad_ok,
    resultado,
    observaciones,
    disposicion,
    estado,
    fecha
):
    # disposicion llega en None cuando el lote es no conforme y aun no se decide su destino

    resultado_sql = db.session.execute(
        text("""
            INSERT INTO CONTROL_CALIDAD
            (
                ordenp_id,
                lote_id,
                usuario_id,
                apariencia_ok,
                homogeneidad_ok,
                resultado,
                observaciones,
                disposicion,
                estado,
                fecha_creacion,
                fecha_modificacion
            )
            VALUES
            (
                :ordenp_id,
                :lote_id,
                :usuario_id,
                :apariencia_ok,
                :homogeneidad_ok,
                :resultado,
                :observaciones,
                :disposicion,
                :estado,
                :fecha,
                :fecha
            )
            RETURNING id_control
        """),
        {
            'ordenp_id': ordenp_id,
            'lote_id': lote_id,
            'usuario_id': usuario_id,
            'apariencia_ok': apariencia_ok,
            'homogeneidad_ok': homogeneidad_ok,
            'resultado': resultado,
            'observaciones': observaciones,
            'disposicion': disposicion,
            'estado': estado,
            'fecha': fecha
        }
    )

    id_control = resultado_sql.scalar()

    db.session.commit()

    return id_control


def obtener_controles():

    resultado = db.session.execute(
        text(_SELECT + " ORDER BY c.fecha_creacion DESC, c.id_control DESC")
    )

    controles = resultado.fetchall()

    return controles


def obtener_un_control(id_control):

    resultado = db.session.execute(
        text(_SELECT + " WHERE c.id_control = :id_control"),
        {
            'id_control': id_control
        }
    )

    control = resultado.fetchone()

    return control


def obtener_controles_por_orden(ordenp_id):
    # Historial de la orden: del mas reciente al mas antiguo

    resultado = db.session.execute(
        text(_SELECT + """
            WHERE c.ordenp_id = :ordenp_id
            ORDER BY c.fecha_creacion DESC, c.id_control DESC
        """),
        {
            'ordenp_id': ordenp_id
        }
    )

    controles = resultado.fetchall()

    return controles


def obtener_ultimo_control_por_orden(ordenp_id, estado='activo'):
    # El ultimo control activo de la orden decide si el lote puede continuar

    resultado = db.session.execute(
        text(_SELECT + """
            WHERE c.ordenp_id = :ordenp_id
              AND c.estado = :estado
            ORDER BY c.fecha_creacion DESC, c.id_control DESC
            LIMIT 1
        """),
        {
            'ordenp_id': ordenp_id,
            'estado': estado
        }
    )

    control = resultado.fetchone()

    return control


def registrar_disposicion(id_control, disposicion, motivo_disposicion, fecha):

    db.session.execute(
        text("""
            UPDATE CONTROL_CALIDAD
            SET
                disposicion = :disposicion,
                motivo_disposicion = :motivo_disposicion,
                fecha_disposicion = :fecha,
                fecha_modificacion = :fecha
            WHERE id_control = :id_control
        """),
        {
            'disposicion': disposicion,
            'motivo_disposicion': motivo_disposicion,
            'fecha': fecha,
            'id_control': id_control
        }
    )

    db.session.commit()