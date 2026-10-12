from datetime import datetime, timedelta
from decimal import Decimal

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from sqlalchemy.exc import IntegrityError

from modulos import (
    orden_compra,
    detalle_orden_compra,
    recepcion,
    detalle_recepcion,
    proveedor,
    almacen,
    producto,
    lote,
    transacciones
)


compras_bp = Blueprint(
    "compras",
    __name__,
    url_prefix="/compras"
)


# Valores de estado (ajustarlos a los que se usen en la BD)
ACTIVO = "activo"
INACTIVO = "inactivo"
OC_PENDIENTE = "pendiente"
OC_RECIBIDA = "recibida"
OC_CANCELADA = "cancelada"


# ---------- AYUDAS INTERNAS ----------

def _texto(nombre):
    # Texto del formulario; vacio -> None
    valor = (request.form.get(nombre) or "").strip()
    return valor or None


def _lineas_form(campos):
    # Los formularios envian cada columna de las lineas con el mismo name
    # (varios <input name="cantidad">): getlist las devuelve en orden.
    columnas = [request.form.getlist(c) for c in campos]
    lineas = []
    for fila in zip(*columnas):
        linea = dict(zip(campos, [x.strip() for x in fila]))
        if linea["producto_id"]:
            lineas.append(linea)
    return lineas


def _lineas_orden():
    # Campos: producto_id, cantidad, costo_unitario. Devuelve None si algo es invalido
    try:
        lineas = [
            {
                "producto_id": int(l["producto_id"]),
                "cantidad": Decimal(l["cantidad"]),
                "costo_unitario": Decimal(l["costo_unitario"])
            }
            for l in _lineas_form(["producto_id", "cantidad", "costo_unitario"])
        ]
    except (ValueError, ArithmeticError):
        return None

    if not lineas:
        return None
    if any(l["cantidad"] <= 0 or l["costo_unitario"] < 0 for l in lineas):
        return None

    return lineas


def _orden_o_404(orden_id):
    orden = orden_compra.obtener_un_orden_compra(orden_id)
    if orden is None:
        abort(404)
    return orden


def _proveedor_activo(proveedor_id):
    prov = proveedor.obtener_un_proveedor(proveedor_id) if proveedor_id else None
    if prov is None or prov.persona_estado != ACTIVO:
        return None
    return prov


def _obtener_o_crear_lote(codigo, producto_id):
    # Si la linea trae codigo de lote: usa el existente o lo crea
    if not codigo:
        return None

    existente = lote.obtener_lote_por_codigo(codigo)
    if existente is not None:
        if existente.producto_id != producto_id:
            raise ValueError("El lote " + codigo + " pertenece a otro producto")
        return existente.id_lote

    ahora = datetime.now()
    return lote.insertar_lote(codigo, ahora, ahora, producto_id)


# ÓRDENES DE COMPRA

@compras_bp.route("/ordenes")
def ordenes():
    estado = request.args.get("estado")

    if estado:
        lista = orden_compra.obtener_ordenes_compra_por_estado(estado)
    else:
        lista = orden_compra.obtener_ordenes_compra()

    return render_template(
        "compras/ordenes/index.html",
        ordenes=lista,
        estado=estado
    )


@compras_bp.route("/ordenes/nueva", methods=["GET", "POST"])
def orden_nueva():
    # Form: proveedor_id + lineas (producto_id, cantidad, costo_unitario repetidos)
    if request.method == "POST":
        proveedor_id = request.form.get("proveedor_id", type=int)
        lineas = _lineas_orden()

        if _proveedor_activo(proveedor_id) is None:
            flash("Debe elegir un proveedor activo", "error")
        elif lineas is None:
            flash("La orden necesita al menos un producto con cantidad y costo válidos", "error")
        else:
            try:
                orden_id = transacciones.crear_orden_compra(
                    proveedor_id, lineas, OC_PENDIENTE, datetime.now()
                )
            except (ValueError, IntegrityError) as e:
                flash("No se pudo crear la orden: " + str(e), "error")
            else:
                flash("Orden de compra creada", "exito")
                return redirect(url_for("compras.orden_detalle", orden_id=orden_id))

        return redirect(url_for("compras.orden_nueva"))

    return render_template(
        "compras/ordenes/form.html",
        orden=None,
        proveedores=proveedor.obtener_proveedores_por_estado(ACTIVO),
        productos=producto.obtener_productos_por_estado(ACTIVO)
    )


@compras_bp.route("/ordenes/<int:orden_id>")
def orden_detalle(orden_id):
    orden = _orden_o_404(orden_id)

    return render_template(
        "compras/ordenes/detail.html",
        orden_id=orden_id,
        orden=orden,
        detalles=detalle_orden_compra.obtener_detalles_orden_compra_por_ordenc(orden_id),
        total=orden_compra.obtener_total_orden_compra(orden_id),
        recepciones=recepcion.obtener_recepciones_por_ordenc(orden_id),
        productos=producto.obtener_productos_por_estado(ACTIVO),
        editable=(orden.estado == OC_PENDIENTE)
    )


