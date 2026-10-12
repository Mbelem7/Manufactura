from datetime import datetime, timedelta
from decimal import Decimal

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from sqlalchemy.exc import IntegrityError

from modulos import (
    orden_venta,
    detalle_orden_venta,
    cliente,
    despacho,
    detalle_despacho,
    producto,
    almacen,
    inventario,
    transacciones
)


ventas_bp = Blueprint(
    "ventas",
    __name__,
    url_prefix="/ventas"
)


# Valores de estado y tipo (ajustarlos a los que se usen en la BD)
ACTIVO = "activo"
INACTIVO = "inactivo"
TIPO_PRODUCTO_TERMINADO = "producto_terminado"
OV_PENDIENTE = "pendiente"
OV_DESPACHADA = "despachada"
OV_CANCELADA = "cancelada"
DESP_DESPACHADO = "despachado"


# ---------- AYUDAS INTERNAS ----------

def _texto(nombre):
    # Texto del formulario; vacio -> None
    valor = (request.form.get(nombre) or "").strip()
    return valor or None


def _decimal(texto, permitir_cero=False):
    # Texto -> Decimal (mayor a 0, o mayor o igual a 0 si permitir_cero); invalido -> None
    try:
        valor = Decimal((texto or "").strip())
        if not valor.is_finite():
            return None
        if valor < 0 or (valor == 0 and not permitir_cero):
            return None
    except ArithmeticError:
        return None
    return valor


def _lineas_form(campos):
    # Los formularios envian cada columna de las lineas con el mismo name
    # (varios <input name="cantidad">): getlist las devuelve en orden.
    # La primera columna decide si la fila esta vacia.
    columnas = [request.form.getlist(c) for c in campos]
    lineas = []
    for fila in zip(*columnas):
        linea = dict(zip(campos, [x.strip() for x in fila]))
        if linea[campos[0]]:
            lineas.append(linea)
    return lineas


def _lineas_orden():
    # Campos: producto_id, cantidad, precio_unitario. Devuelve None si algo es invalido
    lineas = []

    try:
        for l in _lineas_form(["producto_id", "cantidad", "precio_unitario"]):
            cantidad = _decimal(l["cantidad"])
            precio = _decimal(l["precio_unitario"], permitir_cero=True)
            if cantidad is None or precio is None:
                return None
            lineas.append({
                "producto_id": int(l["producto_id"]),
                "cantidad": cantidad,
                "precio_unitario": precio
            })
    except ValueError:
        return None

    return lineas or None


def _lineas_despacho():
    # Campos: lote_id, cantidad. Devuelve None si algo es invalido
    lineas = []

    try:
        for l in _lineas_form(["lote_id", "cantidad"]):
            cantidad = _decimal(l["cantidad"])
            if cantidad is None:
                return None
            lineas.append({"lote_id": int(l["lote_id"]), "cantidad": cantidad})
    except ValueError:
        return None

    return lineas or None


def _productos_terminados():
    return [
        p for p in producto.obtener_productos_por_estado(ACTIVO)
        if p.tipo_producto == TIPO_PRODUCTO_TERMINADO
    ]


def _orden_o_404(orden_id):
    orden = orden_venta.obtener_un_orden_venta(orden_id)
    if orden is None:
        abort(404)
    return orden


def _cliente_activo(cliente_id):
    cli = cliente.obtener_un_cliente(cliente_id) if cliente_id else None
    if cli is None or cli.persona_estado != ACTIVO:
        return None
    return cli


def _error_despacho(ordenv_id, almacen_id, lineas):
    # Revisa que lo que se despacha exista en el almacen y coincida con lo ordenado.
    # Devuelve el mensaje de error, o None si todo esta bien.
    disponibles = {}
    for f in inventario.obtener_inventario_por_almacen(almacen_id):
        if f.lote_id:
            disponibles[f.lote_id] = (f.producto_id, f.cantidad)

    por_lote = {}
    for l in lineas:
        por_lote[l["lote_id"]] = por_lote.get(l["lote_id"], Decimal("0")) + l["cantidad"]

    por_producto = {}
    for lote_id, cantidad in por_lote.items():
        if lote_id not in disponibles:
            return "El lote " + str(lote_id) + " no tiene existencias en ese almacén"

        producto_id, existencia = disponibles[lote_id]

        if cantidad > existencia:
            return "Existencia insuficiente en el lote " + str(lote_id)

        por_producto[producto_id] = por_producto.get(producto_id, Decimal("0")) + cantidad

    ordenado = {}
    for d in detalle_orden_venta.obtener_detalles_orden_venta_por_ordenv(ordenv_id):
        ordenado[d.producto_id] = ordenado.get(d.producto_id, Decimal("0")) + d.cantidad

    # Se despacha la orden completa de una vez (quitar esta comparacion para permitir parciales)
    if por_producto != ordenado:
        return "Debe despachar exactamente la cantidad ordenada de cada producto"

    return None


