from datetime import datetime
from decimal import Decimal

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort

from modulos import (
    produccion,
    orden_produccion,
    sostenibilidad,
    carbono
)
from routes.planta import _calcular_oee


sostenibilidad_bp = Blueprint(
    "sostenibilidad",
    __name__,
    url_prefix="/sostenibilidad"
)


# Valores (ajustarlos a los que se usen en la BD)
CATEGORIAS = {
    "electricidad": "Electricidad (kg CO2e/kWh)",
    "transporte": "Transporte de carga (kg CO2e/tonelada-km)"
}
LITROS_POR_UNIDAD = 0.26      # contenido de una botella de champu


# ---------- AYUDAS INTERNAS ----------

def _decimal(texto, permitir_cero=False):
    # Texto -> Decimal positivo (o con cero); si es invalido devuelve None
    try:
        valor = Decimal((texto or "").strip().replace(",", "."))
        if not valor.is_finite() or valor < 0 or (valor == 0 and not permitir_cero):
            return None
    except ArithmeticError:
        return None
    return valor


def _numero(valor):
    return float(valor) if valor is not None else None


def _huella(registro):
    # Huella de carbono de una ejecucion y del lote que produjo
    calculo, _, ejecuciones = _calcular_oee(registro)
    orden = orden_produccion.obtener_un_orden_produccion(registro.ordenp_id)

    potencias = {c.id_centro: _numero(c.potencia_kw) for c in sostenibilidad.obtener_centros()}
    marcha = {f["codigo"]: f["marcha"] for f in calculo["filas"]}

    ops = [
        {
            "codigo": e.ruta_codigo,
            "centro": e.centro_nombre,
            "potencia": potencias.get(e.centro_id),
            "marcha": marcha.get(e.ruta_codigo, 0.0)
        }
        for e in ejecuciones
    ]

    factor_e = sostenibilidad.obtener_factor_activo("electricidad")
    factor_t = sostenibilidad.obtener_factor_activo("transporte")

    despachos = []
    if orden is not None and orden.lote_id:
        despachos = [
            {
                "codigo": d.codigo,
                "vehiculo": d.vehiculo,
                "unidades": _numero(d.unidades),
                "peso_kg": _numero(d.peso_kg),
                "distancia_km": _numero(d.distancia_km),
                "factor": _numero(d.factor_valor)
            }
            for d in sostenibilidad.obtener_despachos_por_lote(orden.lote_id)
        ]

    resultado = carbono.calcular(
        ops,
        _numero(factor_e.valor) if factor_e is not None else None,
        despachos,
        _numero(factor_t.valor) if factor_t is not None else None,
        registro.cantidad_aceptada if registro.fecha_fin else None,
        LITROS_POR_UNIDAD
    )

    return resultado, orden, factor_e, factor_t


# HUELLA DE CARBONO POR EJECUCION

@sostenibilidad_bp.route("/")
def resumen():
    filas = []

    for e in produccion.obtener_produccion_con_operador():
        resultado, _, _, _ = _huella(e)
        filas.append({"ejecucion": e, "huella": resultado})

    return render_template(
        "sostenibilidad/resumen.html",
        filas=filas,
        litros_por_unidad=LITROS_POR_UNIDAD
    )


@sostenibilidad_bp.route("/<int:produccion_id>")
def detalle(produccion_id):
    registro = produccion.obtener_un_produccion(produccion_id)
    if registro is None:
        abort(404)

    resultado, orden, factor_e, factor_t = _huella(registro)

    grafico = {
        "etiquetas": ["Producción (electricidad)", "Distribución (transporte)"],
        "valores": [
            round(resultado["kg_produccion"], 4) if resultado["kg_produccion"] is not None else 0,
            round(resultado["kg_transporte"], 4)
        ]
    }

    return render_template(
        "sostenibilidad/detalle.html",
        produccion=registro,
        orden=orden,
        h=resultado,
        factor_e=factor_e,
        factor_t=factor_t,
        litros_por_unidad=LITROS_POR_UNIDAD,
        grafico=grafico
    )


# PARAMETROS (factores, potencia, peso y transporte)

@sostenibilidad_bp.route("/parametros")
def parametros():
    return render_template(
        "sostenibilidad/parametros.html",
        categorias=CATEGORIAS,
        factores=sostenibilidad.obtener_factores(),
        factores_transporte=sostenibilidad.obtener_factores("transporte"),
        centros=sostenibilidad.obtener_centros(solo_activos=True),
        productos=sostenibilidad.obtener_productos_terminados(),
        despachos=sostenibilidad.obtener_despachos_para_transporte()
    )


@sostenibilidad_bp.route("/parametros/factor", methods=["POST"])
def factor_nuevo():
    # Form: categoria, concepto, unidad, valor, fuente, anio
    categoria = request.form.get("categoria")
    concepto = (request.form.get("concepto") or "").strip()
    unidad = (request.form.get("unidad") or "").strip()
    fuente = (request.form.get("fuente") or "").strip()
    valor = _decimal(request.form.get("valor"), permitir_cero=True)
    anio = request.form.get("anio", type=int)

    if categoria not in CATEGORIAS:
        flash("Elija la categoría del factor", "error")
    elif not (concepto and unidad and fuente):
        flash("Complete concepto, unidad y fuente: todo factor debe citar su fuente", "error")
    elif valor is None:
        flash("El valor del factor debe ser un número mayor o igual a 0", "error")
    elif anio is None or anio < 1990 or anio > 2100:
        flash("Indique el año del factor", "error")
    else:
        sostenibilidad.insertar_factor(categoria, concepto, unidad, valor, fuente, anio, datetime.now())
        flash("Factor registrado. Se usará el más reciente de cada categoría", "exito")

    return redirect(url_for("sostenibilidad.parametros"))


@sostenibilidad_bp.route("/parametros/centros/<int:centro_id>/potencia", methods=["POST"])
def centro_potencia(centro_id):
    # Form: potencia_kw (potencia promedio del equipo)
    potencia = _decimal(request.form.get("potencia_kw"), permitir_cero=True)

    if potencia is None:
        flash("La potencia debe ser un número mayor o igual a 0 (kW)", "error")
    else:
        sostenibilidad.actualizar_potencia(centro_id, potencia, datetime.now())
        flash("Potencia actualizada", "exito")

    return redirect(url_for("sostenibilidad.parametros"))


@sostenibilidad_bp.route("/parametros/productos/<int:producto_id>/peso", methods=["POST"])
def producto_peso(producto_id):
    # Form: peso_kg (peso de una unidad ya envasada)
    peso = _decimal(request.form.get("peso_kg"))

    if peso is None:
        flash("El peso debe ser un número mayor a 0 (kg)", "error")
    else:
        sostenibilidad.actualizar_peso(producto_id, peso, datetime.now())
        flash("Peso actualizado", "exito")

    return redirect(url_for("sostenibilidad.parametros"))


@sostenibilidad_bp.route("/parametros/despachos/<int:despacho_id>/transporte", methods=["POST"])
def despacho_transporte(despacho_id):
    # Form: distancia_km, vehiculo, factor_id
    distancia = _decimal(request.form.get("distancia_km"))
    vehiculo = (request.form.get("vehiculo") or "").strip() or None
    factor_id = request.form.get("factor_id", type=int)

    if distancia is None:
        flash("La distancia debe ser un número mayor a 0 (km)", "error")
    else:
        sostenibilidad.actualizar_transporte(despacho_id, distancia, vehiculo, factor_id, datetime.now())
        flash("Transporte del despacho actualizado", "exito")

    return redirect(url_for("sostenibilidad.parametros"))