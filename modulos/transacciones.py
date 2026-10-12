from app import db
from sqlalchemy import text
from decimal import Decimal
from .inventario import aumentar_inventario, disminuir_inventario, descontar_inventario_fifo


# Flujos que tocan varias tablas: todo se guarda junto o no se guarda nada.
# Ajustar el import de .inventario segun la carpeta donde queden los archivos.


def registrar_recepcion(ordenc_id, almacen_id, codigo, detalles, fecha,
                        estado_recepcion='activo', estado_orden='recibida'):
    # detalles: lista de dicts {'producto_id', 'lote_id', 'cantidad'}
    # Crea la recepcion, sus detalles, suma al inventario y actualiza la orden de compra

    try:
        resultado = db.session.execute(
            text("""
                INSERT INTO RECEPCION
                (
                    codigo,
                    estado,
                    fecha_creacion,
                    fecha_modificacion,
                    ordenc_id,
                    almacen_id
                )
                VALUES
                (
                    :codigo,
                    :estado,
                    :fecha,
                    :fecha,
                    :ordenc_id,
                    :almacen_id
                )
                RETURNING id_recepcion
            """),
            {
                'codigo': codigo,
                'estado': estado_recepcion,
                'fecha': fecha,
                'ordenc_id': ordenc_id,
                'almacen_id': almacen_id
            }
        )

        id_recepcion = resultado.scalar()

        for d in detalles:
            db.session.execute(
                text("""
                    INSERT INTO DETALLE_RECEPCION
                    (
                        recepcion_id,
                        producto_id,
                        lote_id,
                        cantidad
                    )
                    VALUES
                    (
                        :recepcion_id,
                        :producto_id,
                        :lote_id,
                        :cantidad
                    )
                """),
                {
                    'recepcion_id': id_recepcion,
                    'producto_id': d['producto_id'],
                    'lote_id': d.get('lote_id'),
                    'cantidad': d['cantidad']
                }
            )

            aumentar_inventario(almacen_id, d['producto_id'], d.get('lote_id'),
                                d['cantidad'], fecha, commit=False)

        db.session.execute(
            text("""
                UPDATE ORDEN_COMPRA
                SET
                    estado = :estado,
                    fecha_modificacion = :fecha
                WHERE id_ordenc = :ordenc_id
            """),
            {
                'estado': estado_orden,
                'fecha': fecha,
                'ordenc_id': ordenc_id
            }
        )

        db.session.commit()

        return id_recepcion

    except Exception:
        db.session.rollback()
        raise