@compras_bp.route("/ordenes/<int:orden_id>/editar", methods=["GET", "POST"])
def orden_editar(orden_id):
    # Solo se cambia el proveedor; las lineas se agregan o editan desde el detalle
    orden = _orden_o_404(orden_id)

    if orden.estado != OC_PENDIENTE:
        flash("Solo se puede editar una orden pendiente", "error")
        return redirect(url_for("compras.orden_detalle", orden_id=orden_id))

    if request.method == "POST":
        proveedor_id = request.form.get("proveedor_id", type=int)

        if _proveedor_activo(proveedor_id) is None:
            flash("Debe elegir un proveedor activo", "error")
            return redirect(url_for("compras.orden_editar", orden_id=orden_id))

        orden_compra.actualizar_orden_compra(
            orden_id, orden.estado, datetime.now(), proveedor_id
        )
        flash("Orden actualizada", "exito")
        return redirect(url_for("compras.orden_detalle", orden_id=orden_id))

    return render_template(
        "compras/ordenes/form.html",
        orden=orden,
        proveedores=proveedor.obtener_proveedores_por_estado(ACTIVO),
        productos=[]
    )


@compras_bp.route("/ordenes/<int:orden_id>/baja", methods=["POST"])
def orden_baja(orden_id):
    orden = _orden_o_404(orden_id)

    if orden.estado == OC_RECIBIDA:
        flash("No se puede dar de baja una orden ya recibida", "error")
    else:
        orden_compra.actualizar_estado_orden_compra(orden_id, OC_CANCELADA, datetime.now())
        flash("Orden dada de baja", "exito")

    return redirect(url_for("compras.orden_detalle", orden_id=orden_id))


# LÍNEAS DE LA ORDEN

@compras_bp.route("/ordenes/<int:orden_id>/detalles", methods=["POST"])
def orden_detalle_agregar(orden_id):
    # Form: producto_id, cantidad, costo_unitario
    orden = _orden_o_404(orden_id)
    lineas = _lineas_orden()

    if orden.estado != OC_PENDIENTE:
        flash("Solo se puede modificar una orden pendiente", "error")
    elif lineas is None:
        flash("Producto, cantidad o costo inválidos", "error")
    else:
        for l in lineas:
            detalle_orden_compra.insertar_detalle_orden_compra(
                orden_id, l["producto_id"], l["cantidad"], l["costo_unitario"]
            )
        flash("Línea agregada", "exito")

    return redirect(url_for("compras.orden_detalle", orden_id=orden_id))


@compras_bp.route("/detalles/<int:detalle_id>/actualizar", methods=["POST"])
def orden_detalle_actualizar(detalle_id):
    # Form: cantidad, costo_unitario
    detalle = detalle_orden_compra.obtener_un_detalle_orden_compra(detalle_id)
    if detalle is None:
        abort(404)

    orden = _orden_o_404(detalle.ordenc_id)

    try:
        cantidad = Decimal(request.form.get("cantidad", ""))
        costo = Decimal(request.form.get("costo_unitario", ""))
        valido = cantidad > 0 and costo >= 0
    except ArithmeticError:
        valido = False

    if orden.estado != OC_PENDIENTE:
        flash("Solo se puede modificar una orden pendiente", "error")
    elif not valido:
        flash("Cantidad o costo inválidos", "error")
    else:
        detalle_orden_compra.actualizar_detalle_orden_compra(
            detalle_id, detalle.ordenc_id, detalle.producto_id, cantidad, costo
        )
        flash("Línea actualizada", "exito")

    return redirect(url_for("compras.orden_detalle", orden_id=detalle.ordenc_id))


@compras_bp.route("/detalles/<int:detalle_id>/eliminar", methods=["POST"])
def orden_detalle_eliminar(detalle_id):
    detalle = detalle_orden_compra.obtener_un_detalle_orden_compra(detalle_id)
    if detalle is None:
        abort(404)

    orden = _orden_o_404(detalle.ordenc_id)

    if orden.estado != OC_PENDIENTE:
        flash("Solo se puede modificar una orden pendiente", "error")
    else:
        detalle_orden_compra.eliminar_detalle_orden_compra(detalle_id)
        flash("Línea eliminada", "exito")

    return redirect(url_for("compras.orden_detalle", orden_id=detalle.ordenc_id))


# PROVEEDORES

@compras_bp.route("/proveedores")
def proveedores():
    estado = request.args.get("estado")

    if estado:
        lista = proveedor.obtener_proveedores_por_estado(estado)
    else:
        lista = proveedor.obtener_proveedores()

    return render_template(
        "compras/proveedores/index.html",
        proveedores=lista,
        estado=estado
    )


