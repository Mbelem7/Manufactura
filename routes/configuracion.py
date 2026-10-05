from flask import Blueprint, render_template


configuracion_bp = Blueprint(
    "configuracion",
    __name__,
    url_prefix="/configuracion"
)


# USUARIOS

@configuracion_bp.route("/usuarios")
def usuarios():
    return render_template(
        "configuracion/usuarios/index.html"
    )


@configuracion_bp.route("/usuarios/nuevo")
def usuario_nuevo():
    return render_template(
        "configuracion/usuarios/form.html"
    )