def registrar_despacho(ordenv_id, almacen_id, codigo, detalles, fecha,
                       estado_despacho='despachado', estado_orden='despachada'):
    # detalles: lista de dicts {'lote_id', 'cantidad'}
    # Crea el despacho, sus detalles, resta del inventario y actualiza la orden de venta

    try:
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
                    :fecha,
                    :fecha,
                    :ordenv_id,
                    :almacen_id
                )
                RETURNING id_despacho
            """),
            {
                'codigo': codigo,
                'estado': estado_despacho,
                'fecha': fecha,
                'ordenv_id': ordenv_id,
                'almacen_id': almacen_id
            }
        )

        id_despacho = resultado.scalar()

        for d in detalles:
            # detalle_despacho solo guarda el lote; el producto sale del lote
            producto_id = db.session.execute(
                text("SELECT producto_id FROM LOTE WHERE id_lote = :lote_id"),
                {'lote_id': d['lote_id']}
            ).scalar()

            if producto_id is None:
                raise ValueError('El lote ' + str(d['lote_id']) + ' no existe')

            db.session.execute(
                text("""
                    INSERT INTO DETALLE_DESPACHO
                    (
                        despacho_id,
                        lote_id,
                        cantidad
                    )
                    VALUES
                    (
                        :despacho_id,
                        :lote_id,
                        :cantidad
                    )
                """),
                {
                    'despacho_id': id_despacho,
                    'lote_id': d['lote_id'],
                    'cantidad': d['cantidad']
                }
            )

            disminuir_inventario(almacen_id, producto_id, d['lote_id'],
                                 d['cantidad'], fecha, commit=False)

        db.session.execute(
            text("""
                UPDATE ORDEN_VENTA
                SET
                    estado = :estado,
                    fecha_modificacion = :fecha
                WHERE id_ordenv = :ordenv_id
            """),
            {
                'estado': estado_orden,
                'fecha': fecha,
                'ordenv_id': ordenv_id
            }
        )

        db.session.commit()

        return id_despacho

    except Exception:
        db.session.rollback()
        raise


def finalizar_produccion(id_produccion, fecha_fin, cantidad_aceptada, cantidad_rechazada,
                         almacen_mp_id, almacen_pt_id, estado_orden='finalizada'):
    # Cierra el registro del MES y mueve el inventario:
    #   - consume la materia prima segun el BOM (se asume que detalle_bom.cantidad
    #     es por 1 unidad de producto terminado; se consume aceptadas + rechazadas)
    #   - suma al inventario el producto terminado aceptado
    #   - marca la orden de produccion como finalizada

    try:
        orden = db.session.execute(
            text("""
                SELECT
                    op.id_ordenp,
                    op.producto_id,
                    op.lote_id,
                    op.bom_id
                FROM PRODUCCION p
                INNER JOIN ORDEN_PRODUCCION op ON op.id_ordenp = p.ordenp_id
                WHERE p.id_produccion = :id_produccion
            """),
            {'id_produccion': id_produccion}
        ).fetchone()

        if orden is None:
            raise ValueError('El registro de produccion no existe')

        db.session.execute(
            text("""
                UPDATE PRODUCCION
                SET
                    fecha_fin = :fecha_fin,
                    cantidad_aceptada = :cantidad_aceptada,
                    cantidad_rechazada = :cantidad_rechazada,
                    fecha_modificacion = :fecha_fin
                WHERE id_produccion = :id_produccion
            """),
            {
                'fecha_fin': fecha_fin,
                'cantidad_aceptada': cantidad_aceptada,
                'cantidad_rechazada': cantidad_rechazada,
                'id_produccion': id_produccion
            }
        )

        componentes = db.session.execute(
            text("""
                SELECT producto_component_id, cantidad
                FROM DETALLE_BOM
                WHERE bom_id = :bom_id
            """),
            {'bom_id': orden.bom_id}
        ).fetchall()

        unidades = Decimal(str(cantidad_aceptada + cantidad_rechazada))

        for c in componentes:
            descontar_inventario_fifo(almacen_mp_id, c.producto_component_id,
                                      c.cantidad * unidades, fecha_fin, commit=False)

        if cantidad_aceptada > 0:
            aumentar_inventario(almacen_pt_id, orden.producto_id, orden.lote_id,
                                cantidad_aceptada, fecha_fin, commit=False)

        db.session.execute(
            text("""
                UPDATE ORDEN_PRODUCCION
                SET
                    estado = :estado,
                    fecha_modificacion = :fecha_fin
                WHERE id_ordenp = :ordenp_id
            """),
            {
                'estado': estado_orden,
                'fecha_fin': fecha_fin,
                'ordenp_id': orden.id_ordenp
            }
        )

        db.session.commit()

    except Exception:
        db.session.rollback()
        raise


def crear_orden_compra(proveedor_id, detalles, estado, fecha):
    # detalles: lista de dicts {'producto_id', 'cantidad', 'costo_unitario'}
    # Crea la orden y todas sus lineas en una sola transaccion

    try:
        resultado = db.session.execute(
            text("""
                INSERT INTO ORDEN_COMPRA
                (
                    estado,
                    fecha_creacion,
                    fecha_modificacion,
                    proveedor_id
                )
                VALUES
                (
                    :estado,
                    :fecha,
                    :fecha,
                    :proveedor_id
                )
                RETURNING id_ordenc
            """),
            {
                'estado': estado,
                'fecha': fecha,
                'proveedor_id': proveedor_id
            }
        )

        id_ordenc = resultado.scalar()

        for d in detalles:
            db.session.execute(
                text("""
                    INSERT INTO DETALLE_ORDEN_COMPRA
                    (
                        ordenc_id,
                        producto_id,
                        cantidad,
                        costo_unitario
                    )
                    VALUES
                    (
                        :ordenc_id,
                        :producto_id,
                        :cantidad,
                        :costo_unitario
                    )
                """),
                {
                    'ordenc_id': id_ordenc,
                    'producto_id': d['producto_id'],
                    'cantidad': d['cantidad'],
                    'costo_unitario': d['costo_unitario']
                }
            )

        db.session.commit()

        return id_ordenc

    except Exception:
        db.session.rollback()
        raise


def crear_orden_venta(cliente_id, detalles, estado, fecha):
    # detalles: lista de dicts {'producto_id', 'cantidad', 'precio_unitario'}
    # Crea la orden y todas sus lineas en una sola transaccion

    try:
        resultado = db.session.execute(
            text("""
                INSERT INTO ORDEN_VENTA
                (
                    estado,
                    fecha_creacion,
                    fecha_modificacion,
                    cliente_id
                )
                VALUES
                (
                    :estado,
                    :fecha,
                    :fecha,
                    :cliente_id
                )
                RETURNING id_ordenv
            """),
            {
                'estado': estado,
                'fecha': fecha,
                'cliente_id': cliente_id
            }
        )

        id_ordenv = resultado.scalar()

        for d in detalles:
            db.session.execute(
                text("""
                    INSERT INTO DETALLE_ORDEN_VENTA
                    (
                        ordenv_id,
                        producto_id,
                        cantidad,
                        precio_unitario
                    )
                    VALUES
                    (
                        :ordenv_id,
                        :producto_id,
                        :cantidad,
                        :precio_unitario
                    )
                """),
                {
                    'ordenv_id': id_ordenv,
                    'producto_id': d['producto_id'],
                    'cantidad': d['cantidad'],
                    'precio_unitario': d['precio_unitario']
                }
            )

        db.session.commit()

        return id_ordenv

    except Exception:
        db.session.rollback()
        raise


def crear_proveedor(codigo, empresa, nombre_1, nombre_2, apellido_1, apellido_2,
                    correo, telefono, estado, fecha):
    # Un proveedor necesita su PERSONA: se crean las dos filas en una sola transaccion

    try:
        resultado = db.session.execute(
            text("""
                INSERT INTO PERSONA
                (
                    nombre_1,
                    nombre_2,
                    apellido_1,
                    apellido_2,
                    correo,
                    telefono,
                    estado,
                    fecha_creacion,
                    fecha_modificacion
                )
                VALUES
                (
                    :nombre_1,
                    :nombre_2,
                    :apellido_1,
                    :apellido_2,
                    :correo,
                    :telefono,
                    :estado,
                    :fecha,
                    :fecha
                )
                RETURNING id_persona
            """),
            {
                'nombre_1': nombre_1,
                'nombre_2': nombre_2,
                'apellido_1': apellido_1,
                'apellido_2': apellido_2,
                'correo': correo,
                'telefono': telefono,
                'estado': estado,
                'fecha': fecha
            }
        )

        id_persona = resultado.scalar()

        resultado = db.session.execute(
            text("""
                INSERT INTO PROVEEDOR
                (
                    codigo,
                    empresa,
                    persona_id
                )
                VALUES
                (
                    :codigo,
                    :empresa,
                    :persona_id
                )
                RETURNING id_proveedor
            """),
            {
                'codigo': codigo,
                'empresa': empresa,
                'persona_id': id_persona
            }
        )

        id_proveedor = resultado.scalar()

        db.session.commit()

        return id_proveedor

    except Exception:
        db.session.rollback()
        raise


def editar_proveedor(id_proveedor, codigo, empresa, nombre_1, nombre_2, apellido_1,
                     apellido_2, correo, telefono, fecha):
    # Actualiza el proveedor y los datos de su PERSONA en una sola transaccion

    try:
        db.session.execute(
            text("""
                UPDATE PERSONA
                SET
                    nombre_1 = :nombre_1,
                    nombre_2 = :nombre_2,
                    apellido_1 = :apellido_1,
                    apellido_2 = :apellido_2,
                    correo = :correo,
                    telefono = :telefono,
                    fecha_modificacion = :fecha
                WHERE id_persona = (
                    SELECT persona_id FROM PROVEEDOR WHERE id_proveedor = :id_proveedor
                )
            """),
            {
                'nombre_1': nombre_1,
                'nombre_2': nombre_2,
                'apellido_1': apellido_1,
                'apellido_2': apellido_2,
                'correo': correo,
                'telefono': telefono,
                'fecha': fecha,
                'id_proveedor': id_proveedor
            }
        )

        db.session.execute(
            text("""
                UPDATE PROVEEDOR
                SET
                    codigo = :codigo,
                    empresa = :empresa
                WHERE id_proveedor = :id_proveedor
            """),
            {
                'codigo': codigo,
                'empresa': empresa,
                'id_proveedor': id_proveedor
            }
        )

        db.session.commit()

    except Exception:
        db.session.rollback()
        raise


def crear_bom(codigo, nombre, producto_id, componentes, estado, fecha):
    # componentes: lista de dicts {'producto_component_id', 'cantidad'}
    # Crea el BOM y todos sus componentes en una sola transaccion

    try:
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
                    :fecha,
                    :fecha,
                    :producto_id
                )
                RETURNING id_bom
            """),
            {
                'codigo': codigo,
                'nombre': nombre,
                'estado': estado,
                'fecha': fecha,
                'producto_id': producto_id
            }
        )

        id_bom = resultado.scalar()

        for c in componentes:
            db.session.execute(
                text("""
                    INSERT INTO DETALLE_BOM
                    (
                        bom_id,
                        producto_component_id,
                        cantidad
                    )
                    VALUES
                    (
                        :bom_id,
                        :producto_component_id,
                        :cantidad
                    )
                """),
                {
                    'bom_id': id_bom,
                    'producto_component_id': c['producto_component_id'],
                    'cantidad': c['cantidad']
                }
            )

        db.session.commit()

        return id_bom

    except Exception:
        db.session.rollback()
        raise


