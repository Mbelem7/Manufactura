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
