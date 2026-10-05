from flask import Blueprint, render_template


ventas_bp = Blueprint(
    "ventas",
    __name__,
    url_prefix="/ventas"
)


# ÓRDENES DE VENTA

@ventas_bp.route("/ordenes")
def ordenes():
    return render_template(
        "ventas/ordenes/index.html"
    )


@ventas_bp.route("/ordenes/nueva")
def orden_nueva():
    return render_template(
        "ventas/ordenes/form.html"
    )


@ventas_bp.route("/ordenes/<int:orden_id>")
def orden_detalle(orden_id):
    return render_template(
        "ventas/ordenes/detail.html",
        orden_id=orden_id
    )


# CLIENTES

@ventas_bp.route("/clientes")
def clientes():
    return render_template(
        "ventas/clientes/index.html"
    )


@ventas_bp.route("/clientes/nuevo")
def cliente_nuevo():
    return render_template(
        "ventas/clientes/form.html"
    )


# DESPACHOS

@ventas_bp.route("/despachos")
def despachos():
    return render_template(
        "ventas/despachos/index.html"
    )


@ventas_bp.route("/despachos/nuevo")
def despacho_nuevo():
    return render_template(
        "ventas/despachos/form.html"
    )