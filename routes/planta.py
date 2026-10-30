from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, session, jsonify

from modulos import (
    produccion,
    orden_produccion,
    ruta_operacion,
    control_calidad,
    ejecucion_operacion,
    lectura_sensor,
    parametro_proceso,
    alerta_proceso,
    parada,
    oee,
    spc,
    sensor_sim
)


planta_bp = Blueprint(
    "planta",
    __name__,
    url_prefix="/planta"
)


# Valores (ajustarlos a los que se usen en la BD)
ACTIVO = "activo"
EN_CURSO = "en_curso"
TERMINADA = "terminada"
VARIABLE = "temperatura"          # variable que mide el sensor simulado
UNIDAD = "°C"
OPERACION_CALIDAD = "OP-040"      # las operaciones posteriores exigen un lote liberado
OPERACIONES_ESPERA = frozenset({"OP-030"})   # reposo: no admite paradas y queda fuera del OEE
DURACION_DEMO_MIN = 1.0           # duracion real sugerida para cada operacion en la demostracion

TIPOS_PARADA = {
    "falla_equipo": "Falla de equipo",
    "falta_material": "Falta de material",
    "ajuste": "Ajuste o cambio",
    "limpieza": "Limpieza",
    "espera_calidad": "Espera de calidad",
    "otro": "Otro"
}


# ---------- AYUDAS INTERNAS ----------

def _intervalos(paradas):
    return [(p.fecha_inicio, p.fecha_fin) for p in paradas]


def _minutos_simulados(ejecucion, paradas):
    # Avance de la operacion en minutos simulados: tiempo real x factor de aceleracion,
    # sin contar el tiempo que la linea estuvo detenida
    return oee.minutos_efectivos(
        ejecucion.fecha_inicio,
        ejecucion.fecha_fin,
        float(ejecucion.factor_aceleracion),
        _intervalos(paradas),
        datetime.now()
    )


def _produccion_o_404(produccion_id):
    registro = produccion.obtener_un_produccion(produccion_id)
    if registro is None:
        abort(404)
    return registro


def _ejecucion_o_404(ejecucion_op_id):
    ejecucion = ejecucion_operacion.obtener_una_ejecucion(ejecucion_op_id)
    if ejecucion is None:
        abort(404)
    return ejecucion


def _rutas_activas(ordenp_id):
    rutas = ruta_operacion.obtener_rutas_operacion_por_ordenp(ordenp_id)
    return sorted([r for r in rutas if r.estado == ACTIVO], key=lambda r: r.secuencia)


def _lote_liberado(ordenp_id):
    control = control_calidad.obtener_ultimo_control_por_orden(ordenp_id)
    return control is not None and control.disposicion == "liberacion"


def _parada_abierta(paradas):
    return next((p for p in paradas if p.fecha_fin is None), None)


def _calcular_oee(registro):
    # OEE de una ejecucion (produccion); registro necesita id_produccion, ordenp_id,
    # fecha_fin, cantidad_aceptada y cantidad_rechazada
    ejecuciones = ejecucion_operacion.obtener_ejecuciones_por_produccion(registro.id_produccion)
    paradas = parada.obtener_paradas_por_orden(registro.ordenp_id)

    operaciones = [
        {
            "codigo": e.ruta_codigo,
            "secuencia": e.secuencia,
            "centro": e.centro_nombre,
            "inicio": e.fecha_inicio,
            "fin": e.fecha_fin,
            "factor": float(e.factor_aceleracion),
            "estandar": float(e.tiempo_estandar_min),
            "estado": e.estado
        }
        for e in ejecuciones
    ]

    lista_paradas = [
        {
            "inicio": p.fecha_inicio,
            "fin": p.fecha_fin,
            "tipo": p.tipo,
            "motivo": p.motivo,
            "centro": p.centro_nombre
        }
        for p in paradas
    ]

    terminada = registro.fecha_fin is not None

    calculo = oee.calcular(
        operaciones,
        lista_paradas,
        registro.cantidad_aceptada if terminada else None,
        registro.cantidad_rechazada if terminada else None,
        datetime.now(),
        OPERACIONES_ESPERA
    )

    return calculo, paradas, ejecuciones