@compras_bp.route("/proveedores/nuevo", methods=["GET", "POST"])
def proveedor_nuevo():
    # Form: codigo, empresa, nombre_1, nombre_2, apellido_1, apellido_2, correo, telefono
    if request.method == "POST":
        codigo = _texto("codigo")
        empresa = _texto("empresa")
        nombre_1 = _texto("nombre_1")
        apellido_1 = _texto("apellido_1")
        correo = _texto("correo")

        if not (codigo and empresa and nombre_1 and apellido_1 and correo):
            flash("Complete código, empresa, primer nombre, primer apellido y correo", "error")
        elif proveedor.obtener_proveedor_por_codigo(codigo) is not None:
            flash("Ya existe un proveedor con ese código", "error")
        else:
            try:
                proveedor_id = transacciones.crear_proveedor(
                    codigo, empresa, nombre_1, _texto("nombre_2"),
                    apellido_1, _texto("apellido_2"), correo,
                    _texto("telefono"), ACTIVO, datetime.now()
                )
            except IntegrityError:
                flash("Ya existe una persona con ese correo", "error")
            else:
                flash("Proveedor creado", "exito")
                return redirect(url_for("compras.proveedores"))

        return redirect(url_for("compras.proveedor_nuevo"))

    return render_template(
        "compras/proveedores/form.html",
        proveedor=None
    )


@compras_bp.route("/proveedores/<int:proveedor_id>/editar", methods=["GET", "POST"])
def proveedor_editar(proveedor_id):
    prov = proveedor.obtener_un_proveedor(proveedor_id)
    if prov is None:
        abort(404)

    if request.method == "POST":
        codigo = _texto("codigo")
        empresa = _texto("empresa")
        nombre_1 = _texto("nombre_1")
        apellido_1 = _texto("apellido_1")
        correo = _texto("correo")

        otro = proveedor.obtener_proveedor_por_codigo(codigo) if codigo else None

        if not (codigo and empresa and nombre_1 and apellido_1 and correo):
            flash("Complete código, empresa, primer nombre, primer apellido y correo", "error")
        elif otro is not None and otro.id_proveedor != proveedor_id:
            flash("Ya existe un proveedor con ese código", "error")
        else:
            try:
                transacciones.editar_proveedor(
                    proveedor_id, codigo, empresa, nombre_1, _texto("nombre_2"),
                    apellido_1, _texto("apellido_2"), correo,
                    _texto("telefono"), datetime.now()
                )
            except IntegrityError:
                flash("Ya existe una persona con ese correo", "error")
            else:
                flash("Proveedor actualizado", "exito")
                return redirect(url_for("compras.proveedores"))

        return redirect(url_for("compras.proveedor_editar", proveedor_id=proveedor_id))

    return render_template(
        "compras/proveedores/form.html",
        proveedor=prov
    )


@compras_bp.route("/proveedores/<int:proveedor_id>/baja", methods=["POST"])
def proveedor_baja(proveedor_id):
    if proveedor.obtener_un_proveedor(proveedor_id) is None:
        abort(404)

    proveedor.dar_de_baja_proveedor(proveedor_id, INACTIVO, datetime.now())
    flash("Proveedor dado de baja", "exito")

    return redirect(url_for("compras.proveedores"))


# RECEPCIONES

@compras_bp.route("/recepciones")
def recepciones():
    orden_id = request.args.get("orden_id", type=int)
    estado = request.args.get("estado")

    if orden_id:
        lista = recepcion.obtener_recepciones_por_ordenc(orden_id)
    elif estado:
        lista = recepcion.obtener_recepciones_por_estado(estado)
    else:
        lista = recepcion.obtener_recepciones()

    return render_template(
        "compras/recepciones/index.html",
        recepciones=lista
    )


