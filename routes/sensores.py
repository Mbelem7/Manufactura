import json
from datetime import datetime, date

from flask import Blueprint, render_template, redirect, url_for, flash, abort, jsonify, request

from modulos import (
    ejecucion_operacion,
    lectura_sensor,
    parada,
    alerta_proceso,
    sensor,
    diagnostico
)
from modulos.arbol_sensor import ARBOL, METRICAS
from routes.planta import _minutos_simulados


sensores_bp = Blueprint(
    "sensores",
    __name__,
    url_prefix="/sensores"
)


# Valores (ajustarlos a los que se usen en la BD)
TERMINADA = "terminada"
CALIBRACION_VIGENTE_DIAS = METRICAS["supuestos"]["calibracion_vigente_dias"]
DIAS_SIN_REGISTRO = 365        # si el sensor no tiene fecha de calibracion se trata como vencido

ETIQUETAS = {
    "normal": "Normal",
    "calibrar": "Calibrar",
    "mantenimiento": "Mantenimiento"
}

RECOMENDACIONES = {
    "normal": "El sensor funciona con normalidad. Si hay alertas de proceso, el problema está en el proceso y no en el sensor.",
    "calibrar": "Programe una calibración del sensor antes de la siguiente producción.",
    "mantenimiento": "Revise, repare o reemplace el sensor antes de usarlo: sus lecturas no son confiables."
}


# ---------- AYUDAS INTERNAS ----------

def _dias_calibracion(sensor_fila):
    if sensor_fila.fecha_ultima_calibracion is None:
        return DIAS_SIN_REGISTRO
    return (date.today() - sensor_fila.fecha_ultima_calibracion).days


def _tabla_caracteristicas(valores):
    # Caracteristicas listas para mostrar: nombre, valor y unidad
    filas = []

    for clave, nombre, unidad in diagnostico.CARACTERISTICAS:
        valor = valores.get(clave)
        if valor is None:
            continue

        filas.append({"nombre": nombre, "texto": diagnostico.texto_valor(clave, valor)})

    return filas


# SENSORES

@sensores_bp.route("/")
def index():
    sensores = sensor.obtener_sensores()

    return render_template(
        "sensores/index.html",
        filas=[{"sensor": s, "dias": _dias_calibracion(s)} for s in sensores],
        vigente=CALIBRACION_VIGENTE_DIAS,
        etiquetas=ETIQUETAS,
        metricas=METRICAS
    )


@sensores_bp.route("/<int:sensor_id>")
def detalle(sensor_id):
    sensor_fila = sensor.obtener_un_sensor(sensor_id)
    if sensor_fila is None:
        abort(404)

    historial = []
    for d in sensor.obtener_diagnosticos_por_sensor(sensor_id):
        valores = d.caracteristicas if isinstance(d.caracteristicas, dict) else json.loads(d.caracteristicas)
        historial.append({"diagnostico": d, "caracteristicas": _tabla_caracteristicas(valores)})

    return render_template(
        "sensores/detalle.html",
        sensor=sensor_fila,
        dias=_dias_calibracion(sensor_fila),
        vigente=CALIBRACION_VIGENTE_DIAS,
        historial=historial,
        etiquetas=ETIQUETAS,
        hoy=date.today().isoformat()
    )


@sensores_bp.route("/<int:sensor_id>/calibrar", methods=["POST"])
def calibrar(sensor_id):
    # Form: fecha (AAAA-MM-DD). Registra cuando se calibro el sensor por ultima vez.
    sensor_fila = sensor.obtener_un_sensor(sensor_id)
    if sensor_fila is None:
        abort(404)

    try:
        fecha = datetime.strptime(request.form.get("fecha", ""), "%Y-%m-%d").date()
    except ValueError:
        fecha = None

    if fecha is None:
        flash("Indique la fecha de calibración", "error")
    elif fecha > date.today():
        flash("La fecha de calibración no puede estar en el futuro", "error")
    else:
        sensor.actualizar_calibracion(sensor_id, fecha, datetime.now())
        flash("Calibración registrada", "exito")

    return redirect(url_for("sensores.detalle", sensor_id=sensor_id))


# MODELO

@sensores_bp.route("/modelo")
def modelo():
    return render_template(
        "sensores/modelo.html",
        arbol=ARBOL,
        metricas=METRICAS,
        reglas=diagnostico.reglas(ARBOL),
        nombres=diagnostico.NOMBRES,
        valor_texto=diagnostico.texto_valor,
        etiquetas=ETIQUETAS,
        caracteristicas=diagnostico.CARACTERISTICAS
    )


# DIAGNOSTICO DE UNA OPERACION

@sensores_bp.route("/operacion/<int:ejecucion_op_id>/diagnostico.json")
def diagnostico_json(ejecucion_op_id):
    # Diagnostica el sensor con las lecturas de la operacion. Al terminar la operacion guarda
    # el diagnostico y, si el sensor no esta normal, crea una alerta predictiva.
    ejecucion = ejecucion_operacion.obtener_una_ejecucion(ejecucion_op_id)
    if ejecucion is None:
        abort(404)

    sensor_fila = sensor.obtener_sensor_por_centro(ejecucion.centro_id)
    if sensor_fila is None:
        return jsonify({"sin_sensor": True})

    duracion = float(ejecucion.tiempo_estandar_min)

    if ejecucion.estado == TERMINADA:
        minuto_actual = duracion
    else:
        paradas = parada.obtener_paradas_por_orden(ejecucion.ordenp_id)
        minuto_actual = min(duracion, _minutos_simulados(ejecucion, paradas))

    lecturas = [
        {"minuto": int(l.minuto_proceso), "valor": float(l.valor)}
        for l in lectura_sensor.obtener_lecturas(ejecucion_op_id)
    ]

    dias = _dias_calibracion(sensor_fila)
    valores = diagnostico.caracteristicas(lecturas, duracion, minuto_actual, dias)

    respuesta = {
        "sin_sensor": False,
        "sensor": "%s — %s" % (sensor_fila.codigo, sensor_fila.nombre),
        "id_sensor": sensor_fila.id_sensor,
        "dias_calibracion": dias,
        "suficiente": valores is not None
    }

    if valores is None:
        return jsonify(respuesta)

    clase, probabilidad, camino = diagnostico.recorrer(ARBOL, valores)

    guardado = sensor.obtener_diagnostico_por_operacion(ejecucion_op_id) is not None

    # Solo se guarda el diagnostico final, cuando la operacion termino
    if ejecucion.estado == TERMINADA and not guardado:
        sensor.insertar_diagnostico(
            sensor_fila.id_sensor,
            ejecucion_op_id,
            json.dumps(valores),
            clase,
            " → ".join(camino),
            probabilidad
        )
        guardado = True

        if clase != "normal":
            alerta_proceso.insertar_alerta(
                "predictiva",
                "critica" if clase == "mantenimiento" else "advertencia",
                ejecucion.ordenp_id,
                None,
                "arbol_sensor_" + clase,
                "El árbol de decisión recomienda %s para el sensor %s (probabilidad %.0f %%)."
                % (clase, sensor_fila.codigo, (probabilidad or 0) * 100),
                None,
                probabilidad,
                datetime.now()
            )

    respuesta.update({
        "diagnostico": clase,
        "etiqueta": ETIQUETAS[clase],
        "recomendacion": RECOMENDACIONES[clase],
        "probabilidad": probabilidad,
        "caracteristicas": _tabla_caracteristicas(valores),
        "camino": camino,
        "guardado": guardado
    })

    return jsonify(respuesta)