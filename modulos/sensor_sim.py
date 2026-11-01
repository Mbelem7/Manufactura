import math
import random

from modulos.spc import FRACCION_CALENTAMIENTO, inicio_estable

# Sensor de temperatura simulado para la elaboracion de la mezcla (OP-020); no hay hardware.
# Reproduce las tres fases del proceso descrito en el Entregable 1:
#   1) calentamiento del agua con romero hasta la ebullicion,
#   2) enfriamiento hasta la temperatura de mezclado,
#   3) mezclado a temperatura estable (la unica fase que se controla con SPC).
# Genera una lectura por cada minuto simulado. El resultado depende solo de la operacion y del
# minuto, asi que repetir el calculo da siempre el mismo valor.
#
# Hay dos tipos de escenario:
#   - de PROCESO: el sensor esta sano pero el proceso se desvia (deriva, salto, pico);
#   - de SENSOR: el que falla es el sensor (atascado, ruidoso, degradado, valores imposibles).
# El arbol de decision aprende a distinguirlos.

ESCENARIOS = {
    "normal": "Normal",
    "deriva": "Proceso: deriva descendente",
    "salto": "Proceso: salto de nivel",
    "pico": "Proceso: pico aislado",
    "sensor_atascado": "Sensor: atascado",
    "sensor_ruidoso": "Sensor: ruidoso",
    "sensor_degradado": "Sensor: degradado",
    "sensor_imposible": "Sensor: valores imposibles"
}

ESCENARIOS_SENSOR = frozenset({"sensor_atascado", "sensor_ruidoso", "sensor_degradado", "sensor_imposible"})

FRACCION_CALENTAMIENTO_FASE = 0.15   # el calentamiento dura el 15 % de la operacion
VALOR_DESCONECTADO = -127.0          # lo que reporta un sensor desconectado (como el DS18B20)
INDICE_ATASCO = 10                   # el sensor atascado se congela en la lectura 10 de la fase estable

# Probabilidad de que falte la lectura de un minuto
PERDIDA = {"sensor_degradado": 0.12, "sensor_imposible": 0.05}


def lectura_perdida(minuto, escenario, semilla):
    # True si ese minuto no llego ninguna lectura (el sensor fallo o se desconecto)
    probabilidad = PERDIDA.get(escenario, 0.0)

    if probabilidad == 0.0:
        return False

    return random.Random(f"perdida-{semilla}-{minuto}").random() < probabilidad


def temperatura(minuto, duracion, escenario, semilla, objetivo, ebullicion=99.0, ambiente=26.0):
    # minuto: minuto simulado de la operacion (0, 1, 2...)
    # duracion: tiempo estandar de la operacion en minutos
    # semilla: identificador de la operacion (hace reproducible el ruido)
    # objetivo: temperatura de mezclado (parametro del proceso)
    rng = random.Random(f"{semilla}-{minuto}")

    fin_calentamiento = duracion * FRACCION_CALENTAMIENTO_FASE
    fin_enfriamiento = duracion * FRACCION_CALENTAMIENTO

    # 1) Calentamiento: de la temperatura ambiente a la ebullicion
    if minuto < fin_calentamiento:
        avance = minuto / fin_calentamiento
        base = ambiente + (ebullicion - ambiente) * (1 - math.exp(-3 * avance)) / (1 - math.exp(-3))
        return base + rng.gauss(0, 0.4)

    # 2) Enfriamiento: de la ebullicion a la temperatura de mezclado
    if minuto < fin_enfriamiento:
        avance = (minuto - fin_calentamiento) / (fin_enfriamiento - fin_calentamiento)
        base = objetivo + (ebullicion - objetivo) * math.exp(-4 * avance)
        return base + rng.gauss(0, 0.4)

    # 3) Mezclado: estable alrededor del objetivo
    indice = minuto - inicio_estable(duracion)   # posicion dentro de la fase estable

    # Sensor atascado: se congela en la lectura que dio en INDICE_ATASCO
    if escenario == "sensor_atascado" and indice >= INDICE_ATASCO:
        return temperatura(inicio_estable(duracion) + INDICE_ATASCO, duracion, "normal", semilla, objetivo, ebullicion, ambiente)

    # Ruido de un sensor sano
    ruido = 0.35 * (1 if minuto % 2 == 0 else -1) + max(-0.4, min(0.4, rng.gauss(0, 0.15)))
    ajuste = 0.0

    # Fallas del PROCESO: empiezan despues de las lecturas usadas para fijar los limites de control
    if escenario == "deriva" and indice >= 16:
        ajuste = -0.5 * (indice - 15)
    elif escenario == "salto" and indice >= 18:
        ajuste = 2.5
    elif escenario == "pico" and indice == 20:
        ajuste = 7.0

    # Fallas del SENSOR
    elif escenario == "sensor_ruidoso":
        ruido = max(-6.0, min(6.0, rng.gauss(0, 2.5)))
    elif escenario == "sensor_degradado":
        ruido = 0.35 * (1 if minuto % 2 == 0 else -1) + max(-1.2, min(1.2, rng.gauss(0, 0.45)))
    elif escenario == "sensor_imposible":
        if random.Random(f"imposible-{semilla}-{minuto}").random() < 0.15:
            return VALOR_DESCONECTADO

    return objetivo + ruido + ajuste