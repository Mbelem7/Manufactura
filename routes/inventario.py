from datetime import datetime
from decimal import Decimal

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort

from modulos import (
    producto,
    almacen,
    lote,
    inventario
)


inventario_bp = Blueprint(
    "inventario",
    __name__,
    url_prefix="/inventario"
)


# Valores de estado y tipo (ajustarlos a los que se usen en la BD)
ACTIVO = "activo"
INACTIVO = "inactivo"
TIPOS_PRODUCTO = ("materia_prima", "producto_terminado")


# ---------- AYUDAS INTERNAS ----------

def _texto(nombre):
    # Texto del formulario; vacio -> None
    valor = (request.form.get(nombre) or "").strip()
    return valor or None


def _numero(nombre):
    # Numero del formulario: vacio -> 0; invalido o negativo -> None
    texto = (request.form.get(nombre) or "").strip()
    if not texto:
        return Decimal("0")

    try:
        valor = Decimal(texto)
        if not valor.is_finite() or valor < 0:
            return None
    except ArithmeticError:
        return None

    return valor


def _datos_producto():
    # Lee y valida el formulario de producto; si algo falla avisa y devuelve None
    datos = {
        "codigo": _texto("codigo"),
        "nombre": _texto("nombre"),
        "descripcion": _texto("descripcion"),
        "tipo_producto": _texto("tipo_producto"),
        "presentacion": _texto("presentacion"),
        "unidad_medida": _texto("unidad_medida"),
        "precio": _numero("precio"),
        "costo": _numero("costo")
    }

    if not (datos["codigo"] and datos["nombre"] and datos["unidad_medida"]):
        flash("Complete código, nombre y unidad de medida", "error")
        return None

    if datos["tipo_producto"] not in TIPOS_PRODUCTO:
        flash("Elija si es materia prima o producto terminado", "error")
        return None

    if datos["precio"] is None or datos["costo"] is None:
        flash("Precio y costo deben ser números mayores o iguales a 0", "error")
        return None

    return datos


def _datos_almacen():
    datos = {
        "codigo": _texto("codigo"),
        "nombre": _texto("nombre"),
        "tipo": _texto("tipo"),
        "ubicacion": _texto("ubicacion")
    }

    if not (datos["codigo"] and datos["nombre"]):
        flash("Complete código y nombre", "error")
        return None

    return datos


# PRODUCTOS

@inventario_bp.route("/productos")
def productos():
    estado = request.args.get("estado")
    tipo = request.args.get("tipo")

    if estado:
        lista = producto.obtener_productos_por_estado(estado)
    else:
        lista = producto.obtener_productos()

    if tipo:
        lista = [p for p in lista if p.tipo_producto == tipo]

    return render_template(
        "inventario/productos/index.html",
        productos=lista,
        estado=estado,
        tipo=tipo,
        tipos=TIPOS_PRODUCTO
    )


@inventario_bp.route("/productos/nuevo", methods=["GET", "POST"])
def producto_nuevo():
    # Form: codigo, nombre, descripcion, tipo_producto, presentacion, unidad_medida, precio, costo
    if request.method == "POST":
        datos = _datos_producto()

        if datos is not None:
            if producto.obtener_producto_por_codigo(datos["codigo"]) is not None:
                flash("Ya existe un producto con ese código", "error")
            else:
                ahora = datetime.now()
                producto.insertar_producto(
                    estado=ACTIVO,
                    fecha_creacion=ahora,
                    fecha_modificacion=ahora,
                    **datos
                )
                flash("Producto creado", "exito")
                return redirect(url_for("inventario.productos"))

        return redirect(url_for("inventario.producto_nuevo"))

    return render_template(
        "inventario/productos/form.html",
        producto=None,
        tipos=TIPOS_PRODUCTO
    )


