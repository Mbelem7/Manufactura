

from flask import Blueprint, render_template
from sqlalchemy import text

from app import db


dashboard_bp = Blueprint("dashboard", __name__)


_CONSULTA_DASHBOARD = text("""
    SELECT
        (SELECT COUNT(*) FROM public.producto) AS productos,
        (SELECT COUNT(*) FROM public.orden_produccion) AS ordenes_produccion,
        (SELECT COUNT(*) FROM public.orden_compra) AS ordenes_compra,
        (SELECT COUNT(*) FROM public.orden_venta) AS ordenes_venta,
        (SELECT COUNT(*) FROM public.orden_compra
         WHERE LOWER(estado) = 'recibida') AS compras_recibidas,
        (SELECT COUNT(*) FROM public.orden_venta
         WHERE LOWER(estado) = 'despachada') AS ventas_despachadas,
        (SELECT COALESCE(SUM(cantidad_aceptada), 0)
         FROM public.produccion) AS unidades_aceptadas,
        (SELECT COALESCE(SUM(cantidad_rechazada), 0)
         FROM public.produccion) AS unidades_rechazadas
""")


def _porcentaje(numerador, denominador):
    """Devuelve None cuando aún no existen datos para un indicador."""
    if not denominador:
        return None
    return round(float(numerador) * 100 / float(denominador), 1)


@dashboard_bp.route("/")
def index():
    datos = db.session.execute(_CONSULTA_DASHBOARD).mappings().one()

    resumen = {
        "productos": datos["productos"],
        "ordenes_produccion": datos["ordenes_produccion"],
        "ordenes_compra": datos["ordenes_compra"],
        "ordenes_venta": datos["ordenes_venta"],
    }

    aceptadas = datos["unidades_aceptadas"]
    rechazadas = datos["unidades_rechazadas"]

    kpis = {
        
        "yield_produccion": _porcentaje(aceptadas, aceptadas + rechazadas),
        
        "compras_recibidas": _porcentaje(
            datos["compras_recibidas"], datos["ordenes_compra"]
        ),
        "ventas_despachadas": _porcentaje(
            datos["ventas_despachadas"], datos["ordenes_venta"]
        ),
    }

    return render_template("dashboard/index.html", resumen=resumen, kpis=kpis)
