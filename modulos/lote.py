from app import db
from sqlalchemy import text


def insertar_lote(
    codigo,
    fecha_creacion,
    fecha_modificacion,
    producto_id,
    fecha_vencimiento=None,
    commit=True
):
    # commit=False deja el lote dentro de la transaccion de quien lo llama
    # (recepcion, orden de produccion): si esa falla, el lote tampoco queda

    resultado = db.session.execute(
        text("""
            INSERT INTO LOTE
            (
                codigo,
                fecha_creacion,
                fecha_modificacion,
                fecha_vencimiento,
                producto_id
            )
            VALUES
            (
                :codigo,
                :fecha_creacion,
                :fecha_modificacion,
                :fecha_vencimiento,
                :producto_id
            )
            RETURNING id_lote
        """),
        {
            'codigo': codigo,
            'fecha_creacion': fecha_creacion,
            'fecha_modificacion': fecha_modificacion,
            'fecha_vencimiento': fecha_vencimiento,
            'producto_id': producto_id
        }
    )

    id_lote = resultado.scalar()

    if commit:
        db.session.commit()

    return id_lote


def revisar_capacidad(producto_id, cantidad):
    # La cantidad que entra a un lote no puede pasar de la capacidad de lote del producto
    # (unidades por caja o empaque). Sin capacidad definida no se limita.
    capacidad = db.session.execute(
        text("SELECT capacidad_lote FROM PRODUCTO WHERE id_producto = :producto_id"),
        {'producto_id': producto_id}
    ).scalar()

    if capacidad is not None and cantidad > capacidad:
        raise ValueError(
            'La cantidad (' + str(cantidad) + ') supera la capacidad máxima del lote ('
            + str(capacidad) + ')'
        )


def crear_lote_nuevo(codigo, producto_id, cantidad, fecha_vencimiento, fecha):
    # Lote para una recepcion u orden de produccion. El codigo tiene que ser nuevo:
    # si ya existe es un error (antes se reutilizaba y se mezclaba mercancia nueva
    # con la vieja, lo que rompe el FIFO). No hace commit: queda en la transaccion
    # de quien lo llama. Si algo falla lanza ValueError.
    if obtener_lote_por_codigo(codigo) is not None:
        raise ValueError('Ya existe un lote con el código ' + codigo + '. Use un código nuevo')

    if fecha_vencimiento is not None and fecha_vencimiento < fecha.date():
        raise ValueError('La fecha de vencimiento del lote ' + codigo + ' ya pasó')

    revisar_capacidad(producto_id, cantidad)

    return insertar_lote(codigo, fecha, fecha, producto_id, fecha_vencimiento, commit=False)


def obtener_lotes():

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_lote,
                t.codigo,
                t.fecha_creacion,
                t.fecha_modificacion,
                t.fecha_vencimiento,
                t.producto_id,
                pr.codigo AS producto_codigo,
                pr.nombre AS producto_nombre,
                pr.unidad_medida AS producto_unidad_medida
            FROM LOTE t
            INNER JOIN PRODUCTO pr ON pr.id_producto = t.producto_id
        """)
    )

    lotes = resultado.fetchall()

    return lotes


def obtener_un_lote(id_lote):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_lote,
                t.codigo,
                t.fecha_creacion,
                t.fecha_modificacion,
                t.fecha_vencimiento,
                t.producto_id,
                pr.codigo AS producto_codigo,
                pr.nombre AS producto_nombre,
                pr.unidad_medida AS producto_unidad_medida
            FROM LOTE t
            INNER JOIN PRODUCTO pr ON pr.id_producto = t.producto_id
            WHERE t.id_lote = :id_lote
        """),
        {
            'id_lote': id_lote
        }
    )

    lote = resultado.fetchone()

    return lote


def obtener_lotes_por_producto(producto_id):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_lote,
                t.codigo,
                t.fecha_creacion,
                t.fecha_modificacion,
                t.fecha_vencimiento,
                t.producto_id,
                pr.codigo AS producto_codigo,
                pr.nombre AS producto_nombre,
                pr.unidad_medida AS producto_unidad_medida
            FROM LOTE t
            INNER JOIN PRODUCTO pr ON pr.id_producto = t.producto_id
            WHERE t.producto_id = :producto_id
        """),
        {
            'producto_id': producto_id
        }
    )

    lotes = resultado.fetchall()

    return lotes


def obtener_lote_por_codigo(codigo):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_lote,
                t.codigo,
                t.fecha_creacion,
                t.fecha_modificacion,
                t.fecha_vencimiento,
                t.producto_id,
                pr.codigo AS producto_codigo,
                pr.nombre AS producto_nombre,
                pr.unidad_medida AS producto_unidad_medida
            FROM LOTE t
            INNER JOIN PRODUCTO pr ON pr.id_producto = t.producto_id
            WHERE t.codigo = :codigo
        """),
        {
            'codigo': codigo
        }
    )

    lote = resultado.fetchone()

    return lote


def actualizar_lote(
    id_lote,
    codigo,
    fecha_modificacion,
    fecha_vencimiento,
    producto_id
):

    db.session.execute(
        text("""
            UPDATE LOTE
            SET
                codigo = :codigo,
                fecha_modificacion = :fecha_modificacion,
                fecha_vencimiento = :fecha_vencimiento,
                producto_id = :producto_id
            WHERE id_lote = :id_lote
        """),
        {
            'id_lote': id_lote,
            'codigo': codigo,
            'fecha_modificacion': fecha_modificacion,
            'fecha_vencimiento': fecha_vencimiento,
            'producto_id': producto_id
        }
    )

    db.session.commit()


def obtener_lotes_con_existencia():

    resultado = db.session.execute(
        text("""
            SELECT
                lo.id_lote,
                lo.codigo,
                pr.id_producto,
                pr.nombre AS producto_nombre,
                pr.unidad_medida,
                lo.fecha_vencimiento,
                COALESCE(SUM(i.cantidad), 0) AS existencia
            FROM LOTE lo
            INNER JOIN PRODUCTO pr ON pr.id_producto = lo.producto_id
            LEFT JOIN INVENTARIO i ON i.lote_id = lo.id_lote
            GROUP BY lo.id_lote, lo.codigo, pr.id_producto, pr.nombre, pr.unidad_medida,
                     lo.fecha_vencimiento
            ORDER BY lo.codigo
        """)
    )

    lotes = resultado.fetchall()

    return lotes


def obtener_lotes_disponibles_venta():
    # Lotes que se pueden vender: con existencia y sin vencer.
    # Orden FIFO: primero el que entro antes al inventario (fecha_ingreso)

    resultado = db.session.execute(
        text("""
            SELECT
                lo.id_lote,
                lo.codigo,
                lo.producto_id,
                lo.fecha_vencimiento,
                MIN(i.fecha_creacion) AS fecha_ingreso,
                SUM(i.cantidad) AS existencia
            FROM LOTE lo
            INNER JOIN INVENTARIO i ON i.lote_id = lo.id_lote
            WHERE lo.fecha_vencimiento IS NULL
               OR lo.fecha_vencimiento >= CURRENT_DATE
            GROUP BY lo.id_lote, lo.codigo, lo.producto_id, lo.fecha_vencimiento
            HAVING SUM(i.cantidad) > 0
            ORDER BY lo.producto_id, MIN(i.fecha_creacion), lo.id_lote
        """)
    )

    lotes = resultado.fetchall()

    return lotes
