from app import db
from sqlalchemy import text


def insertar_despacho(
    codigo,
    estado,
    fecha_creacion,
    fecha_modificacion,
    ordenv_id,
    almacen_id
):

    resultado = db.session.execute(
        text("""
            INSERT INTO DESPACHO
            (
                codigo,
                estado,
                fecha_creacion,
                fecha_modificacion,
                ordenv_id,
                almacen_id
            )
            VALUES
            (
                :codigo,
                :estado,
                :fecha_creacion,
                :fecha_modificacion,
                :ordenv_id,
                :almacen_id
            )
            RETURNING id_despacho
        """),
        {
            'codigo': codigo,
            'estado': estado,
            'fecha_creacion': fecha_creacion,
            'fecha_modificacion': fecha_modificacion,
            'ordenv_id': ordenv_id,
            'almacen_id': almacen_id
        }
    )

    id_despacho = resultado.scalar()

    db.session.commit()

    return id_despacho


def obtener_despachos():

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_despacho,
                t.codigo,
                t.estado,
                t.fecha_creacion,
                t.fecha_modificacion,
                t.ordenv_id,
                t.almacen_id,
                al.codigo AS almacen_codigo,
                al.nombre AS almacen_nombre
            FROM DESPACHO t
            INNER JOIN ALMACEN al ON al.id_almacen = t.almacen_id
        """)
    )

    despachos = resultado.fetchall()

    return despachos


def obtener_un_despacho(id_despacho):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_despacho,
                t.codigo,
                t.estado,
                t.fecha_creacion,
                t.fecha_modificacion,
                t.ordenv_id,
                t.almacen_id,
                al.codigo AS almacen_codigo,
                al.nombre AS almacen_nombre
            FROM DESPACHO t
            INNER JOIN ALMACEN al ON al.id_almacen = t.almacen_id
            WHERE t.id_despacho = :id_despacho
        """),
        {
            'id_despacho': id_despacho
        }
    )

    despacho = resultado.fetchone()

    return despacho


def obtener_despachos_por_ordenv(ordenv_id):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_despacho,
                t.codigo,
                t.estado,
                t.fecha_creacion,
                t.fecha_modificacion,
                t.ordenv_id,
                t.almacen_id,
                al.codigo AS almacen_codigo,
                al.nombre AS almacen_nombre
            FROM DESPACHO t
            INNER JOIN ALMACEN al ON al.id_almacen = t.almacen_id
            WHERE t.ordenv_id = :ordenv_id
        """),
        {
            'ordenv_id': ordenv_id
        }
    )

    despachos = resultado.fetchall()

    return despachos


def obtener_despachos_por_almacen(almacen_id):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_despacho,
                t.codigo,
                t.estado,
                t.fecha_creacion,
                t.fecha_modificacion,
                t.ordenv_id,
                t.almacen_id,
                al.codigo AS almacen_codigo,
                al.nombre AS almacen_nombre
            FROM DESPACHO t
            INNER JOIN ALMACEN al ON al.id_almacen = t.almacen_id
            WHERE t.almacen_id = :almacen_id
        """),
        {
            'almacen_id': almacen_id
        }
    )

    despachos = resultado.fetchall()

    return despachos


def obtener_despacho_por_codigo(codigo):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_despacho,
                t.codigo,
                t.estado,
                t.fecha_creacion,
                t.fecha_modificacion,
                t.ordenv_id,
                t.almacen_id,
                al.codigo AS almacen_codigo,
                al.nombre AS almacen_nombre
            FROM DESPACHO t
            INNER JOIN ALMACEN al ON al.id_almacen = t.almacen_id
            WHERE t.codigo = :codigo
        """),
        {
            'codigo': codigo
        }
    )

    despacho = resultado.fetchone()

    return despacho


def obtener_despachos_por_estado(estado):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_despacho,
                t.codigo,
                t.estado,
                t.fecha_creacion,
                t.fecha_modificacion,
                t.ordenv_id,
                t.almacen_id,
                al.codigo AS almacen_codigo,
                al.nombre AS almacen_nombre
            FROM DESPACHO t
            INNER JOIN ALMACEN al ON al.id_almacen = t.almacen_id
            WHERE t.estado = :estado
        """),
        {
            'estado': estado
        }
    )

    despachos = resultado.fetchall()

    return despachos


def actualizar_despacho(
    id_despacho,
    codigo,
    estado,
    fecha_modificacion,
    ordenv_id,
    almacen_id
):

    db.session.execute(
        text("""
            UPDATE DESPACHO
            SET
                codigo = :codigo,
                estado = :estado,
                fecha_modificacion = :fecha_modificacion,
                ordenv_id = :ordenv_id,
                almacen_id = :almacen_id
            WHERE id_despacho = :id_despacho
        """),
        {
            'id_despacho': id_despacho,
            'codigo': codigo,
            'estado': estado,
            'fecha_modificacion': fecha_modificacion,
            'ordenv_id': ordenv_id,
            'almacen_id': almacen_id
        }
    )

    db.session.commit()


def actualizar_estado_despacho(id_despacho, estado, fecha_modificacion):
    # Baja logica: no se borra, solo cambia el estado

    db.session.execute(
        text("""
            UPDATE DESPACHO
            SET
                estado = :estado,
                fecha_modificacion = :fecha_modificacion
            WHERE id_despacho = :id_despacho
        """),
        {
            'id_despacho': id_despacho,
            'estado': estado,
            'fecha_modificacion': fecha_modificacion
        }
    )

    db.session.commit()
