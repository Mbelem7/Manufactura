# Caracteristicas de una operacion para diagnosticar el sensor y recorrido del arbol de decision.
# No usa base de datos ni librerias externas: el arbol ya entrenado esta en arbol_sensor.py.

from modulos.spc import inicio_estable, MINIMO_PUNTOS

RANGO_FISICO = (0.0, 100.0)     # fuera de este rango la lectura es imposible para agua liquida

# Nombre legible y unidad de cada caracteristica (en el orden en que se usan)
CARACTERISTICAS = [
    ("ruido", "Variación media entre lecturas", "°C"),
    ("repetidas", "Lecturas repetidas", "fracción"),
    ("faltantes", "Lecturas faltantes", "fracción"),
    ("imposibles", "Valores fuera del rango físico", "fracción"),
    ("salto_max", "Mayor salto entre lecturas", "°C"),
    ("dias_calibracion", "Días desde la última calibración", "días")
]

NOMBRES = {clave: nombre for clave, nombre, _ in CARACTERISTICAS}
UNIDADES = {clave: unidad for clave, _, unidad in CARACTERISTICAS}


def caracteristicas(lecturas, duracion, minuto_actual, dias_calibracion):
    # lecturas: lista de dicts {"minuto", "valor"} de la operacion
    # Devuelve un dict con las seis caracteristicas, o None si todavia hay muy pocas lecturas
    inicio = inicio_estable(duracion)
    estables = sorted((l for l in lecturas if l["minuto"] >= inicio), key=lambda l: l["minuto"])

    if len(estables) < MINIMO_PUNTOS:
        return None

    valores = [l["valor"] for l in estables]
    diferencias = [abs(valores[i] - valores[i - 1]) for i in range(1, len(valores))]

    esperadas = max(1, int(minuto_actual) - inicio + 1)
    minimo, maximo = RANGO_FISICO

    return {
        "ruido": sum(diferencias) / len(diferencias),
        "repetidas": sum(1 for d in diferencias if round(d, 2) == 0) / len(diferencias),
        "faltantes": max(0.0, 1 - len(estables) / esperadas),
        "imposibles": sum(1 for v in valores if v < minimo or v > maximo) / len(valores),
        "salto_max": max(diferencias),
        "dias_calibracion": float(dias_calibracion)
    }


def recorrer(arbol, datos):
    # Recorre el arbol con las caracteristicas y devuelve (clase, probabilidad, camino)
    camino = []
    nodo = arbol

    while "clase" not in nodo:
        clave = nodo["caracteristica"]
        umbral = nodo["umbral"]
        valor = datos[clave]

        if valor <= umbral:
            camino.append("%s ≤ %s (valor: %s)" % (NOMBRES[clave], texto_valor(clave, umbral), texto_valor(clave, valor)))
            nodo = nodo["izquierda"]
        else:
            camino.append("%s > %s (valor: %s)" % (NOMBRES[clave], texto_valor(clave, umbral), texto_valor(clave, valor)))
            nodo = nodo["derecha"]

    total = nodo["muestras"]
    probabilidad = nodo["conteos"].get(nodo["clase"], 0) / total if total else None

    return nodo["clase"], probabilidad, camino


def reglas(arbol, prefijo=None):
    # Todas las reglas del arbol, una por hoja, como texto
    prefijo = prefijo or []

    if "clase" in arbol:
        condicion = " y ".join(prefijo) if prefijo else "siempre"
        return ["Si %s, entonces %s (%d muestras)." % (condicion, arbol["clase"], arbol["muestras"])]

    clave = arbol["caracteristica"]
    umbral = texto_valor(clave, arbol["umbral"])

    return (
        reglas(arbol["izquierda"], prefijo + ["%s ≤ %s" % (NOMBRES[clave], umbral)])
        + reglas(arbol["derecha"], prefijo + ["%s > %s" % (NOMBRES[clave], umbral)])
    )


def texto_valor(clave, valor):
    # Un valor con su unidad: las fracciones se muestran como porcentaje
    unidad = UNIDADES[clave]

    if unidad == "fracción":
        return "%.1f %%" % (valor * 100)
    if unidad == "días":
        return "%.0f días" % valor
    return "%.2f %s" % (valor, unidad)