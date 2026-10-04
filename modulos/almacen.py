from app import db
from sqlalchemy import text


def insertar_almacen(
    codigo,
    nombre,
    tipo,
    ubicacion,
    estado,
    fecha_creacion,
    fecha_modificacion
):

    resultado = db.session.execute(
        text("""
            INSERT INTO ALMACEN
            (
                codigo,
                nombre,
                tipo,
                ubicacion,
                estado,
                fecha_creacion,
                fecha_modificacion
            )
            VALUES
            (
                :codigo,
                :nombre,
                :tipo,
                :ubicacion,
                :estado,
                :fecha_creacion,
                :fecha_modificacion
            )
            RETURNING id_almacen
        """),
        {
            'codigo': codigo,
            'nombre': nombre,
            'tipo': tipo,
            'ubicacion': ubicacion,
            'estado': estado,
            'fecha_creacion': fecha_creacion,
            'fecha_modificacion': fecha_modificacion
        }
    )

    id_almacen = resultado.scalar()

    db.session.commit()

    return id_almacen


def obtener_almacenes():

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_almacen,
                t.codigo,
                t.nombre,
                t.tipo,
                t.ubicacion,
                t.estado,
                t.fecha_creacion,
                t.fecha_modificacion
            FROM ALMACEN t
        """)
    )

    almacenes = resultado.fetchall()

    return almacenes


def obtener_un_almacen(id_almacen):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_almacen,
                t.codigo,
                t.nombre,
                t.tipo,
                t.ubicacion,
                t.estado,
                t.fecha_creacion,
                t.fecha_modificacion
            FROM ALMACEN t
            WHERE t.id_almacen = :id_almacen
        """),
        {
            'id_almacen': id_almacen
        }
    )

    almacen = resultado.fetchone()

    return almacen


def obtener_almacen_por_codigo(codigo):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_almacen,
                t.codigo,
                t.nombre,
                t.tipo,
                t.ubicacion,
                t.estado,
                t.fecha_creacion,
                t.fecha_modificacion
            FROM ALMACEN t
            WHERE t.codigo = :codigo
        """),
        {
            'codigo': codigo
        }
    )

    almacen = resultado.fetchone()

    return almacen


def obtener_almacenes_por_estado(estado):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_almacen,
                t.codigo,
                t.nombre,
                t.tipo,
                t.ubicacion,
                t.estado,
                t.fecha_creacion,
                t.fecha_modificacion
            FROM ALMACEN t
            WHERE t.estado = :estado
        """),
        {
            'estado': estado
        }
    )

    almacenes = resultado.fetchall()

    return almacenes


def actualizar_almacen(
    id_almacen,
    codigo,
    nombre,
    tipo,
    ubicacion,
    estado,
    fecha_modificacion
):

    db.session.execute(
        text("""
            UPDATE ALMACEN
            SET
                codigo = :codigo,
                nombre = :nombre,
                tipo = :tipo,
                ubicacion = :ubicacion,
                estado = :estado,
                fecha_modificacion = :fecha_modificacion
            WHERE id_almacen = :id_almacen
        """),
        {
            'id_almacen': id_almacen,
            'codigo': codigo,
            'nombre': nombre,
            'tipo': tipo,
            'ubicacion': ubicacion,
            'estado': estado,
            'fecha_modificacion': fecha_modificacion
        }
    )

    db.session.commit()


def actualizar_estado_almacen(id_almacen, estado, fecha_modificacion):
    # Baja logica: no se borra, solo cambia el estado

    db.session.execute(
        text("""
            UPDATE ALMACEN
            SET
                estado = :estado,
                fecha_modificacion = :fecha_modificacion
            WHERE id_almacen = :id_almacen
        """),
        {
            'id_almacen': id_almacen,
            'estado': estado,
            'fecha_modificacion': fecha_modificacion
        }
    )

    db.session.commit()
