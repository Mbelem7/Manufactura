from datetime import timedelta

# Calculo del OEE (disponibilidad x rendimiento x calidad) de una ejecucion y utilidades de
# tiempo. No usa base de datos: recibe operaciones y paradas ya cargadas.
#
# Reglas del modelo:
# - Una parada DETIENE el reloj de la operacion: el tiempo detenido no cuenta como avance.
# - Las operaciones de espera (por ejemplo el reposo de 24 h) no entran en el OEE: el producto
#   esta reposando, la linea no esta parada.
# - Los tiempos se expresan en minutos simulados (tiempo real x factor de aceleracion).


def segundos_superpuestos(ini_a, fin_a, ini_b, fin_b, ahora):
    # Segundos que se solapan dos intervalos; un fin vacio significa "hasta ahora"
    fin_a = fin_a or ahora
    fin_b = fin_b or ahora
    inicio = max(ini_a, ini_b)
    fin = min(fin_a, fin_b)
    return max(0.0, (fin - inicio).total_seconds())


def minutos_efectivos(inicio, fin, factor, paradas, ahora):
    # Minutos simulados de avance de una operacion, sin contar el tiempo detenido
    # paradas: lista de (fecha_inicio, fecha_fin)
    bruto = ((fin or ahora) - inicio).total_seconds()
    detenido = sum(segundos_superpuestos(inicio, fin, p_ini, p_fin, ahora) for p_ini, p_fin in paradas)
    return max(0.0, bruto - detenido) / 60 * factor


def hora_del_minuto(inicio, minuto, factor, paradas, ahora):
    # Hora real en que la operacion alcanzo un minuto simulado de avance (descontando paradas)
    restante = minuto / factor * 60
    cursor = inicio

    for p_ini, p_fin in sorted(paradas, key=lambda p: p[0]):
        p_fin = p_fin or ahora

        if p_fin <= cursor:
            continue

        if p_ini > cursor:
            tramo = (p_ini - cursor).total_seconds()
            if restante <= tramo:
                return cursor + timedelta(seconds=restante)
            restante -= tramo

        cursor = max(cursor, p_fin)

    return cursor + timedelta(seconds=restante)


def calcular(operaciones, paradas, aceptadas, rechazadas, ahora, espera=()):
    # operaciones: lista de dicts {codigo, secuencia, centro, inicio, fin, factor, estandar, estado, espera}
    # paradas: lista de dicts {inicio, fin, tipo, motivo, centro}
    # aceptadas / rechazadas: None mientras la ejecucion no termine
    # espera: codigos de las operaciones de espera, que quedan fuera del OEE
    filas = []
    pareto = {}
    espera_min = 0.0

    for op in sorted(operaciones, key=lambda o: o["secuencia"]):
        factor = op["factor"]
        bruto = ((op["fin"] or ahora) - op["inicio"]).total_seconds() / 60 * factor
        # Cada operacion declara si es de espera; por compatibilidad tambien se admite una lista de codigos
        es_espera = op.get("espera", op["codigo"] in espera)

        detenido = 0.0
        if not es_espera:
            for p in paradas:
                seg = segundos_superpuestos(op["inicio"], op["fin"], p["inicio"], p["fin"], ahora)
                if seg > 0:
                    minutos = seg / 60 * factor
                    detenido += minutos
                    pareto[p["tipo"]] = pareto.get(p["tipo"], 0.0) + minutos

        if es_espera:
            espera_min += bruto

        filas.append({
            "codigo": op["codigo"],
            "centro": op["centro"],
            "estado": op["estado"],
            "espera": es_espera,
            "estandar": op["estandar"],
            "bruto": bruto,
            "detenido": detenido,
            "marcha": bruto - detenido
        })

    # El OEE se calcula solo con las operaciones de trabajo ya terminadas
    hechas = [f for f in filas if not f["espera"] and f["estado"] == "terminada"]

    t_bruto = sum(f["bruto"] for f in hechas)
    t_paradas = sum(f["detenido"] for f in hechas)
    t_marcha = sum(f["marcha"] for f in hechas)
    t_estandar = sum(f["estandar"] for f in hechas)

    disponibilidad = (t_marcha / t_bruto) if t_bruto > 0 else None
    rendimiento = min(1.0, t_estandar / t_marcha) if t_marcha > 0 else None

    calidad = None
    if aceptadas is not None and rechazadas is not None and (aceptadas + rechazadas) > 0:
        calidad = aceptadas / (aceptadas + rechazadas)

    oee = None
    if disponibilidad is not None and rendimiento is not None and calidad is not None:
        oee = disponibilidad * rendimiento * calidad

    return {
        "filas": filas,
        "hay_datos": len(hechas) > 0,
        "t_bruto": t_bruto,
        "t_paradas": t_paradas,
        "t_marcha": t_marcha,
        "t_estandar": t_estandar,
        "espera_min": espera_min,
        "disponibilidad": disponibilidad,
        "rendimiento": rendimiento,
        "calidad": calidad,
        "oee": oee,
        "aceptadas": aceptadas,
        "rechazadas": rechazadas,
        "pareto": sorted(pareto.items(), key=lambda x: x[1], reverse=True)
    }