# ÓRDENES DE VENTA

@ventas_bp.route("/ordenes")
def ordenes():
    estado = request.args.get("estado")
    cliente_id = request.args.get("cliente_id", type=int)

    if estado:
        lista = orden_venta.obtener_ordenes_venta_por_estado(estado)
    elif cliente_id:
        lista = orden_venta.obtener_ordenes_venta_por_cliente(cliente_id)
    else:
        lista = orden_venta.obtener_ordenes_venta()

    return render_template(
        "ventas/ordenes/index.html",
        ordenes=lista,
        estado=estado
    )


@ventas_bp.route("/ordenes/nueva", methods=["GET", "POST"])
def orden_nueva():
    # Form: cliente_id + lineas (producto_id, cantidad, precio_unitario repetidos)
    if request.method == "POST":
        cliente_id = request.form.get("cliente_id", type=int)
        lineas = _lineas_orden()

        if _cliente_activo(cliente_id) is None:
            flash("Debe elegir un cliente activo", "error")
        elif lineas is None:
            flash("La orden necesita al menos un producto con cantidad y precio válidos", "error")
        elif any(l["producto_id"] not in {p.id_producto for p in _productos_terminados()} for l in lineas):
            flash("Solo se pueden vender productos terminados activos", "error")
        else:
            try:
                orden_id = transacciones.crear_orden_venta(
                    cliente_id, lineas, OV_PENDIENTE, datetime.now()
                )
            except (ValueError, IntegrityError) as e:
                flash("No se pudo crear la orden: " + str(e), "error")
            else:
                flash("Orden de venta creada", "exito")
                return redirect(url_for("ventas.orden_detalle", orden_id=orden_id))

        return redirect(url_for("ventas.orden_nueva"))

    return render_template(
        "ventas/ordenes/form.html",
        orden=None,
        clientes=cliente.obtener_clientes_por_estado(ACTIVO),
        productos=_productos_terminados()
    )


@ventas_bp.route("/ordenes/<int:orden_id>")
def orden_detalle(orden_id):
    orden = _orden_o_404(orden_id)

    return render_template(
        "ventas/ordenes/detail.html",
        orden_id=orden_id,
        orden=orden,
        detalles=detalle_orden_venta.obtener_detalles_orden_venta_por_ordenv(orden_id),
        total=orden_venta.obtener_total_orden_venta(orden_id),
        despachos=despacho.obtener_despachos_por_ordenv(orden_id),
        # existencia actual de cada producto, para ver si alcanza para despachar
        stock={f.id_producto: f.stock_actual for f in inventario.obtener_stock_actual()},
        productos=_productos_terminados(),
        editable=(orden.estado == OV_PENDIENTE)
    )


@ventas_bp.route("/ordenes/<int:orden_id>/editar", methods=["GET", "POST"])
def orden_editar(orden_id):
    # Solo se cambia el cliente; las lineas se agregan, editan o eliminan desde el detalle
    orden = _orden_o_404(orden_id)

    if orden.estado != OV_PENDIENTE:
        flash("Solo se puede editar una orden pendiente", "error")
        return redirect(url_for("ventas.orden_detalle", orden_id=orden_id))

    if request.method == "POST":
        cliente_id = request.form.get("cliente_id", type=int)

        if _cliente_activo(cliente_id) is None:
            flash("Debe elegir un cliente activo", "error")
            return redirect(url_for("ventas.orden_editar", orden_id=orden_id))

        orden_venta.actualizar_orden_venta(orden_id, orden.estado, datetime.now(), cliente_id)
        flash("Orden actualizada", "exito")
        return redirect(url_for("ventas.orden_detalle", orden_id=orden_id))

    return render_template(
        "ventas/ordenes/form.html",
        orden=orden,
        clientes=cliente.obtener_clientes_por_estado(ACTIVO),
        productos=[]
    )


