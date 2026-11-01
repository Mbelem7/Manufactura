from datetime import datetime, timedelta

from flask import Blueprint, render_template, request, flash

from modulos import (
    produccion,
    inventario,
    detalle_bom,
    tableros
)
# Se importa con otro nombre para no confundirlo con el modulo de rutas de BOM
from modulos import bom as bom_db
from routes.planta import _calcular_oee, TIPOS_PARADA


tableros_bp = Blueprint(
    "tableros",
    __name__,
    url_prefix="/tableros"
)


# Valores (ajustarlos a los que se usen en la BD)
LOTE_BOTELLAS = 50            # botellas por lote de produccion (Entregable 1)
TIPO_PRODUCTO_TERMINADO = "producto_terminado"
ETIQUETAS_DISPOSICION = {
    "liberacion": "Liberación",
    "retrabajo": "Retrabajo",
    "scrap": "Scrap",
    "pendiente": "Pendiente"
}


# ---------- AYUDAS INTERNAS ----------

def _periodo():
    # Lee ?inicio=AAAA-MM-DD&fin=AAAA-MM-DD. Devuelve (inicio, fin_exclusivo, inicio_txt, fin_txt)
    inicio_txt = request.args.get("inicio") or None
    fin_txt = request.args.get("fin") or None
    inicio = fin = None

    try:
        if inicio_txt:
            inicio = datetime.strptime(inicio_txt, "%Y-%m-%d")
        if fin_txt:
            fin = datetime.strptime(fin_txt, "%Y-%m-%d") + timedelta(days=1)
    except ValueError:
        flash("Use fechas con formato AAAA-MM-DD", "error")
        return None, None, None, None

    return inicio, fin, inicio_txt, fin_txt


def _num(valor):
    return float(valor) if valor is not None else 0.0


def _estado(texto):
    return texto.replace("_", " ").capitalize()


def _grafico(id_canvas, tipo, etiquetas, series, horizontal=False, apilado=False, eje=None):
    # Especificacion de una grafica para el script compartido (tableros/_graficos.html)
    # series: lista de dicts {"nombre", "valores", "color" (opcional)}
    return {
        "id": id_canvas,
        "tipo": tipo,
        "etiquetas": etiquetas,
        "series": series,
        "horizontal": horizontal,
        "apilado": apilado,
        "eje": eje
    }


def _promedio(lista, clave):
    valores = [c[clave] for c in lista if c[clave] is not None]
    return sum(valores) / len(valores) if valores else None


# TABLERO DE PRODUCCION

@tableros_bp.route("/produccion")
def produccion_rubro():
    inicio, fin, inicio_txt, fin_txt = _periodo()

    ejecuciones = [
        e for e in produccion.obtener_produccion_con_operador()
        if (inicio is None or e.fecha_inicio >= inicio) and (fin is None or e.fecha_inicio < fin)
    ]

    calculos = [_calcular_oee(e)[0] for e in ejecuciones]
    con_oee = [c for c in calculos if c["oee"] is not None]

    pareto = {}
    for c in calculos:
        for tipo, minutos in c["pareto"]:
            pareto[tipo] = pareto.get(tipo, 0.0) + minutos
    pareto = sorted(pareto.items(), key=lambda x: x[1], reverse=True)

    terminadas = [e for e in ejecuciones if e.fecha_fin]
    aceptadas = sum(e.cantidad_aceptada for e in terminadas)
    rechazadas = sum(e.cantidad_rechazada for e in terminadas)

    ordenes = tableros.ordenes_por_estado(inicio, fin)
    por_dia = tableros.produccion_por_dia(inicio, fin)
    resultados = tableros.controles_por_resultado(inicio, fin)
    disposiciones = tableros.controles_por_disposicion(inicio, fin)
    alertas = tableros.alertas_por_nivel(inicio, fin)

    no_conformes = sum(r.total for r in resultados if r.resultado == "no_conforme")
    total_controles = sum(r.total for r in resultados)

    indicadores = {
        "disponibilidad": _promedio(con_oee, "disponibilidad"),
        "rendimiento": _promedio(con_oee, "rendimiento"),
        "calidad": _promedio(con_oee, "calidad"),
        "oee": _promedio(con_oee, "oee")
    }

    kpis = {
        "ordenes": sum(o.total for o in ordenes),
        "aceptadas": aceptadas,
        "rechazadas": rechazadas,
        "rendimiento": (aceptadas / (aceptadas + rechazadas)) if (aceptadas + rechazadas) else None,
        "oee": indicadores["oee"],
        "ejecuciones_oee": len(con_oee),
        "controles": total_controles,
        "no_conformes": no_conformes,
        "alertas": sum(a.total for a in alertas)
    }

    def pct(valor):
        return round(valor * 100, 1) if valor is not None else 0

    graficos = [
        _grafico("grafOrdenes", "doughnut", [_estado(o.estado) for o in ordenes],
                 [{"nombre": "Órdenes", "valores": [o.total for o in ordenes]}]),
        _grafico("grafDias", "bar", [d.dia.strftime("%d/%m") for d in por_dia],
                 [{"nombre": "Aceptadas", "valores": [_num(d.aceptadas) for d in por_dia], "color": "#198754"},
                  {"nombre": "Rechazadas", "valores": [_num(d.rechazadas) for d in por_dia], "color": "#dc3545"}],
                 apilado=True, eje="Unidades"),
        _grafico("grafOee", "bar", ["Disponibilidad", "Rendimiento", "Calidad", "OEE"],
                 [{"nombre": "%", "valores": [pct(indicadores[k]) for k in ("disponibilidad", "rendimiento", "calidad", "oee")],
                   "color": "#0d6efd"}],
                 eje="%"),
        _grafico("grafParadas", "bar", [TIPOS_PARADA.get(t, t) for t, _ in pareto],
                 [{"nombre": "Minutos simulados", "valores": [round(m, 1) for _, m in pareto], "color": "#fd7e14"}],
                 eje="Minutos simulados"),
        _grafico("grafCalidad", "doughnut", [_estado(r.resultado) for r in resultados],
                 [{"nombre": "Controles", "valores": [r.total for r in resultados]}]),
        _grafico("grafDisposicion", "bar", [ETIQUETAS_DISPOSICION.get(d.disposicion, d.disposicion) for d in disposiciones],
                 [{"nombre": "Controles", "valores": [d.total for d in disposiciones], "color": "#6f42c1"}],
                 eje="Controles")
    ]

    return render_template(
        "tableros/produccion.html",
        kpis=kpis,
        graficos=graficos,
        inicio=inicio_txt,
        fin=fin_txt
    )