@inventario_bp.route("/productos/<int:producto_id>/editar", methods=["GET", "POST"])
def producto_editar(producto_id):
    prod = producto.obtener_un_producto(producto_id)
    if prod is None:
        abort(404)

    if request.method == "POST":
        datos = _datos_producto()

        if datos is not None:
            otro = producto.obtener_producto_por_codigo(datos["codigo"])

            if otro is not None and otro.id_producto != producto_id:
                flash("Ya existe un producto con ese código", "error")
            else:
                producto.actualizar_producto(
                    id_producto=producto_id,
                    estado=prod.estado,
                    fecha_modificacion=datetime.now(),
                    **datos
                )
                flash("Producto actualizado", "exito")
                return redirect(url_for("inventario.productos"))

        return redirect(url_for("inventario.producto_editar", producto_id=producto_id))

    return render_template(
        "inventario/productos/form.html",
        producto=prod,
        tipos=TIPOS_PRODUCTO
    )


@inventario_bp.route("/productos/<int:producto_id>/baja", methods=["POST"])
def producto_baja(producto_id):
    if producto.obtener_un_producto(producto_id) is None:
        abort(404)

    # Un producto con existencias no se da de baja (se perderia de vista su stock)
    if inventario.obtener_stock_de_producto(producto_id) > 0:
        flash("No se puede dar de baja un producto con existencias", "error")
    else:
        producto.actualizar_estado_producto(producto_id, INACTIVO, datetime.now())
        flash("Producto dado de baja", "exito")

    return redirect(url_for("inventario.productos"))


# ALMACENES

@inventario_bp.route("/almacenes")
def almacenes():
    estado = request.args.get("estado")

    if estado:
        lista = almacen.obtener_almacenes_por_estado(estado)
    else:
        lista = almacen.obtener_almacenes()

    return render_template(
        "inventario/almacenes/index.html",
        almacenes=lista,
        estado=estado
    )


@inventario_bp.route("/almacenes/nuevo", methods=["GET", "POST"])
def almacen_nuevo():
    # Form: codigo, nombre, tipo, ubicacion
    if request.method == "POST":
        datos = _datos_almacen()

        if datos is not None:
            if almacen.obtener_almacen_por_codigo(datos["codigo"]) is not None:
                flash("Ya existe un almacén con ese código", "error")
            else:
                ahora = datetime.now()
                almacen.insertar_almacen(
                    estado=ACTIVO,
                    fecha_creacion=ahora,
                    fecha_modificacion=ahora,
                    **datos
                )
                flash("Almacén creado", "exito")
                return redirect(url_for("inventario.almacenes"))

        return redirect(url_for("inventario.almacen_nuevo"))

    return render_template(
        "inventario/almacenes/form.html",
        almacen=None
    )


@inventario_bp.route("/almacenes/<int:almacen_id>/editar", methods=["GET", "POST"])
def almacen_editar(almacen_id):
    alm = almacen.obtener_un_almacen(almacen_id)
    if alm is None:
        abort(404)

    if request.method == "POST":
        datos = _datos_almacen()

        if datos is not None:
            otro = almacen.obtener_almacen_por_codigo(datos["codigo"])

            if otro is not None and otro.id_almacen != almacen_id:
                flash("Ya existe un almacén con ese código", "error")
            else:
                almacen.actualizar_almacen(
                    id_almacen=almacen_id,
                    estado=alm.estado,
                    fecha_modificacion=datetime.now(),
                    **datos
                )
                flash("Almacén actualizado", "exito")
                return redirect(url_for("inventario.almacenes"))

        return redirect(url_for("inventario.almacen_editar", almacen_id=almacen_id))

    return render_template(
        "inventario/almacenes/form.html",
        almacen=alm
    )


@inventario_bp.route("/almacenes/<int:almacen_id>/baja", methods=["POST"])
def almacen_baja(almacen_id):
    if almacen.obtener_un_almacen(almacen_id) is None:
        abort(404)

    # Un almacen con existencias no se da de baja
    en_almacen = inventario.obtener_inventario_por_almacen(almacen_id)

    if any(fila.cantidad > 0 for fila in en_almacen):
        flash("No se puede dar de baja un almacén con existencias", "error")
    else:
        almacen.actualizar_estado_almacen(almacen_id, INACTIVO, datetime.now())
        flash("Almacén dado de baja", "exito")

    return redirect(url_for("inventario.almacenes"))


# LOTES
# Los lotes no tienen estado en la BD, por eso no hay baja de lotes.