@ventas_bp.route("/ordenes/<int:orden_id>/baja", methods=["POST"])
def orden_baja(orden_id):
    orden = _orden_o_404(orden_id)

    if orden.estado == OV_DESPACHADA:
        flash("No se puede dar de baja una orden ya despachada", "error")
    else:
        orden_venta.actualizar_estado_orden_venta(orden_id, OV_CANCELADA, datetime.now())
        flash("Orden dada de baja", "exito")

    return redirect(url_for("ventas.orden_detalle", orden_id=orden_id))


# LÍNEAS DE LA ORDEN

@ventas_bp.route("/ordenes/<int:orden_id>/detalles", methods=["POST"])
def orden_detalle_agregar(orden_id):
    # Form: producto_id, cantidad, precio_unitario
    orden = _orden_o_404(orden_id)
    lineas = _lineas_orden()

    if orden.estado != OV_PENDIENTE:
        flash("Solo se puede modificar una orden pendiente", "error")
    elif lineas is None:
        flash("Producto, cantidad o precio inválidos", "error")
    elif lineas[0]["producto_id"] not in {p.id_producto for p in _productos_terminados()}:
        flash("Solo se pueden vender productos terminados activos", "error")
    else:
        l = lineas[0]
        detalle_orden_venta.insertar_detalle_orden_venta(
            orden_id, l["producto_id"], l["cantidad"], l["precio_unitario"]
        )
        flash("Línea agregada", "exito")

    return redirect(url_for("ventas.orden_detalle", orden_id=orden_id))


@ventas_bp.route("/detalles/<int:detalle_id>/actualizar", methods=["POST"])
def orden_detalle_actualizar(detalle_id):
    # Form: cantidad, precio_unitario
    detalle = detalle_orden_venta.obtener_un_detalle_orden_venta(detalle_id)
    if detalle is None:
        abort(404)

    orden = _orden_o_404(detalle.ordenv_id)
    cantidad = _decimal(request.form.get("cantidad"))
    precio = _decimal(request.form.get("precio_unitario"), permitir_cero=True)

    if orden.estado != OV_PENDIENTE:
        flash("Solo se puede modificar una orden pendiente", "error")
    elif cantidad is None or precio is None:
        flash("Cantidad o precio inválidos", "error")
    else:
        detalle_orden_venta.actualizar_detalle_orden_venta(
            detalle_id, detalle.ordenv_id, detalle.producto_id, cantidad, precio
        )
        flash("Línea actualizada", "exito")

    return redirect(url_for("ventas.orden_detalle", orden_id=detalle.ordenv_id))


@ventas_bp.route("/detalles/<int:detalle_id>/eliminar", methods=["POST"])
def orden_detalle_eliminar(detalle_id):
    detalle = detalle_orden_venta.obtener_un_detalle_orden_venta(detalle_id)
    if detalle is None:
        abort(404)

    orden = _orden_o_404(detalle.ordenv_id)

    if orden.estado != OV_PENDIENTE:
        flash("Solo se puede modificar una orden pendiente", "error")
    else:
        detalle_orden_venta.eliminar_detalle_orden_venta(detalle_id)
        flash("Línea eliminada", "exito")

    return redirect(url_for("ventas.orden_detalle", orden_id=detalle.ordenv_id))


# CLIENTES

@ventas_bp.route("/clientes")
def clientes():
    estado = request.args.get("estado")

    if estado:
        lista = cliente.obtener_clientes_por_estado(estado)
    else:
        lista = cliente.obtener_clientes()

    return render_template(
        "ventas/clientes/index.html",
        clientes=lista,
        estado=estado
    )


@ventas_bp.route("/clientes/nuevo", methods=["GET", "POST"])
def cliente_nuevo():
    # Form: codigo, empresa, nombre_1, nombre_2, apellido_1, apellido_2, correo, telefono
    if request.method == "POST":
        codigo = _texto("codigo")
        empresa = _texto("empresa")
        nombre_1 = _texto("nombre_1")
        apellido_1 = _texto("apellido_1")
        correo = _texto("correo")

        if not (codigo and empresa and nombre_1 and apellido_1 and correo):
            flash("Complete código, empresa, primer nombre, primer apellido y correo", "error")
        elif cliente.obtener_cliente_por_codigo(codigo) is not None:
            flash("Ya existe un cliente con ese código", "error")
        else:
            try:
                transacciones.crear_cliente(
                    codigo, empresa, nombre_1, _texto("nombre_2"),
                    apellido_1, _texto("apellido_2"), correo,
                    _texto("telefono"), ACTIVO, datetime.now()
                )
            except IntegrityError:
                flash("Ya existe una persona con ese correo", "error")
            else:
                flash("Cliente creado", "exito")
                return redirect(url_for("ventas.clientes"))

        return redirect(url_for("ventas.cliente_nuevo"))

    return render_template(
        "ventas/clientes/form.html",
        cliente=None
    )


