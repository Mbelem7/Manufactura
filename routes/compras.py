from flask import Blueprint, render_template


compras_bp = Blueprint(
    "compras",
    __name__,
    url_prefix="/compras"
)


# ÓRDENES DE COMPRA

@compras_bp.route("/ordenes")
def ordenes():
    return render_template(
        "compras/ordenes/index.html"
    )


@compras_bp.route("/ordenes/nueva")
def orden_nueva():
    return render_template(
        "compras/ordenes/form.html"
    )


@compras_bp.route("/ordenes/<int:orden_id>")
def orden_detalle(orden_id):
    return render_template(
        "compras/ordenes/detail.html",
        orden_id=orden_id
    )


# PROVEEDORES

@compras_bp.route("/proveedores")
def proveedores():
    return render_template(
        "compras/proveedores/index.html"
    )


@compras_bp.route("/proveedores/nuevo")
def proveedor_nuevo():
    return render_template(
        "compras/proveedores/form.html"
    )


# RECEPCIONES

@compras_bp.route("/recepciones")
def recepciones():
    return render_template(
        "compras/recepciones/index.html"
    )


@compras_bp.route("/recepciones/nueva")
def recepcion_nueva():
    return render_template(
        "compras/recepciones/form.html"
    )