# OPERACIONES DE UNA EJECUCION

@planta_bp.route("/ejecucion/<int:produccion_id>")
def operaciones(produccion_id):
    registro = _produccion_o_404(produccion_id)
    orden = orden_produccion.obtener_un_orden_produccion(registro.ordenp_id)

    rutas = _rutas_activas(registro.ordenp_id)
    hechas = {e.ruta_id: e for e in ejecucion_operacion.obtener_ejecuciones_por_produccion(produccion_id)}
    hay_en_curso = any(e.estado == EN_CURSO for e in hechas.values())

    paradas = parada.obtener_paradas_por_orden(registro.ordenp_id)
    abierta = _parada_abierta(paradas)

    secuencia_calidad = next((r.secuencia for r in rutas if r.codigo == OPERACION_CALIDAD), None)
    liberado = _lote_liberado(registro.ordenp_id)

    filas = []
    anterior_terminada = True

    for r in rutas:
        e = hechas.get(r.id_ruta)
        estandar = float(r.tiempo_estandar)

        if e is None:
            estado = "pendiente"
            transcurrido = 0.0
        else:
            estado = e.estado
            transcurrido = _minutos_simulados(e, paradas)

        # Una operacion posterior al control de calidad exige un lote liberado
        bloqueada_calidad = (
            secuencia_calidad is not None
            and r.secuencia > secuencia_calidad
            and not liberado
        )

        puede_iniciar = (
            e is None
            and registro.fecha_fin is None
            and anterior_terminada
            and not hay_en_curso
            and not bloqueada_calidad
        )

        detenida = estado == EN_CURSO and abierta is not None

        puede_terminar = estado == EN_CURSO and transcurrido >= estandar and abierta is None
        puede_parar = estado == EN_CURSO and abierta is None and r.codigo not in OPERACIONES_ESPERA

        filas.append({
            "ruta": r,
            "ejecucion": e,
            "estado": estado,
            "estandar": estandar,
            "transcurrido": transcurrido,
            "progreso": min(100, transcurrido / estandar * 100) if estandar else 0,
            "restante": max(0.0, estandar - transcurrido),
            "puede_iniciar": puede_iniciar,
            "puede_terminar": puede_terminar,
            "puede_parar": puede_parar,
            "detenida": detenida,
            "bloqueada_calidad": bloqueada_calidad and e is None,
            "tiene_sensor": parametro_proceso.obtener_parametro(r.centro_id, VARIABLE) is not None,
            "factor_sugerido": max(1, round(estandar / DURACION_DEMO_MIN))
        })

        anterior_terminada = (e is not None and e.estado == TERMINADA)

    return render_template(
        "planta/operaciones.html",
        produccion=registro,
        orden=orden,
        filas=filas,
        hay_en_curso=hay_en_curso,
        abierta=abierta,
        tipos_parada=TIPOS_PARADA,
        escenarios=sensor_sim.ESCENARIOS
    )


