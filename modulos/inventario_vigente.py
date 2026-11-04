from datetime import date
from decimal import Decimal

from app import db
from sqlalchemy import text


# Existencias que SI se pueden usar: las de lotes sin vencer. Un lote sin fecha de vencimiento
# se considera vigente. Un lote vence al terminar el dia de su fecha: ese ultimo dia aun sirve.

def obtener_stock_vigente(producto_id, hoy=None):
    # Suma solo los lotes que no estan vencidos (todos los almacenes)

    resultado = db.session.execute(
        text("""
            SELECT COALESCE(SUM(i.cantidad), 0)
            FROM INVENTARIO i
            LEFT JOIN LOTE lo ON lo.id_lote = i.lote_id
            WHERE i.producto_id = :producto_id
              AND i.cantidad > 0
              AND (lo.fecha_vencimiento IS NULL OR lo.fecha_vencimiento >= :hoy)
        """),
        {
            'producto_id': producto_id,
            'hoy': hoy or date.today()
        }
    )

    stock = resultado.scalar()

    return stock


def obtener_stock_vencido(producto_id, hoy=None):
    # Lo que hay en lotes ya vencidos: existe en el inventario, pero no se puede usar

    resultado = db.session.execute(
        text("""
            SELECT COALESCE(SUM(i.cantidad), 0)
            FROM INVENTARIO i
            INNER JOIN LOTE lo ON lo.id_lote = i.lote_id
            WHERE i.producto_id = :producto_id
              AND i.cantidad > 0
              AND lo.fecha_vencimiento < :hoy
        """),
        {
            'producto_id': producto_id,
            'hoy': hoy or date.today()
        }
    )

    stock = resultado.scalar()

    return stock


def descontar_inventario_vigente(almacen_id, producto_id, cantidad, fecha, commit=True):
    # Resta de las existencias VIGENTES de un almacen, primero las que vencen antes (FEFO) y,
    # a igual vencimiento, las mas antiguas. Los lotes vencidos no se tocan.
    hoy = fecha.date() if hasattr(fecha, 'date') else fecha

    filas = db.session.execute(
        text("""
            SELECT i.id_inventario, i.cantidad
            FROM INVENTARIO i
            LEFT JOIN LOTE lo ON lo.id_lote = i.lote_id
            WHERE i.almacen_id = :almacen_id
              AND i.producto_id = :producto_id
              AND i.cantidad > 0
              AND (lo.fecha_vencimiento IS NULL OR lo.fecha_vencimiento >= :hoy)
            ORDER BY lo.fecha_vencimiento NULLS LAST, i.fecha_creacion, i.id_inventario
            FOR UPDATE OF i
        """),
        {
            'almacen_id': almacen_id,
            'producto_id': producto_id,
            'hoy': hoy
        }
    ).fetchall()

    pendiente = Decimal(str(cantidad))

    for fila in filas:
        if pendiente <= 0:
            break

        a_descontar = min(fila.cantidad, pendiente)

        db.session.execute(
            text("""
                UPDATE INVENTARIO
                SET
                    cantidad = cantidad - :a_descontar,
                    fecha_modificacion = :fecha
                WHERE id_inventario = :id_inventario
            """),
            {
                'a_descontar': a_descontar,
                'fecha': fecha,
                'id_inventario': fila.id_inventario
            }
        )

        pendiente -= a_descontar

    if pendiente > 0:
        vigente = sum((f.cantidad for f in filas), Decimal('0'))
        db.session.rollback()

        producto = db.session.execute(
            text("SELECT codigo FROM PRODUCTO WHERE id_producto = :producto_id"),
            {'producto_id': producto_id}
        ).scalar()

        vencido = obtener_stock_vencido(producto_id, hoy)

        mensaje = 'Existencia vigente insuficiente de %s: se necesitan %s y hay %s en lotes sin vencer' % (
            producto or producto_id, '{:,.2f}'.format(Decimal(str(cantidad))), '{:,.2f}'.format(vigente)
        )

        if vencido and vencido > 0:
            mensaje += ' (%s en lotes vencidos, que no se pueden usar)' % '{:,.2f}'.format(vencido)

        raise ValueError(mensaje)

    if commit:
        db.session.commit()