@compras_bp.route("/recepciones/nueva", methods=["GET", "POST"])
def recepcion_nueva():
    # Form: ordenc_id, almacen_id, codigo + lineas (producto_id, lote_codigo, cantidad repetidos)
    # Al guardar: se crea la recepcion, se suma al inventario y la orden pasa a "recibida"
    if request.method == "POST":
        ordenc_id = request.form.get("ordenc_id", type=int)
        almacen_id = request.form.get("almacen_id", type=int)
        codigo = _texto("codigo")

        orden = orden_compra.obtener_un_orden_compra(ordenc_id) if ordenc_id else None
        alm = almacen.obtener_un_almacen(almacen_id) if almacen_id else None

        try:
            lineas = [
                {
                    "producto_id": int(l["producto_id"]),
                    "lote_codigo": l["lote_codigo"] or None,
                    "cantidad": Decimal(l["cantidad"])
                }
                for l in _lineas_form(["producto_id", "lote_codigo", "cantidad"])
            ]
        except (ValueError, ArithmeticError):
            lineas = []

        if orden is None or orden.estado != OC_PENDIENTE:
            flash("Debe elegir una orden de compra pendiente", "error")
        elif alm is None or alm.estado != ACTIVO:
            flash("Debe elegir un almacén activo", "error")
        elif not codigo:
            flash("Indique el código de la recepción", "error")
        elif recepcion.obtener_recepcion_por_codigo(codigo) is not None:
            flash("Ya existe una recepción con ese código", "error")
        elif not lineas or any(l["cantidad"] <= 0 for l in lineas):
            flash("Agregue al menos un producto con cantidad válida", "error")
        else:
            try:
                detalles = [
                    {
                        "producto_id": l["producto_id"],
                        "lote_id": _obtener_o_crear_lote(l["lote_codigo"], l["producto_id"]),
                        "cantidad": l["cantidad"]
                    }
                    for l in lineas
                ]
                recepcion_id = transacciones.registrar_recepcion(
                    ordenc_id, almacen_id, codigo, detalles,
                    datetime.now(), ACTIVO, OC_RECIBIDA
                )
            except (ValueError, IntegrityError) as e:
                flash("No se pudo registrar la recepción: " + str(e), "error")
            else:
                flash("Recepción registrada", "exito")
                return redirect(url_for("compras.recepcion_detalle", recepcion_id=recepcion_id))

        return redirect(url_for("compras.recepcion_nueva", orden_id=ordenc_id))

    # GET: si viene ?orden_id=, se precargan los productos de esa orden
    orden_id = request.args.get("orden_id", type=int)
    orden = orden_compra.obtener_un_orden_compra(orden_id) if orden_id else None

    return render_template(
        "compras/recepciones/form.html",
        recepcion=None,
        orden=orden,
        detalles_orden=(
            detalle_orden_compra.obtener_detalles_orden_compra_por_ordenc(orden_id)
            if orden else []
        ),
        ordenes_pendientes=orden_compra.obtener_ordenes_compra_por_estado(OC_PENDIENTE),
        almacenes=almacen.obtener_almacenes_por_estado(ACTIVO)
    )


@compras_bp.route("/recepciones/<int:recepcion_id>")
def recepcion_detalle(recepcion_id):
    rec = recepcion.obtener_un_recepcion(recepcion_id)
    if rec is None:
        abort(404)

    return render_template(
        "compras/recepciones/detail.html",
        recepcion=rec,
        detalles=detalle_recepcion.obtener_detalles_recepcion_por_recepcion(recepcion_id)
    )


@compras_bp.route("/recepciones/<int:recepcion_id>/editar", methods=["GET", "POST"])
def recepcion_editar(recepcion_id):
    # Solo se permite cambiar el codigo: cambiar orden o almacen descuadraria el inventario
    rec = recepcion.obtener_un_recepcion(recepcion_id)
    if rec is None:
        abort(404)

    if request.method == "POST":
        codigo = _texto("codigo")
        otra = recepcion.obtener_recepcion_por_codigo(codigo) if codigo else None

        if not codigo:
            flash("Indique el código de la recepción", "error")
        elif otra is not None and otra.id_recepcion != recepcion_id:
            flash("Ya existe una recepción con ese código", "error")
        else:
            recepcion.actualizar_recepcion(
                recepcion_id, codigo, datetime.now(),
                rec.ordenc_id, rec.almacen_id, rec.estado
            )
            flash("Recepción actualizada", "exito")
            return redirect(url_for("compras.recepcion_detalle", recepcion_id=recepcion_id))

        return redirect(url_for("compras.recepcion_editar", recepcion_id=recepcion_id))

    return render_template(
        "compras/recepciones/form.html",
        recepcion=rec,
        orden=None,
        detalles_orden=[],
        ordenes_pendientes=[],
        almacenes=[]
    )


@compras_bp.route("/recepciones/<int:recepcion_id>/baja", methods=["POST"])
def recepcion_baja(recepcion_id):
    # La baja es logica y NO revierte lo que ya entro al inventario
    if recepcion.obtener_un_recepcion(recepcion_id) is None:
        abort(404)

    recepcion.actualizar_estado_recepcion(recepcion_id, INACTIVO, datetime.now())
    flash("Recepción dada de baja", "exito")

    return redirect(url_for("compras.recepciones"))


# REPORTE

@compras_bp.route("/reporte")
def reporte():
    # /compras/reporte?inicio=2026-10-01&fin=2026-10-31
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
            filas = orden_compra.obtener_reporte_compras(desde, hasta)
            total_general = sum(f.total for f in filas)

    return render_template(
        "compras/reporte.html",
        reporte=filas,
        total_general=total_general,
        inicio=inicio,
        fin=fin
    )