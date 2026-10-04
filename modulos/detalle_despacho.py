from app import db
from sqlalchemy import text


def insertar_detalle_despacho(despacho_id, lote_id, cantidad):

    resultado = db.session.execute(
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
            RETURNING id_detalle_despacho
        """),
        {
            'despacho_id': despacho_id,
            'lote_id': lote_id,
            'cantidad': cantidad
        }
    )

    id_detalle_despacho = resultado.scalar()

    db.session.commit()

    return id_detalle_despacho


def obtener_detalles_despacho():

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_detalle_despacho,
                t.despacho_id,
                t.lote_id,
                t.cantidad,
                lo.codigo AS lote_codigo
            FROM DETALLE_DESPACHO t
            LEFT JOIN LOTE lo ON lo.id_lote = t.lote_id
        """)
    )

    detalles_despacho = resultado.fetchall()

    return detalles_despacho


def obtener_un_detalle_despacho(id_detalle_despacho):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_detalle_despacho,
                t.despacho_id,
                t.lote_id,
                t.cantidad,
                lo.codigo AS lote_codigo
            FROM DETALLE_DESPACHO t
            LEFT JOIN LOTE lo ON lo.id_lote = t.lote_id
            WHERE t.id_detalle_despacho = :id_detalle_despacho
        """),
        {
            'id_detalle_despacho': id_detalle_despacho
        }
    )

    detalle_despacho = resultado.fetchone()

    return detalle_despacho


def obtener_detalles_despacho_por_despacho(despacho_id):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_detalle_despacho,
                t.despacho_id,
                t.lote_id,
                t.cantidad,
                lo.codigo AS lote_codigo
            FROM DETALLE_DESPACHO t
            LEFT JOIN LOTE lo ON lo.id_lote = t.lote_id
            WHERE t.despacho_id = :despacho_id
        """),
        {
            'despacho_id': despacho_id
        }
    )

    detalles_despacho = resultado.fetchall()

    return detalles_despacho


def obtener_detalles_despacho_por_lote(lote_id):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_detalle_despacho,
                t.despacho_id,
                t.lote_id,
                t.cantidad,
                lo.codigo AS lote_codigo
            FROM DETALLE_DESPACHO t
            LEFT JOIN LOTE lo ON lo.id_lote = t.lote_id
            WHERE t.lote_id = :lote_id
        """),
        {
            'lote_id': lote_id
        }
    )

    detalles_despacho = resultado.fetchall()

    return detalles_despacho


def actualizar_detalle_despacho(
    id_detalle_despacho,
    despacho_id,
    lote_id,
    cantidad
):

    db.session.execute(
        text("""
            UPDATE DETALLE_DESPACHO
            SET
                despacho_id = :despacho_id,
                lote_id = :lote_id,
                cantidad = :cantidad
            WHERE id_detalle_despacho = :id_detalle_despacho
        """),
        {
            'id_detalle_despacho': id_detalle_despacho,
            'despacho_id': despacho_id,
            'lote_id': lote_id,
            'cantidad': cantidad
        }
    )

    db.session.commit()


def eliminar_detalle_despacho(id_detalle_despacho):
    # Las lineas de detalle si se pueden borrar (no tienen estado)

    db.session.execute(
        text("""
            DELETE FROM DETALLE_DESPACHO
            WHERE id_detalle_despacho = :id_detalle_despacho
        """),
        {
            'id_detalle_despacho': id_detalle_despacho
        }
    )

    db.session.commit()