# TABLERO DE VENTAS

@tableros_bp.route("/ventas")
def ventas_rubro():
    inicio, fin, inicio_txt, fin_txt = _periodo()

    resumen = tableros.ventas_resumen(inicio, fin)
    estados = tableros.ventas_por_estado(inicio, fin)
    meses = tableros.ventas_por_mes(inicio, fin)
    productos = tableros.ventas_por_producto(inicio, fin)
    clientes = tableros.ventas_por_cliente(inicio, fin)
    despachadas = tableros.unidades_despachadas(inicio, fin)

    total_ordenes = sum(e.total for e in estados)
    ordenes_despachadas = sum(e.total for e in estados if e.estado == "despachada")

    kpis = {
        "total": _num(resumen.total),
        "ordenes": resumen.ordenes,
        "ticket": (_num(resumen.total) / resumen.ordenes) if resumen.ordenes else None,
        "unidades_despachadas": _num(despachadas),
        "cumplimiento": (ordenes_despachadas / total_ordenes) if total_ordenes else None
    }

    graficos = [
        _grafico("grafMeses", "bar", [m.mes.strftime("%m/%Y") for m in meses],
                 [{"nombre": "Ventas (C$)", "valores": [_num(m.total) for m in meses], "color": "#0d6efd"}],
                 eje="C$"),
        _grafico("grafEstados", "doughnut", [_estado(e.estado) for e in estados],
                 [{"nombre": "Órdenes", "valores": [e.total for e in estados]}]),
        _grafico("grafProductos", "bar", [p.nombre for p in productos],
                 [{"nombre": "Ventas (C$)", "valores": [_num(p.monto) for p in productos], "color": "#198754"}],
                 horizontal=True, eje="C$"),
        _grafico("grafClientes", "bar", [c.empresa for c in clientes],
                 [{"nombre": "Ventas (C$)", "valores": [_num(c.monto) for c in clientes], "color": "#6f42c1"}],
                 horizontal=True, eje="C$")
    ]

    return render_template(
        "tableros/ventas.html",
        kpis=kpis,
        graficos=graficos,
        inicio=inicio_txt,
        fin=fin_txt
    )


# TABLERO DE COMPRAS

