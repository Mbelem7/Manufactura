from app import db
from sqlalchemy import text


# La lista de materiales tiene dos niveles: la receta del producto se divide en etapas
# (mezcla, envasado) y cada etapa tiene sus materiales. La etapa se guarda en cada linea
# de DETALLE_BOM (columna "etapa"), asi que el consumo de materia prima, que suma todas las
# lineas del BOM, sigue funcionando igual.

def obtener_componentes_con_etapa(bom_id):

    resultado = db.session.execute(
        text("""
            SELECT
                t.id_detalle_bom,
                t.bom_id,
                t.producto_component_id,
                t.cantidad,
                t.etapa,
                pr.codigo AS producto_codigo,
                pr.nombre AS producto_nombre,
                pr.unidad_medida AS producto_unidad_medida
            FROM DETALLE_BOM t
            INNER JOIN PRODUCTO pr ON pr.id_producto = t.producto_component_id
            WHERE t.bom_id = :bom_id
            ORDER BY pr.codigo
        """),
        {
            'bom_id': bom_id
        }
    )

    componentes = resultado.fetchall()

    return componentes


def actualizar_etapa(id_detalle_bom, etapa):

    db.session.execute(
        text("""
            UPDATE DETALLE_BOM
            SET etapa = :etapa
            WHERE id_detalle_bom = :id_detalle_bom
        """),
        {
            'etapa': etapa,
            'id_detalle_bom': id_detalle_bom
        }
    )

    db.session.commit()


def asignar_etapas(bom_id, etapas_por_producto):
    # etapas_por_producto: {producto_component_id: etapa}
    # Se usa justo despues de crear un BOM para dejar cada componente en su etapa

    for producto_component_id, etapa in etapas_por_producto.items():
        db.session.execute(
            text("""
                UPDATE DETALLE_BOM
                SET etapa = :etapa
                WHERE bom_id = :bom_id
                  AND producto_component_id = :producto_component_id
            """),
            {
                'etapa': etapa,
                'bom_id': bom_id,
                'producto_component_id': producto_component_id
            }
        )

    db.session.commit()