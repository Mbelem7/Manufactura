# Entrenamiento del arbol de decision que diagnostica el estado del sensor de temperatura.
#
# Como no hay un sensor real, los datos de entrenamiento se GENERAN con el simulador:
#   - normal:        sensor sano (incluye procesos que se desvian: el sensor no tiene la culpa)
#   - calibrar:      sensor degradado, o sano pero con la calibracion vencida
#   - mantenimiento: sensor atascado, ruidoso, con valores imposibles o que pierde muchas lecturas
# El arbol es un CART (indice de Gini) escrito en Python puro. Este archivo es la evidencia de
# como se obtuvo el modelo; el resultado ya esta guardado en arbol_sensor.py, asi que el sistema
# no necesita volver a ejecutarlo.

import random

from modulos import sensor_sim
from modulos.diagnostico import caracteristicas, CARACTERISTICAS

CLASES = ["normal", "calibrar", "mantenimiento"]
CLAVES = [c[0] for c in CARACTERISTICAS]
DURACION = 40.0
OBJETIVO = 40.0


# ---------- DATOS SIMULADOS ----------

def _muestra(rng, escenario, dias, id_op, perdida_extra=0.0):
    lecturas = []

    for m in range(0, int(DURACION) + 1):
        if sensor_sim.lectura_perdida(m, escenario, id_op):
            continue
        if perdida_extra and random.Random(f"extra-{id_op}-{m}").random() < perdida_extra:
            continue

        valor = sensor_sim.temperatura(m, DURACION, escenario, id_op, OBJETIVO)
        lecturas.append({"minuto": m, "valor": round(valor, 2)})

    return caracteristicas(lecturas, DURACION, DURACION, dias)


def generar_datos(n, semilla):
    rng = random.Random(semilla)
    procesos = ["normal", "deriva", "salto", "pico"]
    datos = []
    id_op = 100000 + semilla * 1000

    while len(datos) < n:
        id_op += 1
        sorteo = rng.random()

        if sorteo < 0.40:
            clase = "normal"
            x = _muestra(rng, rng.choice(procesos), rng.uniform(0, 90), id_op)
        elif sorteo < 0.60:
            clase = "calibrar"            # sensor sano pero con la calibracion vencida
            x = _muestra(rng, rng.choice(procesos), rng.uniform(95, 400), id_op)
        elif sorteo < 0.74:
            clase = "calibrar"            # sensor degradado
            x = _muestra(rng, "sensor_degradado", rng.uniform(0, 200), id_op)
        else:
            clase = "mantenimiento"
            falla = rng.choice(["sensor_atascado", "sensor_ruidoso", "sensor_imposible", "perdida"])
            if falla == "perdida":        # el sensor deja de enviar muchas lecturas
                x = _muestra(rng, "normal", rng.uniform(0, 300), id_op, perdida_extra=rng.uniform(0.35, 0.6))
            else:
                x = _muestra(rng, falla, rng.uniform(0, 300), id_op)

        if x is not None:
            datos.append((x, clase))

    return datos


# ---------- CART ----------

def _gini(conteos, total):
    return 1.0 - sum((c / total) ** 2 for c in conteos.values()) if total else 0.0


def _conteos(filas):
    resultado = {c: 0 for c in CLASES}
    for _, clase in filas:
        resultado[clase] += 1
    return resultado


def _mejor_division(filas, minimo_hoja):
    total = len(filas)
    base = _gini(_conteos(filas), total)
    mejor = None

    for clave in CLAVES:
        ordenadas = sorted(filas, key=lambda f: f[0][clave])
        izquierda = {c: 0 for c in CLASES}
        derecha = _conteos(filas)

        for i in range(total - 1):
            x, clase = ordenadas[i]
            izquierda[clase] += 1
            derecha[clase] -= 1

            valor, siguiente = x[clave], ordenadas[i + 1][0][clave]
            if valor == siguiente:
                continue

            n_izq, n_der = i + 1, total - i - 1
            if n_izq < minimo_hoja or n_der < minimo_hoja:
                continue

            impureza = (n_izq * _gini(izquierda, n_izq) + n_der * _gini(derecha, n_der)) / total
            ganancia = base - impureza

            if mejor is None or ganancia > mejor[0]:
                mejor = (ganancia, clave, (valor + siguiente) / 2)

    return mejor


def _construir(filas, profundidad, maxima, minimo_hoja, importancia, total_global):
    conteos = _conteos(filas)
    clase = max(conteos, key=conteos.get)
    hoja = {"clase": clase, "conteos": conteos, "muestras": len(filas)}

    if profundidad >= maxima or len(set(c for _, c in filas)) == 1:
        return hoja

    division = _mejor_division(filas, minimo_hoja)
    if division is None or division[0] < 0.005:
        return hoja

    ganancia, clave, umbral = division
    importancia[clave] += ganancia * len(filas) / total_global

    izq = [f for f in filas if f[0][clave] <= umbral]
    der = [f for f in filas if f[0][clave] > umbral]

    return {
        "caracteristica": clave,
        "umbral": round(umbral, 4),
        "muestras": len(filas),
        "conteos": conteos,
        "izquierda": _construir(izq, profundidad + 1, maxima, minimo_hoja, importancia, total_global),
        "derecha": _construir(der, profundidad + 1, maxima, minimo_hoja, importancia, total_global)
    }


def entrenar(filas, maxima=5, minimo_hoja=10):
    importancia = {c: 0.0 for c in CLAVES}
    arbol = _construir(filas, 0, maxima, minimo_hoja, importancia, len(filas))
    suma = sum(importancia.values()) or 1.0
    return arbol, {c: round(v / suma, 4) for c, v in importancia.items()}


def predecir(arbol, x):
    nodo = arbol
    while "clase" not in nodo:
        nodo = nodo["izquierda"] if x[nodo["caracteristica"]] <= nodo["umbral"] else nodo["derecha"]
    return nodo["clase"]


def evaluar(arbol, filas):
    matriz = [[0] * len(CLASES) for _ in CLASES]
    for x, real in filas:
        matriz[CLASES.index(real)][CLASES.index(predecir(arbol, x))] += 1
    aciertos = sum(matriz[i][i] for i in range(len(CLASES)))
    return matriz, aciertos / len(filas)


def ejecutar(semilla=2026, n=2000, proporcion_prueba=0.3):
    datos = generar_datos(n, semilla)
    random.Random(semilla).shuffle(datos)
    corte = int(len(datos) * (1 - proporcion_prueba))
    entrenamiento, prueba = datos[:corte], datos[corte:]

    arbol, importancia = entrenar(entrenamiento)
    _, exactitud_entrenamiento = evaluar(arbol, entrenamiento)
    matriz, exactitud_prueba = evaluar(arbol, prueba)

    return arbol, {
        "semilla": semilla,
        "muestras_entrenamiento": len(entrenamiento),
        "muestras_prueba": len(prueba),
        "clases": CLASES,
        "exactitud_entrenamiento": round(exactitud_entrenamiento, 4),
        "exactitud_prueba": round(exactitud_prueba, 4),
        "matriz_confusion": matriz,
        "importancia": importancia
    }