@planta_bp.route("/ejecucion/<int:produccion_id>/operaciones/<int:ruta_id>/iniciar", methods=["POST"])
def operacion_iniciar(produccion_id, ruta_id):
    # Form: factor (aceleracion del tiempo) y escenario (solo se usa si el centro tiene sensor)
    registro = _produccion_o_404(produccion_id)
    ruta = ruta_operacion.obtener_un_ruta_operacion(ruta_id)

    factor = request.form.get("factor", type=float)
    escenario = request.form.get("escenario") or "normal"

    rutas = _rutas_activas(registro.ordenp_id)
    hechas = {e.ruta_id: e for e in ejecucion_operacion.obtener_ejecuciones_por_produccion(produccion_id)}

    anteriores = [r for r in rutas if ruta is not None and r.secuencia < ruta.secuencia]
    secuencia_calidad = next((r.secuencia for r in rutas if r.codigo == OPERACION_CALIDAD), None)

    if ruta is None or ruta.ordenp_id != registro.ordenp_id or ruta.estado != ACTIVO:
        flash("La operación no pertenece a esta orden", "error")
    elif registro.fecha_fin is not None:
        flash("Esta ejecución ya fue terminada", "error")
    elif ruta_id in hechas:
        flash("Esa operación ya se inició", "error")
    elif any(e.estado == EN_CURSO for e in hechas.values()):
        flash("Termine la operación en curso antes de iniciar otra", "error")
    elif any(r.id_ruta not in hechas or hechas[r.id_ruta].estado != TERMINADA for r in anteriores):
        flash("Primero deben terminarse las operaciones anteriores de la ruta", "error")
    elif secuencia_calidad is not None and ruta.secuencia > secuencia_calidad and not _lote_liberado(registro.ordenp_id):
        flash("El lote no tiene un control de calidad liberado: no puede continuar", "error")
    elif factor is None or factor < 1 or factor > 100000:
        flash("El factor de aceleración debe estar entre 1 y 100000", "error")
    elif escenario not in sensor_sim.ESCENARIOS:
        flash("Escenario del sensor no válido", "error")
    else:
        usuario_id = session.get("id_usuario")

        ejecucion_operacion.iniciar_operacion(
            produccion_id,
            ruta_id,
            str(usuario_id) if usuario_id else None,
            datetime.now(),
            ruta.tiempo_estandar,
            factor,
            escenario
        )
        flash("Operación iniciada", "exito")

    return redirect(url_for("planta.operaciones", produccion_id=produccion_id))


@planta_bp.route("/operacion/<int:ejecucion_op_id>/terminar", methods=["POST"])
def operacion_terminar(ejecucion_op_id):
    ejecucion = _ejecucion_o_404(ejecucion_op_id)
    paradas = parada.obtener_paradas_por_orden(ejecucion.ordenp_id)

    if ejecucion.estado != EN_CURSO:
        flash("Esa operación ya fue terminada", "error")
    elif _parada_abierta(paradas) is not None:
        flash("La línea está detenida: reanude el trabajo antes de terminar la operación", "error")
    elif _minutos_simulados(ejecucion, paradas) < float(ejecucion.tiempo_estandar_min):
        faltan = float(ejecucion.tiempo_estandar_min) - _minutos_simulados(ejecucion, paradas)
        flash("Aún no se cumple el tiempo estándar: faltan %.1f minutos simulados" % faltan, "error")
    else:
        ejecucion_operacion.terminar_operacion(ejecucion_op_id, datetime.now())
        flash("Operación terminada", "exito")

    return redirect(url_for("planta.operaciones", produccion_id=ejecucion.produccion_id))


# PARADAS DE LA LINEA

@planta_bp.route("/ejecucion/<int:produccion_id>/paradas", methods=["POST"])
def parada_iniciar(produccion_id):
    # Form: tipo y motivo. Detiene el reloj de la operacion en curso hasta que se reanude.
    registro = _produccion_o_404(produccion_id)

    en_curso = next(
        (e for e in ejecucion_operacion.obtener_ejecuciones_por_produccion(produccion_id) if e.estado == EN_CURSO),
        None
    )
    paradas = parada.obtener_paradas_por_orden(registro.ordenp_id)

    tipo = request.form.get("tipo")
    motivo = (request.form.get("motivo") or "").strip() or None

    if en_curso is None:
        flash("No hay una operación en curso que detener", "error")
    elif en_curso.ruta_codigo in OPERACIONES_ESPERA:
        flash("No se registran paradas durante el reposo: el producto está esperando, no la línea", "error")
    elif _parada_abierta(paradas) is not None:
        flash("Ya hay una parada abierta", "error")
    elif tipo not in TIPOS_PARADA:
        flash("Elija el tipo de parada", "error")
    elif tipo == "otro" and not motivo:
        flash("Describa el motivo de la parada", "error")
    else:
        usuario_id = session.get("id_usuario")

        parada.insertar_parada(
            registro.ordenp_id,
            en_curso.centro_id,
            str(usuario_id) if usuario_id else None,
            tipo,
            motivo,
            datetime.now()
        )
        flash("Parada registrada: el reloj de la operación está detenido", "exito")

    return redirect(url_for("planta.operaciones", produccion_id=produccion_id))


