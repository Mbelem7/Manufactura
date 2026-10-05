from flask import Blueprint, render_template


produccion_bp = Blueprint(
    "produccion",
    __name__,
    url_prefix="/produccion"
)


# BOM

@produccion_bp.route("/bom")
def bom():
    return render_template("produccion/bom/index.html")


@produccion_bp.route("/bom/nuevo")
def bom_nuevo():
    return render_template("produccion/bom/form.html")


@produccion_bp.route("/bom/<int:bom_id>")
def bom_detalle(bom_id):
    return render_template(
        "produccion/bom/detail.html",
        bom_id=bom_id
    )


# CENTROS DE TRABAJO

@produccion_bp.route("/centros-trabajo")
def centros_trabajo():
    return render_template(
        "produccion/centros_trabajo/index.html"
    )


@produccion_bp.route("/centros-trabajo/nuevo")
def centro_trabajo_nuevo():
    return render_template(
        "produccion/centros_trabajo/form.html"
    )


# RUTAS DE OPERACIÓN

@produccion_bp.route("/rutas")
def rutas():
    return render_template(
        "produccion/rutas/index.html"
    )


@produccion_bp.route("/rutas/nueva")
def ruta_nueva():
    return render_template(
        "produccion/rutas/form.html"
    )


# ÓRDENES DE PRODUCCIÓN

@produccion_bp.route("/ordenes")
def ordenes():
    return render_template(
        "produccion/ordenes/index.html"
    )


@produccion_bp.route("/ordenes/nueva")
def orden_nueva():
    return render_template(
        "produccion/ordenes/form.html"
    )


@produccion_bp.route("/ordenes/<int:orden_id>")
def orden_detalle(orden_id):
    return render_template(
        "produccion/ordenes/detail.html",
        orden_id=orden_id
    )


# EJECUCIONES

@produccion_bp.route("/ejecuciones")
def ejecuciones():
    return render_template(
        "produccion/ejecuciones/index.html"
    )


@produccion_bp.route("/ejecuciones/nueva")
def ejecucion_nueva():
    return render_template(
        "produccion/ejecuciones/form.html"
    )