@inventario_bp.route("/lotes")
def lotes():
    producto_id = request.args.get("producto_id", type=int)
    con_existencia = request.args.get("con_existencia")

    if con_existencia:
        lista = lote.obtener_lotes_con_existencia()
    elif producto_id:
        lista = lote.obtener_lotes_por_producto(producto_id)
    else:
        lista = lote.obtener_lotes()

    return render_template(
        "inventario/lotes/index.html",
        lotes=lista,
        productos=producto.obtener_productos_por_estado(ACTIVO),
        producto_id=producto_id
    )


@inventario_bp.route("/lotes/nuevo", methods=["GET", "POST"])
def lote_nuevo():
    # Form: codigo, producto_id
    if request.method == "POST":
        codigo = _texto("codigo")
        producto_id = request.form.get("producto_id", type=int)
        prod = producto.obtener_un_producto(producto_id) if producto_id else None

        if not codigo:
            flash("Indique el código del lote", "error")
        elif prod is None or prod.estado != ACTIVO:
            flash("Debe elegir un producto activo", "error")
        elif lote.obtener_lote_por_codigo(codigo) is not None:
            flash("Ya existe un lote con ese código", "error")
        else:
            ahora = datetime.now()
            lote.insertar_lote(codigo, ahora, ahora, producto_id)
            flash("Lote creado", "exito")
            return redirect(url_for("inventario.lotes"))

        return redirect(url_for("inventario.lote_nuevo"))

    return render_template(
        "inventario/lotes/form.html",
        lote=None,
        productos=producto.obtener_productos_por_estado(ACTIVO)
    )


@inventario_bp.route("/lotes/<int:lote_id>/editar", methods=["GET", "POST"])
def lote_editar(lote_id):
    # Solo se permite cambiar el codigo: cambiar el producto descuadraria el inventario
    lot = lote.obtener_un_lote(lote_id)
    if lot is None:
        abort(404)

    if request.method == "POST":
        codigo = _texto("codigo")
        otro = lote.obtener_lote_por_codigo(codigo) if codigo else None

        if not codigo:
            flash("Indique el código del lote", "error")
        elif otro is not None and otro.id_lote != lote_id:
            flash("Ya existe un lote con ese código", "error")
        else:
            lote.actualizar_lote(lote_id, codigo, datetime.now(), lot.producto_id)
            flash("Lote actualizado", "exito")
            return redirect(url_for("inventario.lotes"))

        return redirect(url_for("inventario.lote_editar", lote_id=lote_id))

    return render_template(
        "inventario/lotes/form.html",
        lote=lot,
        productos=[]
    )


# EXISTENCIAS

@inventario_bp.route("/existencias")
def existencias():
    # ?almacen_id=1&producto_id=2 filtran; ?detalle=lotes agrega el desglose por lote
    almacen_id = request.args.get("almacen_id", type=int)
    producto_id = request.args.get("producto_id", type=int)

    por_almacen = inventario.obtener_existencias_por_producto_almacen()
    stock = inventario.obtener_stock_actual()

    if almacen_id:
        por_almacen = [f for f in por_almacen if f.id_almacen == almacen_id]
    if producto_id:
        por_almacen = [f for f in por_almacen if f.id_producto == producto_id]
        stock = [f for f in stock if f.id_producto == producto_id]

    por_lote = []
    if request.args.get("detalle") == "lotes":
        por_lote = inventario.obtener_inventario()
        if almacen_id:
            por_lote = [f for f in por_lote if f.almacen_id == almacen_id]
        if producto_id:
            por_lote = [f for f in por_lote if f.producto_id == producto_id]

    return render_template(
        "inventario/existencias/index.html",
        existencias=por_almacen,
        stock=stock,
        por_lote=por_lote,
        almacenes=almacen.obtener_almacenes_por_estado(ACTIVO),
        productos=producto.obtener_productos_por_estado(ACTIVO),
        almacen_id=almacen_id,
        producto_id=producto_id
    )


# REPORTE

@inventario_bp.route("/reporte")
def reporte():
    return render_template(
        "inventario/reporte.html",
        existencias=inventario.obtener_existencias_por_producto_almacen(),
        stock=inventario.obtener_stock_actual(),
        lotes=lote.obtener_lotes_con_existencia(),
        generado=datetime.now()
    )