@planta_bp.route("/ejecucion/<int:produccion_id>/paradas/<int:parada_id>/reanudar", methods=["POST"])
def parada_reanudar(produccion_id, parada_id):
    registro = _produccion_o_404(produccion_id)
    abierta = parada.obtener_una_parada(parada_id)

    if abierta is None or abierta.ordenp_id != registro.ordenp_id:
        flash("Parada no encontrada", "error")
    elif abierta.fecha_fin is not None:
        flash("Esa parada ya fue cerrada", "error")
    else:
        parada.cerrar_parada(parada_id, datetime.now())
        flash("Trabajo reanudado", "exito")

    return redirect(url_for("planta.operaciones", produccion_id=produccion_id))


# SENSOR SIMULADO Y CARTA DE CONTROL (SPC)

@planta_bp.route("/operacion/<int:ejecucion_op_id>/spc")
def spc_operacion(ejecucion_op_id):
    ejecucion = _ejecucion_o_404(ejecucion_op_id)
    parametro = parametro_proceso.obtener_parametro(ejecucion.centro_id, VARIABLE)

    if parametro is None:
        flash("Este centro de trabajo no tiene un sensor configurado", "error")
        return redirect(url_for("planta.operaciones", produccion_id=ejecucion.produccion_id))

    return render_template(
        "planta/spc.html",
        ej=ejecucion,
        parametro=parametro,
        escenario=sensor_sim.ESCENARIOS.get(ejecucion.escenario, ejecucion.escenario)
    )


@planta_bp.route("/operacion/<int:ejecucion_op_id>/lecturas.json")
def lecturas_json(ejecucion_op_id):
    # Genera las lecturas que faltan hasta el minuto simulado actual, las guarda y devuelve
    # las lecturas con el analisis SPC. La pagina de SPC lo consulta cada pocos segundos.
    ejecucion = _ejecucion_o_404(ejecucion_op_id)
    parametro = parametro_proceso.obtener_parametro(ejecucion.centro_id, VARIABLE)

    if parametro is None:
        abort(404)

    paradas = parada.obtener_paradas_por_orden(ejecucion.ordenp_id)

    duracion = float(ejecucion.tiempo_estandar_min)
    factor = float(ejecucion.factor_aceleracion)
    objetivo = float(parametro.valor_objetivo)
    lsl = float(parametro.limite_inferior) if parametro.limite_inferior is not None else None
    usl = float(parametro.limite_superior) if parametro.limite_superior is not None else None

    if ejecucion.estado == TERMINADA:
        minuto_actual = duracion
    else:
        minuto_actual = min(duracion, _minutos_simulados(ejecucion, paradas))

    ultimo = lectura_sensor.obtener_ultimo_minuto(ejecucion_op_id)
    siguiente = 0 if ultimo is None else int(ultimo) + 1

    ahora = datetime.now()
    nuevas = []
    for m in range(siguiente, int(minuto_actual) + 1):
        # un sensor averiado puede dejar de enviar la lectura de algunos minutos
        if sensor_sim.lectura_perdida(m, ejecucion.escenario, ejecucion.id_ejecucion_op):
            continue

        valor = sensor_sim.temperatura(m, duracion, ejecucion.escenario, ejecucion.id_ejecucion_op, objetivo)
        nuevas.append({
            "variable": VARIABLE,
            "valor": round(valor, 2),
            "unidad": UNIDAD,
            "minuto_proceso": m,
            # hora real en que ocurrio ese minuto, descontando el tiempo de las paradas
            "fecha_hora": oee.hora_del_minuto(ejecucion.fecha_inicio, m, factor, _intervalos(paradas), ahora)
        })

    if nuevas:
        lectura_sensor.insertar_lecturas(ejecucion_op_id, nuevas)

    lecturas = [
        {"minuto": int(l.minuto_proceso), "valor": float(l.valor), "id": l.id_lectura, "fecha_hora": l.fecha_hora}
        for l in lectura_sensor.obtener_lecturas(ejecucion_op_id)
    ]

    analisis = spc.analizar(lecturas, duracion, lsl, usl)

    # Se guarda solo la primera alerta de cada regla en la operacion
    for v in analisis["violaciones"]:
        if v["id_lectura"] and not alerta_proceso.existe_alerta_en_operacion(ejecucion_op_id, v["regla"]):
            alerta_proceso.insertar_alerta(
                "spc", v["nivel"], ejecucion.ordenp_id, v["id_lectura"],
                v["regla"], v["mensaje"], v["valor"], None, datetime.now()
            )

    return jsonify({
        "estado": ejecucion.estado,
        "detenida": _parada_abierta(paradas) is not None and ejecucion.estado == EN_CURSO,
        "duracion": duracion,
        "minuto_actual": round(minuto_actual, 1),
        "inicio_estable": analisis["inicio_estable"],
        "objetivo": objetivo,
        "lsl": lsl,
        "usl": usl,
        "lecturas": [
            {"minuto": l["minuto"], "valor": l["valor"], "hora": l["fecha_hora"].strftime("%H:%M:%S")}
            for l in lecturas
        ],
        "suficiente": analisis["suficiente"],
        "limites_provisionales": analisis.get("limites_provisionales", False),
        "cl": analisis.get("cl"),
        "sigma": analisis.get("sigma"),
        "ucl": analisis.get("ucl"),
        "lcl": analisis.get("lcl"),
        "mas2": analisis.get("mas2"),
        "menos2": analisis.get("menos2"),
        "cp": analisis.get("cp"),
        "cpk": analisis.get("cpk"),
        "violaciones": [
            {"minuto": v["minuto"], "valor": v["valor"], "regla": v["regla"],
             "nivel": v["nivel"], "mensaje": v["mensaje"]}
            for v in analisis["violaciones"]
        ]
    })


