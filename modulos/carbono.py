# Calculo de la energia, la intensidad energetica y la huella de carbono de un lote.
# No usa base de datos: recibe los datos ya cargados.
#
# Formulas:
#   Energia (kWh)                  = potencia del equipo (kW) x tiempo en marcha (h)
#   Emisiones de produccion (kg)   = energia (kWh) x factor de emision electrico (kg CO2e/kWh)
#   Emisiones de transporte (kg)   = peso (t) x distancia (km) x factor de transporte (kg CO2e/t-km)
#   Huella por botella (kg CO2e)   = (produccion + transporte) / unidades aceptadas
#   Intensidad energetica          = energia (kWh) / unidades aceptadas


def calcular(ops, factor_electrico, despachos, factor_transporte_defecto, unidades, litros_por_unidad):
    # ops: lista de dicts {codigo, centro, potencia (kW o None), marcha (minutos simulados)}
    # factor_electrico: kg CO2e/kWh o None
    # despachos: lista de dicts {codigo, unidades, peso_kg, distancia_km, factor (o None), vehiculo}
    # factor_transporte_defecto: se usa cuando el despacho no tiene factor propio
    # unidades: unidades aceptadas (None mientras la ejecucion no termine)

    # ---- Energia y produccion ----
    filas = []
    kwh_total = 0.0
    sin_potencia = []

    for op in ops:
        horas = op["marcha"] / 60
        potencia = op["potencia"]

        if potencia is None:
            kwh = None
            sin_potencia.append(op["centro"])
        else:
            kwh = potencia * horas
            kwh_total += kwh

        filas.append({
            "codigo": op["codigo"],
            "centro": op["centro"],
            "potencia": potencia,
            "horas": horas,
            "kwh": kwh,
            "kg": (kwh * factor_electrico) if (kwh is not None and factor_electrico is not None) else None
        })

    kg_produccion = (kwh_total * factor_electrico) if factor_electrico is not None else None

    # ---- Transporte ----
    filas_t = []
    kg_transporte = 0.0
    despachos_incompletos = 0

    for d in despachos:
        factor = d["factor"] if d["factor"] is not None else factor_transporte_defecto
        peso = d["peso_kg"]
        distancia = d["distancia_km"]

        if peso is None or distancia is None or factor is None:
            despachos_incompletos += 1
            toneladas = tkm = kg = None
        else:
            toneladas = d["unidades"] * peso / 1000
            tkm = toneladas * distancia
            kg = tkm * factor
            kg_transporte += kg

        filas_t.append({
            "codigo": d["codigo"],
            "vehiculo": d["vehiculo"],
            "unidades": d["unidades"],
            "peso_kg": peso,
            "distancia_km": distancia,
            "factor": factor,
            "toneladas": toneladas,
            "tkm": tkm,
            "kg": kg
        })

    # ---- Totales y por unidad ----
    completo_produccion = (factor_electrico is not None and len(sin_potencia) == 0 and len(ops) > 0)
    completo_transporte = (despachos_incompletos == 0)

    kg_total = None
    if kg_produccion is not None and completo_produccion:
        kg_total = kg_produccion + kg_transporte

    def por_unidad(valor):
        if valor is None or not unidades:
            return None
        return valor / unidades

    return {
        "filas": filas,
        "kwh_total": kwh_total,
        "kg_produccion": kg_produccion,
        "sin_potencia": sorted(set(sin_potencia)),
        "factor_electrico": factor_electrico,
        "filas_transporte": filas_t,
        "kg_transporte": kg_transporte,
        "despachos_incompletos": despachos_incompletos,
        "completo_produccion": completo_produccion,
        "completo_transporte": completo_transporte,
        "kg_total": kg_total,
        "unidades": unidades,
        "kwh_por_unidad": por_unidad(kwh_total if completo_produccion else None),
        "kwh_por_litro": (por_unidad(kwh_total) / litros_por_unidad) if (completo_produccion and por_unidad(kwh_total) is not None) else None,
        "kg_por_unidad": por_unidad(kg_total),
        "kg_produccion_por_unidad": por_unidad(kg_produccion if completo_produccion else None),
        "kg_transporte_por_unidad": por_unidad(kg_transporte if completo_transporte else None)
    }