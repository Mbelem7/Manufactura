from app import db
from sqlalchemy import text


def insertar_cliente(codigo, empresa, persona_id):

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
            'persona_id': persona_id
        }
    )

    id_cliente = resultado.scalar()

    db.session.commit()

    return id_cliente


def obtener_clientes():

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_cliente,
                t.codigo,
                t.empresa,
                t.persona_id,
                pe.nombre_1 AS persona_nombre_1,
                pe.nombre_2 AS persona_nombre_2,
                pe.apellido_1 AS persona_apellido_1,
                pe.apellido_2 AS persona_apellido_2,
                pe.correo AS persona_correo,
                pe.telefono AS persona_telefono,
                pe.estado AS persona_estado
            FROM CLIENTE t
            INNER JOIN PERSONA pe ON pe.id_persona = t.persona_id
        """)
    )

    clientes = resultado.fetchall()

    return clientes


def obtener_un_cliente(id_cliente):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_cliente,
                t.codigo,
                t.empresa,
                t.persona_id,
                pe.nombre_1 AS persona_nombre_1,
                pe.nombre_2 AS persona_nombre_2,
                pe.apellido_1 AS persona_apellido_1,
                pe.apellido_2 AS persona_apellido_2,
                pe.correo AS persona_correo,
                pe.telefono AS persona_telefono,
                pe.estado AS persona_estado
            FROM CLIENTE t
            INNER JOIN PERSONA pe ON pe.id_persona = t.persona_id
            WHERE t.id_cliente = :id_cliente
        """),
        {
            'id_cliente': id_cliente
        }
    )

    cliente = resultado.fetchone()

    return cliente


def obtener_cliente_por_persona(persona_id):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_cliente,
                t.codigo,
                t.empresa,
                t.persona_id,
                pe.nombre_1 AS persona_nombre_1,
                pe.nombre_2 AS persona_nombre_2,
                pe.apellido_1 AS persona_apellido_1,
                pe.apellido_2 AS persona_apellido_2,
                pe.correo AS persona_correo,
                pe.telefono AS persona_telefono,
                pe.estado AS persona_estado
            FROM CLIENTE t
            INNER JOIN PERSONA pe ON pe.id_persona = t.persona_id
            WHERE t.persona_id = :persona_id
        """),
        {
            'persona_id': persona_id
        }
    )

    cliente = resultado.fetchone()

    return cliente


def obtener_cliente_por_codigo(codigo):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_cliente,
                t.codigo,
                t.empresa,
                t.persona_id,
                pe.nombre_1 AS persona_nombre_1,
                pe.nombre_2 AS persona_nombre_2,
                pe.apellido_1 AS persona_apellido_1,
                pe.apellido_2 AS persona_apellido_2,
                pe.correo AS persona_correo,
                pe.telefono AS persona_telefono,
                pe.estado AS persona_estado
            FROM CLIENTE t
            INNER JOIN PERSONA pe ON pe.id_persona = t.persona_id
            WHERE t.codigo = :codigo
        """),
        {
            'codigo': codigo
        }
    )

    cliente = resultado.fetchone()

    return cliente


def actualizar_cliente(
    id_cliente,
    codigo,
    empresa,
    persona_id
):

    db.session.execute(
        text("""
            UPDATE CLIENTE
            SET
                codigo = :codigo,
                empresa = :empresa,
                persona_id = :persona_id
            WHERE id_cliente = :id_cliente
        """),
        {
            'id_cliente': id_cliente,
            'codigo': codigo,
            'empresa': empresa,
            'persona_id': persona_id
        }
    )

    db.session.commit()


def dar_de_baja_cliente(id_cliente, estado, fecha_modificacion):
    # cliente no tiene estado propio: la baja se registra en su PERSONA

    db.session.execute(
        text("""
            UPDATE PERSONA
            SET
                estado = :estado,
                fecha_modificacion = :fecha_modificacion
            WHERE id_persona = (
                SELECT persona_id FROM CLIENTE WHERE id_cliente = :id_cliente
            )
        """),
        {
            'estado': estado,
            'fecha_modificacion': fecha_modificacion,
            'id_cliente': id_cliente
        }
    )

    db.session.commit()


def obtener_clientes_por_estado(estado):
    # Util para llenar listas desplegables solo con registros activos

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_cliente,
                t.codigo,
                t.empresa,
                t.persona_id,
                pe.nombre_1,
                pe.apellido_1,
                pe.correo,
                pe.telefono,
                pe.estado
            FROM CLIENTE t
            INNER JOIN PERSONA pe ON pe.id_persona = t.persona_id
            WHERE pe.estado = :estado
        """),
        {
            'estado': estado
        }
    )

    clientes = resultado.fetchall()

    return clientes