# OEE

@planta_bp.route("/oee")
def oee_resumen():
    filas = []

    for e in produccion.obtener_produccion_con_operador():
        calculo, _, _ = _calcular_oee(e)
        filas.append({"ejecucion": e, "calculo": calculo})

    # Promedio de las ejecuciones que ya tienen OEE
    con_oee = [f["calculo"] for f in filas if f["calculo"]["oee"] is not None]

    def promedio(clave):
        return sum(c[clave] for c in con_oee) / len(con_oee) if con_oee else None

    return render_template(
        "planta/oee_resumen.html",
        filas=filas,
        promedios={
            "disponibilidad": promedio("disponibilidad"),
            "rendimiento": promedio("rendimiento"),
            "calidad": promedio("calidad"),
            "oee": promedio("oee"),
            "cantidad": len(con_oee)
        }
    )


@planta_bp.route("/oee/<int:produccion_id>")
def oee_detalle(produccion_id):
    registro = _produccion_o_404(produccion_id)
    orden = orden_produccion.obtener_un_orden_produccion(registro.ordenp_id)

    calculo, paradas, ejecuciones = _calcular_oee(registro)

    # Duracion de cada parada en minutos simulados: segundos reales x factor de la operacion
    # que estaba en marcha cuando empezo
    lista_paradas = []
    ahora = datetime.now()
    for p in paradas:
        factor = next(
            (float(e.factor_aceleracion) for e in ejecuciones
             if e.fecha_inicio <= p.fecha_inicio <= (e.fecha_fin or ahora)),
            1.0
        )
        segundos = ((p.fecha_fin or ahora) - p.fecha_inicio).total_seconds()
        lista_paradas.append({"parada": p, "minutos": segundos / 60 * factor})

    def porcentaje(valor):
        return round(valor * 100, 1) if valor is not None else None

    grafico = {
        "indicadores": {
            "etiquetas": ["Disponibilidad", "Rendimiento", "Calidad", "OEE"],
            "valores": [
                porcentaje(calculo["disponibilidad"]),
                porcentaje(calculo["rendimiento"]),
                porcentaje(calculo["calidad"]),
                porcentaje(calculo["oee"])
            ]
        },
        "pareto": {
            "etiquetas": [TIPOS_PARADA.get(t, t) for t, _ in calculo["pareto"]],
            "valores": [round(m, 1) for _, m in calculo["pareto"]]
        }
    }

    return render_template(
        "planta/oee.html",
        produccion=registro,
        orden=orden,
        c=calculo,
        paradas=lista_paradas,
        tipos_parada=TIPOS_PARADA,
        grafico=grafico
    )