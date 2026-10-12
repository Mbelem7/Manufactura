from app import db
from sqlalchemy import text


def insertar_proveedor(codigo, empresa, persona_id):

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
            'persona_id': persona_id
        }
    )

    id_proveedor = resultado.scalar()

    db.session.commit()

    return id_proveedor


def obtener_proveedores():

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_proveedor,
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
            FROM PROVEEDOR t
            INNER JOIN PERSONA pe ON pe.id_persona = t.persona_id
        """)
    )

    proveedores = resultado.fetchall()

    return proveedores


def obtener_un_proveedor(id_proveedor):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_proveedor,
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
            FROM PROVEEDOR t
            INNER JOIN PERSONA pe ON pe.id_persona = t.persona_id
            WHERE t.id_proveedor = :id_proveedor
        """),
        {
            'id_proveedor': id_proveedor
        }
    )

    proveedor = resultado.fetchone()

    return proveedor


def obtener_proveedor_por_persona(persona_id):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_proveedor,
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
            FROM PROVEEDOR t
            INNER JOIN PERSONA pe ON pe.id_persona = t.persona_id
            WHERE t.persona_id = :persona_id
        """),
        {
            'persona_id': persona_id
        }
    )

    proveedor = resultado.fetchone()

    return proveedor


def obtener_proveedor_por_codigo(codigo):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_proveedor,
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
            FROM PROVEEDOR t
            INNER JOIN PERSONA pe ON pe.id_persona = t.persona_id
            WHERE t.codigo = :codigo
        """),
        {
            'codigo': codigo
        }
    )

    proveedor = resultado.fetchone()

    return proveedor


def actualizar_proveedor(
    id_proveedor,
    codigo,
    empresa,
    persona_id
):

    db.session.execute(
        text("""
            UPDATE PROVEEDOR
            SET
                codigo = :codigo,
                empresa = :empresa,
                persona_id = :persona_id
            WHERE id_proveedor = :id_proveedor
        """),
        {
            'id_proveedor': id_proveedor,
            'codigo': codigo,
            'empresa': empresa,
            'persona_id': persona_id
        }
    )

    db.session.commit()


def dar_de_baja_proveedor(id_proveedor, estado, fecha_modificacion):
    # proveedor no tiene estado propio: la baja se registra en su PERSONA

    db.session.execute(
        text("""
            UPDATE PERSONA
            SET
                estado = :estado,
                fecha_modificacion = :fecha_modificacion
            WHERE id_persona = (
                SELECT persona_id FROM PROVEEDOR WHERE id_proveedor = :id_proveedor
            )
        """),
        {
            'estado': estado,
            'fecha_modificacion': fecha_modificacion,
            'id_proveedor': id_proveedor
        }
    )

    db.session.commit()


def obtener_proveedores_por_estado(estado):
    # Util para llenar listas desplegables solo con registros activos

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_proveedor,
                t.codigo,
                t.empresa,
                t.persona_id,
                pe.nombre_1,
                pe.apellido_1,
                pe.correo,
                pe.telefono,
                pe.estado
            FROM PROVEEDOR t
            INNER JOIN PERSONA pe ON pe.id_persona = t.persona_id
            WHERE pe.estado = :estado
        """),
        {
            'estado': estado
        }
    )

    proveedores = resultado.fetchall()

    return proveedores
