"""Autorización centralizada por roles para Manufactura (Flask).

Roles habilitados:
- administrador: acceso a todas las operaciones actuales del ERP, incluidas las de usuarios.
- operador: acceso a operaciones de inventario, producción, compras, ventas y reportes,
  pero NO a la administración de usuarios o configuración.

La calidad (inspección y disposición de lotes) y la planta (operaciones de la ruta y
sensor simulado) se rigen por las políticas de abajo.
Cualquier endpoint nuevo permanece bloqueado hasta registrar su política.
"""

from flask import jsonify, redirect, request, session, url_for
from modulos.seguridad import obtener_usuario_actual

ADMIN = "administrador"
OPERADOR = "operador"
AMBOS = frozenset({ADMIN, OPERADOR})
SOLO_ADMIN = frozenset({ADMIN})

# Clave: endpoint Flask (nombre_blueprint.nombre_funcion)
# Valor: {metodo_HTTP: frozenset(codigos_de_rol)}
POLITICA = {}


def _asignar(nombres, *, leer=None, escribir=None):
    for endpoint in nombres.split():
        if endpoint in POLITICA:
            raise ValueError(f"Permisos duplicados para la ruta: {endpoint}")
        reglas = {}
        if leer is not None:
            reglas["GET"] = frozenset(leer)
        if escribir is not None:
            reglas["POST"] = frozenset(escribir)
        POLITICA[endpoint] = reglas


# Dashboard: ambos roles pueden consultar.
_asignar("dashboard.index", leer=AMBOS)

# Administrar usuarios y asignar roles: exclusivamente Administrador.
# Nota: los endpoints actuales de configuracion son GET; cuando se añadan
# endpoints POST para usuarios, deben declararse aqui con escribir=SOLO_ADMIN.
_asignar("configuracion.usuarios configuracion.usuario_nuevo", leer=SOLO_ADMIN)
_asignar("""
    configuracion.csrf_api configuracion.roles_api configuracion.usuarios_api
    configuracion.usuario_detalle_api
""", leer=SOLO_ADMIN)
_asignar("""
    configuracion.vincular_usuario_api configuracion.actualizar_usuario_api
    configuracion.cambiar_estado_usuario_api
""", escribir=SOLO_ADMIN)

# Inventario: registros de artículos, almacenes, lotes, existencias y reportes.
_asignar("inventario.productos inventario.almacenes inventario.lotes inventario.existencias inventario.reporte", leer=AMBOS)
_asignar("""
    inventario.producto_nuevo inventario.producto_editar
    inventario.almacen_nuevo inventario.almacen_editar
    inventario.lote_nuevo inventario.lote_editar
""", leer=AMBOS, escribir=AMBOS)
_asignar("inventario.producto_baja inventario.almacen_baja", escribir=AMBOS)

# Producción: BOM, centros, rutas, órdenes, ejecuciones y reportes.
_asignar("""
    produccion.bom produccion.bom_detalle
    produccion.centros_trabajo produccion.rutas
    produccion.ordenes produccion.orden_detalle produccion.ejecuciones
    produccion.reporte
""", leer=AMBOS)
_asignar("""
    produccion.bom_nuevo produccion.bom_editar
    produccion.centro_trabajo_nuevo produccion.centro_trabajo_editar
    produccion.ruta_nueva produccion.ruta_editar
    produccion.orden_nueva produccion.orden_editar
    produccion.ejecucion_nueva
""", leer=AMBOS, escribir=AMBOS)
_asignar("""
    produccion.bom_baja produccion.bom_componente_agregar
    produccion.bom_componente_actualizar produccion.bom_componente_eliminar
    produccion.centro_trabajo_baja produccion.ruta_baja
    produccion.orden_baja produccion.ejecucion_terminar
    produccion.bom_operacion_agregar produccion.bom_operacion_actualizar produccion.bom_operacion_baja
""", escribir=AMBOS)

# Calidad: revisión de lotes (operación OP-040). Cualquier rol puede registrar una
# revisión, pero la disposición de un lote no conforme (liberación con concesión,
# retrabajo o scrap) la decide solo el administrador. Para que también la decida el
# operador, cambiar SOLO_ADMIN por AMBOS en la última línea de este bloque.
_asignar("calidad.controles calidad.control_detalle", leer=AMBOS)
_asignar("calidad.control_nuevo", leer=AMBOS, escribir=AMBOS)
_asignar("calidad.control_disposicion", escribir=SOLO_ADMIN)