@ventas_bp.route("/clientes/<int:cliente_id>/editar", methods=["GET", "POST"])
def cliente_editar(cliente_id):
    cli = cliente.obtener_un_cliente(cliente_id)
    if cli is None:
        abort(404)

    if request.method == "POST":
        codigo = _texto("codigo")
        empresa = _texto("empresa")
        nombre_1 = _texto("nombre_1")
        apellido_1 = _texto("apellido_1")
        correo = _texto("correo")

        otro = cliente.obtener_cliente_por_codigo(codigo) if codigo else None

        if not (codigo and empresa and nombre_1 and apellido_1 and correo):
            flash("Complete código, empresa, primer nombre, primer apellido y correo", "error")
        elif otro is not None and otro.id_cliente != cliente_id:
            flash("Ya existe un cliente con ese código", "error")
        else:
            try:
                transacciones.editar_cliente(
                    cliente_id, codigo, empresa, nombre_1, _texto("nombre_2"),
                    apellido_1, _texto("apellido_2"), correo,
                    _texto("telefono"), datetime.now()
                )
            except IntegrityError:
                flash("Ya existe una persona con ese correo", "error")
            else:
                flash("Cliente actualizado", "exito")
                return redirect(url_for("ventas.clientes"))

        return redirect(url_for("ventas.cliente_editar", cliente_id=cliente_id))

    return render_template(
        "ventas/clientes/form.html",
        cliente=cli
    )


@ventas_bp.route("/clientes/<int:cliente_id>/baja", methods=["POST"])
def cliente_baja(cliente_id):
    if cliente.obtener_un_cliente(cliente_id) is None:
        abort(404)

    cliente.dar_de_baja_cliente(cliente_id, INACTIVO, datetime.now())
    flash("Cliente dado de baja", "exito")

    return redirect(url_for("ventas.clientes"))


# DESPACHOS

@ventas_bp.route("/despachos")
def despachos():
    orden_id = request.args.get("orden_id", type=int)
    estado = request.args.get("estado")

    if orden_id:
        lista = despacho.obtener_despachos_por_ordenv(orden_id)
    elif estado:
        lista = despacho.obtener_despachos_por_estado(estado)
    else:
        lista = despacho.obtener_despachos()

    return render_template(
        "ventas/despachos/index.html",
        despachos=lista
    )


@ventas_bp.route("/despachos/nuevo", methods=["GET", "POST"])
def despacho_nuevo():
    # Form: ordenv_id, almacen_id, codigo + lineas (lote_id, cantidad repetidos)
    # Al guardar: se crea el despacho, se resta del inventario y la orden pasa a "despachada"
    if request.method == "POST":
        ordenv_id = request.form.get("ordenv_id", type=int)
        almacen_id = request.form.get("almacen_id", type=int)
        codigo = _texto("codigo")
        lineas = _lineas_despacho()

        orden = orden_venta.obtener_un_orden_venta(ordenv_id) if ordenv_id else None
        alm = almacen.obtener_un_almacen(almacen_id) if almacen_id else None

        if orden is None or orden.estado != OV_PENDIENTE:
            flash("Debe elegir una orden de venta pendiente", "error")
        elif alm is None or alm.estado != ACTIVO:
            flash("Debe elegir un almacén activo", "error")
        elif not codigo:
            flash("Indique el código del despacho", "error")
        elif despacho.obtener_despacho_por_codigo(codigo) is not None:
            flash("Ya existe un despacho con ese código", "error")
        elif lineas is None:
            flash("Agregue al menos un lote con cantidad válida", "error")
        else:
            mensaje = _error_despacho(ordenv_id, almacen_id, lineas)

            if mensaje:
                flash(mensaje, "error")
            else:
                try:
                    despacho_id = transacciones.registrar_despacho(
                        ordenv_id, almacen_id, codigo, lineas,
                        datetime.now(), DESP_DESPACHADO, OV_DESPACHADA
                    )
                except (ValueError, IntegrityError) as e:
                    flash("No se pudo registrar el despacho: " + str(e), "error")
                else:
                    flash("Despacho registrado", "exito")
                    return redirect(url_for("ventas.despacho_detalle", despacho_id=despacho_id))

        return redirect(url_for("ventas.despacho_nuevo", orden_id=ordenv_id, almacen_id=almacen_id))

    # GET: ?orden_id= precarga lo ordenado; ?almacen_id= muestra los lotes con existencia ahi
    orden_id = request.args.get("orden_id", type=int)
    almacen_id = request.args.get("almacen_id", type=int)
    orden = orden_venta.obtener_un_orden_venta(orden_id) if orden_id else None

    lotes_disponibles = []
    if almacen_id:
        lotes_disponibles = [
            f for f in inventario.obtener_inventario_por_almacen(almacen_id)
            if f.lote_id and f.cantidad > 0
        ]

    return render_template(
        "ventas/despachos/form.html",
        despacho=None,
        orden=orden,
        detalles_orden=(
            detalle_orden_venta.obtener_detalles_orden_venta_por_ordenv(orden_id)
            if orden else []
        ),
        ordenes_pendientes=orden_venta.obtener_ordenes_venta_por_estado(OV_PENDIENTE),
        almacenes=almacen.obtener_almacenes_por_estado(ACTIVO),
        almacen_id=almacen_id,
        lotes_disponibles=lotes_disponibles
    )


