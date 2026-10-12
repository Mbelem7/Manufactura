from app import db
from sqlalchemy import text


def insertar_producto(
    nombre,
    descripcion,
    tipo_producto,
    presentacion,
    precio,
    costo,
    unidad_medida,
    codigo,
    estado,
    fecha_creacion,
    fecha_modificacion
):

    resultado = db.session.execute(
        text("""
            INSERT INTO PRODUCTO
            (
                nombre,
                descripcion,
                tipo_producto,
                presentacion,
                precio,
                costo,
                unidad_medida,
                codigo,
                estado,
                fecha_creacion,
                fecha_modificacion
            )
            VALUES
            (
                :nombre,
                :descripcion,
                :tipo_producto,
                :presentacion,
                :precio,
                :costo,
                :unidad_medida,
                :codigo,
                :estado,
                :fecha_creacion,
                :fecha_modificacion
            )
            RETURNING id_producto
        """),
        {
            'nombre': nombre,
            'descripcion': descripcion,
            'tipo_producto': tipo_producto,
            'presentacion': presentacion,
            'precio': precio,
            'costo': costo,
            'unidad_medida': unidad_medida,
            'codigo': codigo,
            'estado': estado,
            'fecha_creacion': fecha_creacion,
            'fecha_modificacion': fecha_modificacion
        }
    )

    id_producto = resultado.scalar()

    db.session.commit()

    return id_producto


def obtener_productos():

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_producto,
                t.nombre,
                t.descripcion,
                t.tipo_producto,
                t.presentacion,
                t.precio,
                t.costo,
                t.unidad_medida,
                t.codigo,
                t.estado,
                t.fecha_creacion,
                t.fecha_modificacion
            FROM PRODUCTO t
        """)
    )

    productos = resultado.fetchall()

    return productos


def obtener_un_producto(id_producto):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_producto,
                t.nombre,
                t.descripcion,
                t.tipo_producto,
                t.presentacion,
                t.precio,
                t.costo,
                t.unidad_medida,
                t.codigo,
                t.estado,
                t.fecha_creacion,
                t.fecha_modificacion
            FROM PRODUCTO t
            WHERE t.id_producto = :id_producto
        """),
        {
            'id_producto': id_producto
        }
    )

    producto = resultado.fetchone()

    return producto


def obtener_producto_por_codigo(codigo):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_producto,
                t.nombre,
                t.descripcion,
                t.tipo_producto,
                t.presentacion,
                t.precio,
                t.costo,
                t.unidad_medida,
                t.codigo,
                t.estado,
                t.fecha_creacion,
                t.fecha_modificacion
            FROM PRODUCTO t
            WHERE t.codigo = :codigo
        """),
        {
            'codigo': codigo
        }
    )

    producto = resultado.fetchone()

    return producto


def obtener_productos_por_estado(estado):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_producto,
                t.nombre,
                t.descripcion,
                t.tipo_producto,
                t.presentacion,
                t.precio,
                t.costo,
                t.unidad_medida,
                t.codigo,
                t.estado,
                t.fecha_creacion,
                t.fecha_modificacion
            FROM PRODUCTO t
            WHERE t.estado = :estado
        """),
        {
            'estado': estado
        }
    )

    productos = resultado.fetchall()

    return productos


def actualizar_producto(
    id_producto,
    nombre,
    descripcion,
    tipo_producto,
    presentacion,
    precio,
    costo,
    unidad_medida,
    codigo,
    estado,
    fecha_modificacion
):

    db.session.execute(
        text("""
            UPDATE PRODUCTO
            SET
                nombre = :nombre,
                descripcion = :descripcion,
                tipo_producto = :tipo_producto,
                presentacion = :presentacion,
                precio = :precio,
                costo = :costo,
                unidad_medida = :unidad_medida,
                codigo = :codigo,
                estado = :estado,
                fecha_modificacion = :fecha_modificacion
            WHERE id_producto = :id_producto
        """),
        {
            'id_producto': id_producto,
            'nombre': nombre,
            'descripcion': descripcion,
            'tipo_producto': tipo_producto,
            'presentacion': presentacion,
            'precio': precio,
            'costo': costo,
            'unidad_medida': unidad_medida,
            'codigo': codigo,
            'estado': estado,
            'fecha_modificacion': fecha_modificacion
        }
    )

    db.session.commit()


def actualizar_estado_producto(id_producto, estado, fecha_modificacion):
    # Baja logica: no se borra, solo cambia el estado

    db.session.execute(
        text("""
            UPDATE PRODUCTO
            SET
                estado = :estado,
                fecha_modificacion = :fecha_modificacion
            WHERE id_producto = :id_producto
        """),
        {
            'id_producto': id_producto,
            'estado': estado,
            'fecha_modificacion': fecha_modificacion
        }
    )

    db.session.commit()
