from flask import Blueprint, render_template


inventario_bp = Blueprint(
    "inventario",
    __name__,
    url_prefix="/inventario"
)


# PRODUCTOS

@inventario_bp.route("/productos")
def productos():
    return render_template("inventario/productos/index.html")


@inventario_bp.route("/productos/nuevo")
def producto_nuevo():
    return render_template("inventario/productos/form.html")


# ALMACENES

@inventario_bp.route("/almacenes")
def almacenes():
    return render_template("inventario/almacenes/index.html")


@inventario_bp.route("/almacenes/nuevo")
def almacen_nuevo():
    return render_template("inventario/almacenes/form.html")


# LOTES

@inventario_bp.route("/lotes")
def lotes():
    return render_template("inventario/lotes/index.html")


@inventario_bp.route("/lotes/nuevo")
def lote_nuevo():
    return render_template("inventario/lotes/form.html")


# EXISTENCIAS

@inventario_bp.route("/existencias")
def existencias():
    return render_template("inventario/existencias/index.html")