def iniciar_ejecucion(ordenp_id, usuario_id, fecha_inicio, estado_orden='en_proceso'):
    # MES: registra el inicio (hora y operador) y pone la orden en proceso, todo junto

    try:
        resultado = db.session.execute(
            text("""
                INSERT INTO PRODUCCION
                (
                    fecha_inicio,
                    cantidad_aceptada,
                    cantidad_rechazada,
                    fecha_creacion,
                    fecha_modificacion,
                    ordenp_id,
                    usuario_id
                )
                VALUES
                (
                    :fecha_inicio,
                    0,
                    0,
                    :fecha_inicio,
                    :fecha_inicio,
                    :ordenp_id,
                    :usuario_id
                )
                RETURNING id_produccion
            """),
            {
                'fecha_inicio': fecha_inicio,
                'ordenp_id': ordenp_id,
                'usuario_id': usuario_id
            }
        )

        id_produccion = resultado.scalar()

        db.session.execute(
            text("""
                UPDATE ORDEN_PRODUCCION
                SET
                    estado = :estado,
                    fecha_modificacion = :fecha_inicio
                WHERE id_ordenp = :ordenp_id
            """),
            {
                'estado': estado_orden,
                'fecha_inicio': fecha_inicio,
                'ordenp_id': ordenp_id
            }
        )

        db.session.commit()

        return id_produccion

    except Exception:
        db.session.rollback()
        raise


