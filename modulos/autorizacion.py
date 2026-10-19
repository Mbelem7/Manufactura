"""Autorización centralizada por roles para Manufactura (Flask).

Roles habilitados:
- administrador: acceso a todas las operaciones actuales del ERP, incluidas las de usuarios.
- operador: acceso a operaciones de inventario, producción, compras, ventas y reportes,
  pero NO a la administración de usuarios o configuración.

La calidad aún no tiene endpoints de inspección / liberación en este proyecto.
Cualquier endpoint nuevo permanece bloqueado hasta registrar su política.
"""

from flask import jsonify, request, session
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
""", escribir=AMBOS)

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
        return jsonify(error="Iniciá sesión para continuar."), 401

    usuario = obtener_usuario_actual()  # Consulta usuario, persona y rol activos en BD.
    if usuario is None:
        session.clear()
        return jsonify(error="Cuenta inactiva, inexistente o sin rol válido."), 403

    if usuario["rol_codigo"] not in roles_permitidos:
        return jsonify(error="No tenés permiso para esta operación."), 403

    return None