@ventas_bp.route("/despachos/<int:despacho_id>")
def despacho_detalle(despacho_id):
    desp = despacho.obtener_un_despacho(despacho_id)
    if desp is None:
        abort(404)

    return render_template(
        "ventas/despachos/detail.html",
        despacho=desp,
        detalles=detalle_despacho.obtener_detalles_despacho_por_despacho(despacho_id)
    )


@ventas_bp.route("/despachos/<int:despacho_id>/editar", methods=["GET", "POST"])
def despacho_editar(despacho_id):
    # Solo se permite cambiar el codigo: cambiar orden o almacen descuadraria el inventario
    desp = despacho.obtener_un_despacho(despacho_id)
    if desp is None:
        abort(404)

    if request.method == "POST":
        codigo = _texto("codigo")
        otro = despacho.obtener_despacho_por_codigo(codigo) if codigo else None

        if not codigo:
            flash("Indique el código del despacho", "error")
        elif otro is not None and otro.id_despacho != despacho_id:
            flash("Ya existe un despacho con ese código", "error")
        else:
            despacho.actualizar_despacho(
                despacho_id, codigo, desp.estado, datetime.now(),
                desp.ordenv_id, desp.almacen_id
            )
            flash("Despacho actualizado", "exito")
            return redirect(url_for("ventas.despacho_detalle", despacho_id=despacho_id))

        return redirect(url_for("ventas.despacho_editar", despacho_id=despacho_id))

    return render_template(
        "ventas/despachos/form.html",
        despacho=desp,
        orden=None,
        detalles_orden=[],
        ordenes_pendientes=[],
        almacenes=[],
        almacen_id=None,
        lotes_disponibles=[]
    )


@ventas_bp.route("/despachos/<int:despacho_id>/baja", methods=["POST"])
def despacho_baja(despacho_id):
    # La baja es logica y NO devuelve al inventario lo que ya salio
    if despacho.obtener_un_despacho(despacho_id) is None:
        abort(404)

    despacho.actualizar_estado_despacho(despacho_id, INACTIVO, datetime.now())
    flash("Despacho dado de baja", "exito")

    return redirect(url_for("ventas.despachos"))


# REPORTE

@ventas_bp.route("/reporte")
def reporte():
    # /ventas/reporte?inicio=2026-10-01&fin=2026-10-31
    inicio = request.args.get("inicio")
    fin = request.args.get("fin")
    filas = []
    total_general = 0

    if inicio and fin:
        try:
            desde = datetime.strptime(inicio, "%Y-%m-%d")
            hasta = datetime.strptime(fin, "%Y-%m-%d") + timedelta(days=1)
        except ValueError:
            flash("Use fechas con formato AAAA-MM-DD", "error")
        else:
            filas = orden_venta.obtener_reporte_ventas(desde, hasta)
            total_general = sum(f.total for f in filas)

    return render_template(
        "ventas/reporte.html",
        reporte=filas,
        total_general=total_general,
        inicio=inicio,
        fin=fin
    )