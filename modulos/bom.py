from app import db
from sqlalchemy import text


def insertar_bom(
    codigo,
    nombre,
    estado,
    fecha_creacion,
    fecha_modificacion,
    producto_id
):

    resultado = db.session.execute(
        text("""
            INSERT INTO BOM
            (
                codigo,
                nombre,
                estado,
                fecha_creacion,
                fecha_modificacion,
                producto_id
            )
            VALUES
            (
                :codigo,
                :nombre,
                :estado,
                :fecha_creacion,
                :fecha_modificacion,
                :producto_id
            )
            RETURNING id_bom
        """),
        {
            'codigo': codigo,
            'nombre': nombre,
            'estado': estado,
            'fecha_creacion': fecha_creacion,
            'fecha_modificacion': fecha_modificacion,
            'producto_id': producto_id
        }
    )

    id_bom = resultado.scalar()

    db.session.commit()

    return id_bom


def obtener_boms():

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_bom,
                t.codigo,
                t.nombre,
                t.estado,
                t.fecha_creacion,
                t.fecha_modificacion,
                t.producto_id,
                pr.codigo AS producto_codigo,
                pr.nombre AS producto_nombre,
                pr.unidad_medida AS producto_unidad_medida
            FROM BOM t
            INNER JOIN PRODUCTO pr ON pr.id_producto = t.producto_id
        """)
    )

    boms = resultado.fetchall()

    return boms


def obtener_un_bom(id_bom):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_bom,
                t.codigo,
                t.nombre,
                t.estado,
                t.fecha_creacion,
                t.fecha_modificacion,
                t.producto_id,
                pr.codigo AS producto_codigo,
                pr.nombre AS producto_nombre,
                pr.unidad_medida AS producto_unidad_medida
            FROM BOM t
            INNER JOIN PRODUCTO pr ON pr.id_producto = t.producto_id
            WHERE t.id_bom = :id_bom
        """),
        {
            'id_bom': id_bom
        }
    )

    bom = resultado.fetchone()

    return bom


def obtener_boms_por_producto(producto_id):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_bom,
                t.codigo,
                t.nombre,
                t.estado,
                t.fecha_creacion,
                t.fecha_modificacion,
                t.producto_id,
                pr.codigo AS producto_codigo,
                pr.nombre AS producto_nombre,
                pr.unidad_medida AS producto_unidad_medida
            FROM BOM t
            INNER JOIN PRODUCTO pr ON pr.id_producto = t.producto_id
            WHERE t.producto_id = :producto_id
        """),
        {
            'producto_id': producto_id
        }
    )

    boms = resultado.fetchall()

    return boms


def obtener_bom_por_codigo(codigo):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_bom,
                t.codigo,
                t.nombre,
                t.estado,
                t.fecha_creacion,
                t.fecha_modificacion,
                t.producto_id,
                pr.codigo AS producto_codigo,
                pr.nombre AS producto_nombre,
                pr.unidad_medida AS producto_unidad_medida
            FROM BOM t
            INNER JOIN PRODUCTO pr ON pr.id_producto = t.producto_id
            WHERE t.codigo = :codigo
        """),
        {
            'codigo': codigo
        }
    )

    bom = resultado.fetchone()

    return bom


def obtener_boms_por_estado(estado):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_bom,
                t.codigo,
                t.nombre,
                t.estado,
                t.fecha_creacion,
                t.fecha_modificacion,
                t.producto_id,
                pr.codigo AS producto_codigo,
                pr.nombre AS producto_nombre,
                pr.unidad_medida AS producto_unidad_medida
            FROM BOM t
            INNER JOIN PRODUCTO pr ON pr.id_producto = t.producto_id
            WHERE t.estado = :estado
        """),
        {
            'estado': estado
        }
    )

    boms = resultado.fetchall()

    return boms


def actualizar_bom(
    id_bom,
    codigo,
    nombre,
    estado,
    fecha_modificacion,
    producto_id
):

    db.session.execute(
        text("""
            UPDATE BOM
            SET
                codigo = :codigo,
                nombre = :nombre,
                estado = :estado,
                fecha_modificacion = :fecha_modificacion,
                producto_id = :producto_id
            WHERE id_bom = :id_bom
        """),
        {
            'id_bom': id_bom,
            'codigo': codigo,
            'nombre': nombre,
            'estado': estado,
            'fecha_modificacion': fecha_modificacion,
            'producto_id': producto_id
        }
    )

    db.session.commit()


def actualizar_estado_bom(id_bom, estado, fecha_modificacion):
    # Baja logica: no se borra, solo cambia el estado

    db.session.execute(
        text("""
            UPDATE BOM
            SET
                estado = :estado,
                fecha_modificacion = :fecha_modificacion
            WHERE id_bom = :id_bom
        """),
        {
            'id_bom': id_bom,
            'estado': estado,
            'fecha_modificacion': fecha_modificacion
        }
    )

    db.session.commit()


def obtener_bom_completo(id_bom):
    # Lista de materiales: los componentes con su cantidad

    resultado = db.session.execute(
        text("""
            SELECT
                b.id_bom,
                b.codigo AS bom_codigo,
                b.nombre AS bom_nombre,
                b.producto_id,
                d.id_detalle_bom,
                d.producto_component_id,
                pr.codigo AS componente_codigo,
                pr.nombre AS componente_nombre,
                pr.unidad_medida,
                d.cantidad
            FROM BOM b
            INNER JOIN DETALLE_BOM d ON d.bom_id = b.id_bom
            INNER JOIN PRODUCTO pr ON pr.id_producto = d.producto_component_id
            WHERE b.id_bom = :id_bom
        """),
        {
            'id_bom': id_bom
        }
    )

    bom = resultado.fetchall()

    return bom
