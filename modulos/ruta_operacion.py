from app import db
from sqlalchemy import text


def insertar_ruta_operacion(
    codigo,
    tiempo_estandar,
    secuencia,
    fecha_creacion,
    fecha_modificacion,
    centro_id,
    ordenp_id
):

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
                ordenp_id
            )
            VALUES
            (
                :codigo,
                :tiempo_estandar,
                :secuencia,
                :fecha_creacion,
                :fecha_modificacion,
                :centro_id,
                :ordenp_id
            )
            RETURNING id_ruta
        """),
        {
            'codigo': codigo,
            'tiempo_estandar': tiempo_estandar,
            'secuencia': secuencia,
            'fecha_creacion': fecha_creacion,
            'fecha_modificacion': fecha_modificacion,
            'centro_id': centro_id,
            'ordenp_id': ordenp_id
        }
    )

    id_ruta = resultado.scalar()

    db.session.commit()

    return id_ruta


def obtener_rutas_operacion():

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_ruta,
                t.codigo,
                t.tiempo_estandar,
                t.secuencia,
                t.fecha_creacion,
                t.fecha_modificacion,
                t.centro_id,
                t.ordenp_id,
                ct.codigo AS centro_trabajo_codigo,
                ct.nombre AS centro_trabajo_nombre
            FROM RUTA_OPERACION t
            INNER JOIN CENTRO_TRABAJO ct ON ct.id_centro = t.centro_id
        """)
    )

    rutas_operacion = resultado.fetchall()

    return rutas_operacion


def obtener_un_ruta_operacion(id_ruta):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_ruta,
                t.codigo,
                t.tiempo_estandar,
                t.secuencia,
                t.fecha_creacion,
                t.fecha_modificacion,
                t.centro_id,
                t.ordenp_id,
                ct.codigo AS centro_trabajo_codigo,
                ct.nombre AS centro_trabajo_nombre
            FROM RUTA_OPERACION t
            INNER JOIN CENTRO_TRABAJO ct ON ct.id_centro = t.centro_id
            WHERE t.id_ruta = :id_ruta
        """),
        {
            'id_ruta': id_ruta
        }
    )

    ruta_operacion = resultado.fetchone()

    return ruta_operacion


def obtener_rutas_operacion_por_centro(centro_id):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_ruta,
                t.codigo,
                t.tiempo_estandar,
                t.secuencia,
                t.fecha_creacion,
                t.fecha_modificacion,
                t.centro_id,
                t.ordenp_id,
                ct.codigo AS centro_trabajo_codigo,
                ct.nombre AS centro_trabajo_nombre
            FROM RUTA_OPERACION t
            INNER JOIN CENTRO_TRABAJO ct ON ct.id_centro = t.centro_id
            WHERE t.centro_id = :centro_id
        """),
        {
            'centro_id': centro_id
        }
    )

    rutas_operacion = resultado.fetchall()

    return rutas_operacion


def obtener_rutas_operacion_por_ordenp(ordenp_id):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_ruta,
                t.codigo,
                t.tiempo_estandar,
                t.secuencia,
                t.fecha_creacion,
                t.fecha_modificacion,
                t.centro_id,
                t.ordenp_id,
                ct.codigo AS centro_trabajo_codigo,
                ct.nombre AS centro_trabajo_nombre
            FROM RUTA_OPERACION t
            INNER JOIN CENTRO_TRABAJO ct ON ct.id_centro = t.centro_id
            WHERE t.ordenp_id = :ordenp_id
        """),
        {
            'ordenp_id': ordenp_id
        }
    )

    rutas_operacion = resultado.fetchall()

    return rutas_operacion


def obtener_ruta_operacion_por_codigo(codigo):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_ruta,
                t.codigo,
                t.tiempo_estandar,
                t.secuencia,
                t.fecha_creacion,
                t.fecha_modificacion,
                t.centro_id,
                t.ordenp_id,
                ct.codigo AS centro_trabajo_codigo,
                ct.nombre AS centro_trabajo_nombre
            FROM RUTA_OPERACION t
            INNER JOIN CENTRO_TRABAJO ct ON ct.id_centro = t.centro_id
            WHERE t.codigo = :codigo
        """),
        {
            'codigo': codigo
        }
    )

    ruta_operacion = resultado.fetchone()

    return ruta_operacion


def actualizar_ruta_operacion(
    id_ruta,
    codigo,
    tiempo_estandar,
    secuencia,
    fecha_modificacion,
    centro_id,
    ordenp_id
):

    db.session.execute(
        text("""
            UPDATE RUTA_OPERACION
            SET
                codigo = :codigo,
                tiempo_estandar = :tiempo_estandar,
                secuencia = :secuencia,
                fecha_modificacion = :fecha_modificacion,
                centro_id = :centro_id,
                ordenp_id = :ordenp_id
            WHERE id_ruta = :id_ruta
        """),
        {
            'id_ruta': id_ruta,
            'codigo': codigo,
            'tiempo_estandar': tiempo_estandar,
            'secuencia': secuencia,
            'fecha_modificacion': fecha_modificacion,
            'centro_id': centro_id,
            'ordenp_id': ordenp_id
        }
    )

    db.session.commit()
