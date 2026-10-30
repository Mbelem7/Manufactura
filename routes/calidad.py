from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, session

from modulos import (
    control_calidad,
    orden_produccion
)


calidad_bp = Blueprint(
    "calidad",
    __name__,
    url_prefix="/calidad"
)


# Valores (ajustarlos a los que se usen en la BD)
ACTIVO = "activo"
OP_EN_PROCESO = "en_proceso"
CONFORME = "conforme"
NO_CONFORME = "no_conforme"
LIBERACION = "liberacion"
RETRABAJO = "retrabajo"
SCRAP = "scrap"
DISPOSICIONES = (LIBERACION, RETRABAJO, SCRAP)


def _texto(nombre):
    # Texto del formulario; vacio -> None
    valor = (request.form.get(nombre) or "").strip()
    return valor or None


def _control_o_404(control_id):
    control = control_calidad.obtener_un_control(control_id)
    if control is None:
        abort(404)
    return control


# CONTROLES DE CALIDAD

@calidad_bp.route("/")
def controles():
    resultado = request.args.get("resultado")
    lista = control_calidad.obtener_controles()

    if resultado:
        lista = [c for c in lista if c.resultado == resultado]

    return render_template(
        "calidad/index.html",
        controles=lista,
        resultado=resultado
    )


@calidad_bp.route("/nuevo", methods=["GET", "POST"])
def control_nuevo():
    # Form: ordenp_id, apariencia, homogeneidad ("conforme" o "no_conforme"), observaciones
    if request.method == "POST":
        ordenp_id = request.form.get("ordenp_id", type=int)
        apariencia = request.form.get("apariencia")
        homogeneidad = request.form.get("homogeneidad")
        observaciones = _texto("observaciones")

        orden = orden_produccion.obtener_un_orden_produccion(ordenp_id) if ordenp_id else None

        if orden is None or orden.estado != OP_EN_PROCESO:
            flash("Debe elegir una orden de producción en proceso", "error")
        elif apariencia not in (CONFORME, NO_CONFORME) or homogeneidad not in (CONFORME, NO_CONFORME):
            flash("Indique el resultado de la apariencia y de la homogeneidad", "error")
        else:
            apariencia_ok = apariencia == CONFORME
            homogeneidad_ok = homogeneidad == CONFORME
            conforme = apariencia_ok and homogeneidad_ok

            if not conforme and not observaciones:
                flash("Describa en las observaciones por qué el lote no es conforme", "error")
            else:
                usuario_id = session.get("id_usuario")

                control_id = control_calidad.insertar_control(
                    ordenp_id,
                    orden.lote_id,
                    str(usuario_id) if usuario_id else None,
                    apariencia_ok,
                    homogeneidad_ok,
                    CONFORME if conforme else NO_CONFORME,
                    observaciones,
                    # un lote conforme se libera; uno no conforme espera su disposicion
                    LIBERACION if conforme else None,
                    ACTIVO,
                    datetime.now()
                )

                if conforme:
                    flash("Control registrado: el lote es conforme y quedó liberado", "exito")
                else:
                    flash("Control registrado: el lote es no conforme. Falta decidir su disposición", "exito")

                return redirect(url_for("calidad.control_detalle", control_id=control_id))

        return redirect(url_for("calidad.control_nuevo", orden_id=ordenp_id))

    return render_template(
        "calidad/form.html",
        orden_id=request.args.get("orden_id", type=int),
        ordenes=orden_produccion.obtener_ordenes_produccion_por_estado(OP_EN_PROCESO)
    )


@calidad_bp.route("/<int:control_id>")
def control_detalle(control_id):
    control = _control_o_404(control_id)

    return render_template(
        "calidad/detail.html",
        control=control,
        historial=control_calidad.obtener_controles_por_orden(control.ordenp_id),
        # solo un lote no conforme sin decidir admite elegir su disposicion
        pendiente=(control.resultado == NO_CONFORME and control.disposicion is None and control.estado == ACTIVO)
    )


@calidad_bp.route("/<int:control_id>/disposicion", methods=["POST"])
def control_disposicion(control_id):
    # Form: disposicion ("liberacion", "retrabajo" o "scrap") y motivo
    control = _control_o_404(control_id)

    disposicion = request.form.get("disposicion")
    motivo = _texto("motivo")

    if control.resultado != NO_CONFORME or control.disposicion is not None:
        flash("Este control no está pendiente de disposición", "error")
    elif disposicion not in DISPOSICIONES:
        flash("Elija la disposición del lote: liberación, retrabajo o scrap", "error")
    elif not motivo:
        flash("Escriba el motivo de la decisión", "error")
    else:
        control_calidad.registrar_disposicion(control_id, disposicion, motivo, datetime.now())

        if disposicion == LIBERACION:
            flash("Lote liberado con concesión. Ya se puede terminar la ejecución", "exito")
        elif disposicion == RETRABAJO:
            flash("Lote enviado a retrabajo. Registre un nuevo control de calidad cuando termine", "exito")
        else:
            flash("Lote descartado (scrap). La ejecución solo podrá terminarse con 0 unidades aceptadas", "exito")

    return redirect(url_for("calidad.control_detalle", control_id=control_id))