# Planta (MES): operaciones de la ruta, paradas, sensor simulado, carta de control (SPC) y OEE.
_asignar("planta.operaciones planta.spc_operacion planta.lecturas_json planta.oee_resumen planta.oee_detalle", leer=AMBOS)
_asignar("planta.operacion_iniciar planta.operacion_terminar planta.parada_iniciar planta.parada_reanudar", escribir=AMBOS)

# Sensores: calibración, diagnóstico con árbol de decisión y modelo. Cualquier rol consulta y
# registra calibraciones.
_asignar("sensores.index sensores.detalle sensores.modelo sensores.diagnostico_json", leer=AMBOS)
_asignar("sensores.calibrar", escribir=AMBOS)

# Sostenibilidad: energía, intensidad energética y huella de carbono. Cualquier rol consulta y
# completa los datos de cada equipo, producto y despacho; solo el administrador registra los
# factores de emisión, porque deben citar su fuente.
_asignar("sostenibilidad.resumen sostenibilidad.detalle sostenibilidad.parametros", leer=AMBOS)
_asignar("""
    sostenibilidad.centro_potencia sostenibilidad.producto_peso sostenibilidad.despacho_transporte
""", escribir=AMBOS)
_asignar("sostenibilidad.factor_nuevo", escribir=SOLO_ADMIN)

# Tableros por rubro (producción, ventas, compras e inventario): solo consulta.
_asignar("""
    tableros.produccion_rubro tableros.ventas_rubro
    tableros.compras_rubro tableros.inventario_rubro
""", leer=AMBOS)

# Compras: proveedores, órdenes y recepciones.
_asignar("""
    compras.ordenes compras.orden_detalle compras.proveedores
    compras.recepciones compras.recepcion_detalle compras.reporte
""", leer=AMBOS)
_asignar("""
    compras.orden_nueva compras.orden_editar
    compras.proveedor_nuevo compras.proveedor_editar
    compras.recepcion_nueva compras.recepcion_editar
""", leer=AMBOS, escribir=AMBOS)
_asignar("""
    compras.orden_baja compras.orden_detalle_agregar
    compras.orden_detalle_actualizar compras.orden_detalle_eliminar
    compras.proveedor_baja compras.recepcion_baja
""", escribir=AMBOS)

# Ventas: clientes, órdenes, despachos y reportes.
_asignar("""
    ventas.ordenes ventas.orden_detalle ventas.clientes
    ventas.despachos ventas.despacho_detalle ventas.reporte
""", leer=AMBOS)
_asignar("""
    ventas.orden_nueva ventas.orden_editar
    ventas.cliente_nuevo ventas.cliente_editar
    ventas.despacho_nuevo ventas.despacho_editar
""", leer=AMBOS, escribir=AMBOS)
_asignar("""
    ventas.orden_baja ventas.orden_detalle_agregar
    ventas.orden_detalle_actualizar ventas.orden_detalle_eliminar
    ventas.cliente_baja ventas.despacho_baja
""", escribir=AMBOS)

# El login, logout y la consulta de sesión tienen su propio control en routes/auth.py.
PUBLICOS = frozenset({"static", "auth.login", "auth.logout", "auth.me"})


def _peticion_de_pagina():
    """Solo navegación HTML del navegador; API/PowerShell siguen recibiendo JSON."""
    return request.method in {"GET", "HEAD"} and "text/html" in request.headers.get("Accept", "").lower()


def verificar_acceso():
    """Registrar una sola vez con app.before_request(verificar_acceso)."""
    endpoint = request.endpoint
    if endpoint in PUBLICOS:
        return None
    if endpoint is None:  # Flask responde 404 / 405 sin filtrar rutas internas.
        return None

    reglas = POLITICA.get(endpoint)
    if reglas is None:
        return jsonify(error="Ruta sin permisos definidos. Contactá al administrador."), 403

    metodo = "GET" if request.method == "HEAD" else request.method
    if metodo == "OPTIONS":  # Preflight automático, no ejecuta la operación.
        return None
    roles_permitidos = reglas.get(metodo)
    if roles_permitidos is None:
        return jsonify(error="Método no autorizado para esta ruta."), 405

    if not session.get("id_usuario"):
        if _peticion_de_pagina():
            return redirect(url_for("auth.login"))
        return jsonify(error="Iniciá sesión para continuar."), 401

    usuario = obtener_usuario_actual()  # Consulta usuario, persona y rol activos en BD.
    if usuario is None:
        session.clear()
        if _peticion_de_pagina():
            return redirect(url_for("auth.login"))
        return jsonify(error="Cuenta inactiva, inexistente o sin rol válido."), 403

    if usuario["rol_codigo"] not in roles_permitidos:
        return jsonify(error="No tenés permiso para esta operación."), 403

    return None
