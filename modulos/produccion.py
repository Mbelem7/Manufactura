from app import db
from sqlalchemy import text


def insertar_produccion(
    fecha_inicio,
    fecha_fin,
    cantidad_aceptada,
    cantidad_rechazada,
    fecha_creacion,
    fecha_modificacion,
    ordenp_id,
    usuario_id
):

    resultado = db.session.execute(
        text("""
            INSERT INTO PRODUCCION
            (
                fecha_inicio,
                fecha_fin,
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
                :fecha_fin,
                :cantidad_aceptada,
                :cantidad_rechazada,
                :fecha_creacion,
                :fecha_modificacion,
                :ordenp_id,
                :usuario_id
            )
            RETURNING id_produccion
        """),
        {
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'cantidad_aceptada': cantidad_aceptada,
            'cantidad_rechazada': cantidad_rechazada,
            'fecha_creacion': fecha_creacion,
            'fecha_modificacion': fecha_modificacion,
            'ordenp_id': ordenp_id,
            'usuario_id': usuario_id
        }
    )

    id_produccion = resultado.scalar()

    db.session.commit()

    return id_produccion


def obtener_producciones():

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_produccion,
                t.fecha_inicio,
                t.fecha_fin,
                t.cantidad_aceptada,
                t.cantidad_rechazada,
                t.fecha_creacion,
                t.fecha_modificacion,
                t.ordenp_id,
                t.usuario_id
            FROM PRODUCCION t
        """)
    )

    producciones = resultado.fetchall()

    return producciones


def obtener_un_produccion(id_produccion):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_produccion,
                t.fecha_inicio,
                t.fecha_fin,
                t.cantidad_aceptada,
                t.cantidad_rechazada,
                t.fecha_creacion,
                t.fecha_modificacion,
                t.ordenp_id,
                t.usuario_id
            FROM PRODUCCION t
            WHERE t.id_produccion = :id_produccion
        """),
        {
            'id_produccion': id_produccion
        }
    )

    produccion = resultado.fetchone()

    return produccion


def obtener_producciones_por_ordenp(ordenp_id):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_produccion,
                t.fecha_inicio,
                t.fecha_fin,
                t.cantidad_aceptada,
                t.cantidad_rechazada,
                t.fecha_creacion,
                t.fecha_modificacion,
                t.ordenp_id,
                t.usuario_id
            FROM PRODUCCION t
            WHERE t.ordenp_id = :ordenp_id
        """),
        {
            'ordenp_id': ordenp_id
        }
    )

    producciones = resultado.fetchall()

    return producciones


def obtener_producciones_por_usuario(usuario_id):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_produccion,
                t.fecha_inicio,
                t.fecha_fin,
                t.cantidad_aceptada,
                t.cantidad_rechazada,
                t.fecha_creacion,
                t.fecha_modificacion,
                t.ordenp_id,
                t.usuario_id
            FROM PRODUCCION t
            WHERE t.usuario_id = :usuario_id
        """),
        {
            'usuario_id': usuario_id
        }
    )

    producciones = resultado.fetchall()

    return producciones


def actualizar_produccion(
    id_produccion,
    fecha_inicio,
    fecha_fin,
    cantidad_aceptada,
    cantidad_rechazada,
    fecha_modificacion,
    ordenp_id,
    usuario_id
):

    db.session.execute(
        text("""
            UPDATE PRODUCCION
            SET
                fecha_inicio = :fecha_inicio,
                fecha_fin = :fecha_fin,
                cantidad_aceptada = :cantidad_aceptada,
                cantidad_rechazada = :cantidad_rechazada,
                fecha_modificacion = :fecha_modificacion,
                ordenp_id = :ordenp_id,
                usuario_id = :usuario_id
            WHERE id_produccion = :id_produccion
        """),
        {
            'id_produccion': id_produccion,
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'cantidad_aceptada': cantidad_aceptada,
            'cantidad_rechazada': cantidad_rechazada,
            'fecha_modificacion': fecha_modificacion,
            'ordenp_id': ordenp_id,
            'usuario_id': usuario_id
        }
    )

    db.session.commit()


def iniciar_produccion(ordenp_id, usuario_id, fecha_inicio):
    # MES: boton "Iniciar" (registra hora y operador)

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

    db.session.commit()

    return id_produccion


def terminar_produccion(id_produccion, fecha_fin, cantidad_aceptada, cantidad_rechazada):
    # MES: boton "Terminar" (registra hora y cantidades buena/rechazada)
    # Para ademas mover el inventario usar finalizar_produccion() de transacciones.py

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

    db.session.commit()


def obtener_produccion_en_curso():
    # Registros iniciados que aun no se terminan

    resultado = db.session.execute(
        text("""
            SELECT
                p.id_produccion,
                p.fecha_inicio,
                p.ordenp_id,
                pr.nombre AS producto_nombre,
                pe.nombre_1,
                pe.apellido_1
            FROM PRODUCCION p
            INNER JOIN ORDEN_PRODUCCION op ON op.id_ordenp = p.ordenp_id
            INNER JOIN PRODUCTO pr ON pr.id_producto = op.producto_id
            INNER JOIN USUARIO u ON u.id_usuario = p.usuario_id
            INNER JOIN PERSONA pe ON pe.id_persona = u.persona_id
            WHERE p.fecha_fin IS NULL
            ORDER BY p.fecha_inicio
        """)
    )

    produccion = resultado.fetchall()

    return produccion


def obtener_produccion_con_operador():
    # Historial del MES con el operador que ejecuto cada registro

    resultado = db.session.execute(
        text("""
            SELECT
                p.id_produccion,
                p.fecha_inicio,
                p.fecha_fin,
                p.cantidad_aceptada,
                p.cantidad_rechazada,
                p.ordenp_id,
                pr.codigo AS producto_codigo,
                pr.nombre AS producto_nombre,
                u.id_usuario,
                pe.nombre_1,
                pe.apellido_1
            FROM PRODUCCION p
            INNER JOIN ORDEN_PRODUCCION op ON op.id_ordenp = p.ordenp_id
            INNER JOIN PRODUCTO pr ON pr.id_producto = op.producto_id
            INNER JOIN USUARIO u ON u.id_usuario = p.usuario_id
            INNER JOIN PERSONA pe ON pe.id_persona = u.persona_id
            ORDER BY p.fecha_inicio DESC
        """)
    )

    produccion = resultado.fetchall()

    return produccion
