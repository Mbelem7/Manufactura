import math

# Cálculo de la carta de control individual (I-MR) y de sus reglas de alerta.
# No usa base de datos: recibe las lecturas y devuelve los límites y las alertas.

FRACCION_CALENTAMIENTO = 0.35  # el primer 35 % (calentamiento y enfriamiento) no se controla
PUNTOS_BASE = 15               # lecturas estables usadas para calcular los límites
MINIMO_PUNTOS = 8              # con menos lecturas estables no se calcula nada
D2 = 1.128                     # constante para estimar sigma con el rango móvil (n = 2)


def inicio_estable(duracion):
    # Primer minuto de la fase estable
    return math.ceil(duracion * FRACCION_CALENTAMIENTO)


def analizar(lecturas, duracion, lsl=None, usl=None):
    # lecturas: lista de dicts {"minuto", "valor", "id"} ordenada por minuto
    # lsl / usl: limites de especificacion (opcionales)
    inicio = inicio_estable(duracion)
    estables = [l for l in lecturas if l["minuto"] >= inicio]

    resultado = {
        "suficiente": False,
        "inicio_estable": inicio,
        "puntos_estables": len(estables),
        "violaciones": []
    }

    if len(estables) < MINIMO_PUNTOS:
        return resultado

    # Limites de control: se calculan con las primeras lecturas estables
    base = [l["valor"] for l in estables[:PUNTOS_BASE]]
    cl = sum(base) / len(base)
    rangos = [abs(base[i] - base[i - 1]) for i in range(1, len(base))]
    sigma = (sum(rangos) / len(rangos)) / D2
    sigma = max(sigma, 0.05)

    resultado.update({
        "suficiente": True,
        "limites_provisionales": len(estables) < PUNTOS_BASE,
        "cl": cl,
        "sigma": sigma,
        "ucl": cl + 3 * sigma,
        "lcl": cl - 3 * sigma,
        "mas2": cl + 2 * sigma,
        "menos2": cl - 2 * sigma
    })

    # Capacidad del proceso frente a la especificacion
    media = sum(l["valor"] for l in estables) / len(estables)
    resultado["media"] = media

    if lsl is not None and usl is not None:
        resultado["cp"] = (usl - lsl) / (6 * sigma)
        resultado["cpk"] = min(usl - media, media - lsl) / (3 * sigma)

    # Reglas de alerta
    violaciones = []
    racha = 0
    lado_racha = 0

    for i, p in enumerate(estables):
        v = p["valor"]
        desvio = v - cl
        lado = 1 if desvio > 0 else (-1 if desvio < 0 else 0)

        # 1) Un punto fuera de +-3 sigma
        if abs(desvio) > 3 * sigma:
            violaciones.append(_alerta(p, "fuera_3sigma", "critica",
                f"Temperatura fuera de los límites de control (±3σ) en el minuto {p['minuto']}: {v:.2f} °C"))

        # 2) Dos de tres puntos seguidos a mas de 2 sigma, del mismo lado
        if i >= 2 and abs(desvio) > 2 * sigma:
            ventana = estables[i - 2:i + 1]
            del_lado = [q for q in ventana if (q["valor"] - cl) * lado > 2 * sigma * abs(lado)]
            if lado != 0 and len(del_lado) >= 2:
                violaciones.append(_alerta(p, "dos_de_tres_2sigma", "advertencia",
                    f"Dos de tres lecturas seguidas a más de 2σ del mismo lado (minuto {p['minuto']})"))

        # 3) Ocho puntos seguidos del mismo lado de la linea central
        if lado != 0 and lado == lado_racha:
            racha += 1
        else:
            racha = 1 if lado != 0 else 0
            lado_racha = lado
        if racha == 8:
            violaciones.append(_alerta(p, "racha_8", "advertencia",
                f"Ocho lecturas seguidas del mismo lado de la línea central (minuto {p['minuto']}): posible deriva"))

        # 4) Fuera de la especificacion
        if (lsl is not None and v < lsl) or (usl is not None and v > usl):
            violaciones.append(_alerta(p, "fuera_especificacion", "critica",
                f"Temperatura fuera de la especificación ({lsl}–{usl} °C) en el minuto {p['minuto']}: {v:.2f} °C"))

    resultado["violaciones"] = violaciones
    return resultado


def _alerta(punto, regla, nivel, mensaje):
    return {
        "minuto": punto["minuto"],
        "valor": punto["valor"],
        "id_lectura": punto.get("id"),
        "regla": regla,
        "nivel": nivel,
        "mensaje": mensaje
    }