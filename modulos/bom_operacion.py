from app import db
from sqlalchemy import text


# Ruta de fabricacion de un producto: las operaciones (secuencia, codigo, centro de trabajo y
# tiempo estandar) se definen UNA vez en la lista de materiales (BOM) del producto. Al crear
# una orden de produccion se copian a RUTA_OPERACION, asi cada orden conserva su propia copia
# y el resto del MES (ejecuciones, OEE, sensor) sigue funcionando igual.

def obtener_operaciones_por_bom(bom_id):

    resultado = db.session.execute(
        text("""
            SELECT
                bo.id_bom_operacion,
                bo.bom_id,
                bo.codigo,
                bo.secuencia,
                bo.centro_id,
                bo.tiempo_estandar,
                bo.estado,
                ct.codigo AS centro_codigo,
                ct.nombre AS centro_nombre
            FROM BOM_OPERACION bo
            INNER JOIN CENTRO_TRABAJO ct ON ct.id_centro = bo.centro_id
            WHERE bo.bom_id = :bom_id
              AND bo.estado = 'activo'
            ORDER BY bo.secuencia
        """),
        {
            'bom_id': bom_id
        }
    )

    operaciones = resultado.fetchall()

    return operaciones


def obtener_una_operacion(id_bom_operacion):

    resultado = db.session.execute(
        text("""
            SELECT
                id_bom_operacion,
                bom_id,
                codigo,
                secuencia,
                centro_id,
                tiempo_estandar,
                estado
            FROM BOM_OPERACION
            WHERE id_bom_operacion = :id_bom_operacion
        """),
        {
            'id_bom_operacion': id_bom_operacion
        }
    )

    operacion = resultado.fetchone()

    return operacion


def insertar_operacion(bom_id, codigo, secuencia, centro_id, tiempo_estandar, fecha):

    resultado = db.session.execute(
        text("""
            INSERT INTO BOM_OPERACION
            (
                bom_id,
                codigo,
                secuencia,
                centro_id,
                tiempo_estandar,
                estado,
                fecha_creacion,
                fecha_modificacion
            )
            VALUES
            (
                :bom_id,
                :codigo,
                :secuencia,
                :centro_id,
                :tiempo_estandar,
                'activo',
                :fecha,
                :fecha
            )
            RETURNING id_bom_operacion
        """),
        {
            'bom_id': bom_id,
            'codigo': codigo,
            'secuencia': secuencia,
            'centro_id': centro_id,
            'tiempo_estandar': tiempo_estandar,
            'fecha': fecha
        }
    )

    id_bom_operacion = resultado.scalar()

    db.session.commit()

    return id_bom_operacion


def actualizar_operacion(id_bom_operacion, codigo, secuencia, centro_id, tiempo_estandar, fecha):

    db.session.execute(
        text("""
            UPDATE BOM_OPERACION
            SET
                codigo = :codigo,
                secuencia = :secuencia,
                centro_id = :centro_id,
                tiempo_estandar = :tiempo_estandar,
                fecha_modificacion = :fecha
            WHERE id_bom_operacion = :id_bom_operacion
        """),
        {
            'codigo': codigo,
            'secuencia': secuencia,
            'centro_id': centro_id,
            'tiempo_estandar': tiempo_estandar,
            'fecha': fecha,
            'id_bom_operacion': id_bom_operacion
        }
    )

    db.session.commit()


def actualizar_estado_operacion(id_bom_operacion, estado, fecha):

    db.session.execute(
        text("""
            UPDATE BOM_OPERACION
            SET
                estado = :estado,
                fecha_modificacion = :fecha
            WHERE id_bom_operacion = :id_bom_operacion
        """),
        {
            'estado': estado,
            'fecha': fecha,
            'id_bom_operacion': id_bom_operacion
        }
    )

    db.session.commit()


def copiar_a_orden(bom_id, ordenp_id, fecha):
    # Copia las operaciones activas de la ruta del BOM a la orden. Devuelve cuantas copio.

    resultado = db.session.execute(
        text("""
            INSERT INTO RUTA_OPERACION
            (
                codigo,
                tiempo_estandar,
                secuencia,
                fecha_creacion,
                fecha_modificacion,
                centro_id,
                ordenp_id,
                estado
            )
            SELECT
                bo.codigo,
                bo.tiempo_estandar,
                bo.secuencia,
                :fecha,
                :fecha,
                bo.centro_id,
                :ordenp_id,
                'activo'
            FROM BOM_OPERACION bo
            WHERE bo.bom_id = :bom_id
              AND bo.estado = 'activo'
            ORDER BY bo.secuencia
        """),
        {
            'fecha': fecha,
            'ordenp_id': ordenp_id,
            'bom_id': bom_id
        }
    )

    copiadas = resultado.rowcount

    db.session.commit()

    return copiadas