def crear_cliente(codigo, empresa, nombre_1, nombre_2, apellido_1, apellido_2,
                    correo, telefono, estado, fecha):
    # Un cliente necesita su PERSONA: se crean las dos filas en una sola transaccion

    try:
        resultado = db.session.execute(
            text("""
                INSERT INTO PERSONA
                (
                    nombre_1,
                    nombre_2,
                    apellido_1,
                    apellido_2,
                    correo,
                    telefono,
                    estado,
                    fecha_creacion,
                    fecha_modificacion
                )
                VALUES
                (
                    :nombre_1,
                    :nombre_2,
                    :apellido_1,
                    :apellido_2,
                    :correo,
                    :telefono,
                    :estado,
                    :fecha,
                    :fecha
                )
                RETURNING id_persona
            """),
            {
                'nombre_1': nombre_1,
                'nombre_2': nombre_2,
                'apellido_1': apellido_1,
                'apellido_2': apellido_2,
                'correo': correo,
                'telefono': telefono,
                'estado': estado,
                'fecha': fecha
            }
        )

        id_persona = resultado.scalar()

        resultado = db.session.execute(
            text("""
                INSERT INTO CLIENTE
                (
                    codigo,
                    empresa,
                    persona_id
                )
                VALUES
                (
                    :codigo,
                    :empresa,
                    :persona_id
                )
                RETURNING id_cliente
            """),
            {
                'codigo': codigo,
                'empresa': empresa,
                'persona_id': id_persona
            }
        )

        id_cliente = resultado.scalar()

        db.session.commit()

        return id_cliente

    except Exception:
        db.session.rollback()
        raise


def editar_cliente(id_cliente, codigo, empresa, nombre_1, nombre_2, apellido_1,
                     apellido_2, correo, telefono, fecha):
    # Actualiza el cliente y los datos de su PERSONA en una sola transaccion

    try:
        db.session.execute(
            text("""
                UPDATE PERSONA
                SET
                    nombre_1 = :nombre_1,
                    nombre_2 = :nombre_2,
                    apellido_1 = :apellido_1,
                    apellido_2 = :apellido_2,
                    correo = :correo,
                    telefono = :telefono,
                    fecha_modificacion = :fecha
                WHERE id_persona = (
                    SELECT persona_id FROM CLIENTE WHERE id_cliente = :id_cliente
                )
            """),
            {
                'nombre_1': nombre_1,
                'nombre_2': nombre_2,
                'apellido_1': apellido_1,
                'apellido_2': apellido_2,
                'correo': correo,
                'telefono': telefono,
                'fecha': fecha,
                'id_cliente': id_cliente
            }
        )

        db.session.execute(
            text("""
                UPDATE CLIENTE
                SET
                    codigo = :codigo,
                    empresa = :empresa
                WHERE id_cliente = :id_cliente
            """),
            {
                'codigo': codigo,
                'empresa': empresa,
                'id_cliente': id_cliente
            }
        )

        db.session.commit()

    except Exception:
        db.session.rollback()
        raise