@tableros_bp.route("/compras")
def compras_rubro():
    inicio, fin, inicio_txt, fin_txt = _periodo()

    resumen = tableros.compras_resumen(inicio, fin)
    estados = tableros.compras_por_estado(inicio, fin)
    meses = tableros.compras_por_mes(inicio, fin)
    proveedores = tableros.compras_por_proveedor(inicio, fin)
    materiales = tableros.compras_por_material(inicio, fin)
    horas = tableros.horas_hasta_recepcion(inicio, fin)

    total_ordenes = sum(e.total for e in estados)
    recibidas = sum(e.total for e in estados if e.estado == "recibida")

    kpis = {
        "total": _num(resumen.total),
        "ordenes": resumen.ordenes,
        "recibidas": (recibidas / total_ordenes) if total_ordenes else None,
        "horas_recepcion": _num(horas) if horas is not None else None
    }

    graficos = [
        _grafico("grafMeses", "bar", [m.mes.strftime("%m/%Y") for m in meses],
                 [{"nombre": "Compras (C$)", "valores": [_num(m.total) for m in meses], "color": "#0d6efd"}],
                 eje="C$"),
        _grafico("grafEstados", "doughnut", [_estado(e.estado) for e in estados],
                 [{"nombre": "Órdenes", "valores": [e.total for e in estados]}]),
        _grafico("grafProveedores", "bar", [p.empresa for p in proveedores],
                 [{"nombre": "Compras (C$)", "valores": [_num(p.monto) for p in proveedores], "color": "#fd7e14"}],
                 horizontal=True, eje="C$"),
        _grafico("grafMateriales", "bar", [m.nombre for m in materiales],
                 [{"nombre": "Compras (C$)", "valores": [_num(m.monto) for m in materiales], "color": "#198754"}],
                 horizontal=True, eje="C$")
    ]

    return render_template(
        "tableros/compras.html",
        kpis=kpis,
        graficos=graficos,
        inicio=inicio_txt,
        fin=fin_txt
    )


# TABLERO DE INVENTARIO

@tableros_bp.route("/inventario")
def inventario_rubro():
    inicio, fin, inicio_txt, fin_txt = _periodo()

    productos = tableros.productos_con_existencia()
    existencia = {p.id_producto: _num(p.existencia) for p in productos}
    almacenes = tableros.existencias_por_almacen()
    antiguos = tableros.lotes_mas_antiguos()

    # Cobertura de materia prima: cuantos lotes de produccion cubre el stock actual
    cobertura = []
    capacidad = None
    limitante = None
    boms = bom_db.obtener_boms_por_estado("activo")

    if boms:
        for c in detalle_bom.obtener_detalles_bom_por_bom(boms[0].id_bom):
            por_botella = _num(c.cantidad)
            botellas = existencia.get(c.producto_component_id, 0.0) / por_botella if por_botella > 0 else 0.0

            cobertura.append({
                "codigo": c.producto_codigo,
                "nombre": c.producto_nombre,
                "lotes": botellas / LOTE_BOTELLAS,
                "botellas": botellas
            })

            if capacidad is None or botellas < capacidad:
                capacidad = botellas
                limitante = c.producto_nombre

    # Rotacion del producto terminado (aproximada con la existencia actual)
    stock_pt = sum(_num(p.existencia) for p in productos if p.tipo_producto == TIPO_PRODUCTO_TERMINADO)
    despachadas = _num(tableros.unidades_despachadas(inicio, fin))

    kpis = {
        "productos_con_existencia": len([p for p in productos if _num(p.existencia) > 0]),
        "lotes_con_existencia": sum(a.lotes for a in almacenes),
        "capacidad": capacidad,
        "limitante": limitante,
        "stock_pt": stock_pt,
        "despachadas": despachadas,
        "rotacion": (despachadas / stock_pt) if stock_pt > 0 else None
    }

    graficos = [
        _grafico("grafCobertura", "bar", [c["nombre"] for c in cobertura],
                 [{"nombre": "Lotes de producción cubiertos", "valores": [round(c["lotes"], 2) for c in cobertura],
                   "color": "#0d6efd"}],
                 horizontal=True, eje="Lotes de producción"),
        _grafico("grafTerminados", "bar",
                 [p.nombre for p in productos if p.tipo_producto == TIPO_PRODUCTO_TERMINADO],
                 [{"nombre": "Existencia", "valores": [_num(p.existencia) for p in productos if p.tipo_producto == TIPO_PRODUCTO_TERMINADO],
                   "color": "#198754"}],
                 eje="Unidades"),
        _grafico("grafAlmacenes", "bar", [a.nombre for a in almacenes],
                 [{"nombre": "Productos con existencia", "valores": [a.productos for a in almacenes], "color": "#6f42c1"},
                  {"nombre": "Lotes con existencia", "valores": [a.lotes for a in almacenes], "color": "#fd7e14"}],
                 eje="Cantidad")
    ]

    return render_template(
        "tableros/inventario.html",
        kpis=kpis,
        graficos=graficos,
        cobertura=cobertura,
        antiguos=antiguos,
        lote_botellas=LOTE_BOTELLAS,
        inicio=inicio_txt,
        fin=fin_txt
    )