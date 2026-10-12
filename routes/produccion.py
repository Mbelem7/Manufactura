from datetime import datetime, timedelta
from decimal import Decimal

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, session
from sqlalchemy.exc import IntegrityError

from modulos import (
    producto,
    lote,
    almacen,
    inventario,
    detalle_bom,
    centro_trabajo,
    ruta_operacion,
    orden_produccion,
    produccion,
    transacciones
)
# Se importa con otro nombre porque la ruta de abajo se llama "bom"
# y pisaria el modulo si tuvieran el mismo nombre
from modulos import bom as bom_db


produccion_bp = Blueprint(
    "produccion",
    __name__,
    url_prefix="/produccion"
)


# Valores de estado y tipo (ajustarlos a los que se usen en la BD)
ACTIVO = "activo"
INACTIVO = "inactivo"
TIPO_MATERIA_PRIMA = "materia_prima"
TIPO_PRODUCTO_TERMINADO = "producto_terminado"
OP_PENDIENTE = "pendiente"
OP_EN_PROCESO = "en_proceso"
OP_FINALIZADA = "finalizada"
OP_CANCELADA = "cancelada"


# ---------- AYUDAS INTERNAS ----------

def _texto(nombre):
    # Texto del formulario; vacio -> None
    valor = (request.form.get(nombre) or "").strip()
    return valor or None


def _decimal_positivo(texto):
    # Texto -> Decimal mayor que 0; si es invalido devuelve None
    try:
        valor = Decimal((texto or "").strip())
        if not valor.is_finite() or valor <= 0:
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


def _componentes():
    # Campos: producto_component_id, cantidad. Devuelve None si algo es invalido
    lineas = []

    try:
        for l in _lineas_form(["producto_component_id", "cantidad"]):
            cantidad = _decimal_positivo(l["cantidad"])
            if cantidad is None:
                return None
            lineas.append({
                "producto_component_id": int(l["producto_component_id"]),
                "cantidad": cantidad
            })
    except ValueError:
        return None

    return lineas or None


def _ids_materias_primas():
    return {
        p.id_producto
        for p in producto.obtener_productos_por_estado(ACTIVO)
        if p.tipo_producto == TIPO_MATERIA_PRIMA
    }


def _producto_terminado_activo(producto_id):
    prod = producto.obtener_un_producto(producto_id) if producto_id else None
    if prod is None or prod.estado != ACTIVO or prod.tipo_producto != TIPO_PRODUCTO_TERMINADO:
        return None
    return prod


def _obtener_o_crear_lote(codigo, producto_id):
    # Usa el lote existente o lo crea con ese codigo
    existente = lote.obtener_lote_por_codigo(codigo)
    if existente is not None:
        if existente.producto_id != producto_id:
            raise ValueError("El lote " + codigo + " pertenece a otro producto")
        return existente.id_lote

    ahora = datetime.now()
    return lote.insertar_lote(codigo, ahora, ahora, producto_id)


def _bom_o_404(bom_id):
    registro = bom_db.obtener_un_bom(bom_id)
    if registro is None:
        abort(404)
    return registro


def _orden_o_404(orden_id):
    orden = orden_produccion.obtener_un_orden_produccion(orden_id)
    if orden is None:
        abort(404)
    return orden


# BOM

@produccion_bp.route("/bom")
def bom():
    estado = request.args.get("estado")

    if estado:
        lista = bom_db.obtener_boms_por_estado(estado)
    else:
        lista = bom_db.obtener_boms()

    return render_template(
        "produccion/bom/index.html",
        boms=lista,
        estado=estado
    )


@produccion_bp.route("/bom/nuevo", methods=["GET", "POST"])
def bom_nuevo():
    # Form: codigo, nombre, producto_id + componentes (producto_component_id, cantidad repetidos)
    if request.method == "POST":
        codigo = _texto("codigo")
        nombre = _texto("nombre")
        producto_id = request.form.get("producto_id", type=int)
        componentes = _componentes()

        if not (codigo and nombre):
            flash("Complete código y nombre", "error")
        elif _producto_terminado_activo(producto_id) is None:
            flash("El BOM debe ser de un producto terminado activo", "error")
        elif bom_db.obtener_bom_por_codigo(codigo) is not None:
            flash("Ya existe un BOM con ese código", "error")
        elif componentes is None:
            flash("Agregue al menos un componente con cantidad válida", "error")
        else:
            ids = [c["producto_component_id"] for c in componentes]

            if len(set(ids)) != len(ids):
                flash("No repita componentes en el BOM", "error")
            elif any(i not in _ids_materias_primas() for i in ids):
                flash("Los componentes deben ser materias primas activas", "error")
            else:
                try:
                    bom_id = transacciones.crear_bom(
                        codigo, nombre, producto_id, componentes, ACTIVO, datetime.now()
                    )
                except IntegrityError:
                    flash("No se pudo crear el BOM", "error")
                else:
                    flash("BOM creado", "exito")
                    return redirect(url_for("produccion.bom_detalle", bom_id=bom_id))

        return redirect(url_for("produccion.bom_nuevo"))

    return render_template(
        "produccion/bom/form.html",
        bom=None,
        productos_terminados=[
            p for p in producto.obtener_productos_por_estado(ACTIVO)
            if p.tipo_producto == TIPO_PRODUCTO_TERMINADO
        ],
        materias_primas=[
            p for p in producto.obtener_productos_por_estado(ACTIVO)
            if p.tipo_producto == TIPO_MATERIA_PRIMA
        ]
    )


@produccion_bp.route("/bom/<int:bom_id>")
def bom_detalle(bom_id):
    registro = _bom_o_404(bom_id)

    return render_template(
        "produccion/bom/detail.html",
        bom_id=bom_id,
        bom=registro,
        componentes=detalle_bom.obtener_detalles_bom_por_bom(bom_id),
        materias_primas=[
            p for p in producto.obtener_productos_por_estado(ACTIVO)
            if p.tipo_producto == TIPO_MATERIA_PRIMA
        ]
    )


@produccion_bp.route("/bom/<int:bom_id>/editar", methods=["GET", "POST"])
def bom_editar(bom_id):
    # Solo codigo y nombre; los componentes se manejan desde el detalle
    registro = _bom_o_404(bom_id)

    if request.method == "POST":
        codigo = _texto("codigo")
        nombre = _texto("nombre")
        otro = bom_db.obtener_bom_por_codigo(codigo) if codigo else None

        if not (codigo and nombre):
            flash("Complete código y nombre", "error")
        elif otro is not None and otro.id_bom != bom_id:
            flash("Ya existe un BOM con ese código", "error")
        else:
            bom_db.actualizar_bom(
                bom_id, codigo, nombre, registro.estado,
                datetime.now(), registro.producto_id
            )
            flash("BOM actualizado", "exito")
            return redirect(url_for("produccion.bom_detalle", bom_id=bom_id))

        return redirect(url_for("produccion.bom_editar", bom_id=bom_id))

    return render_template(
        "produccion/bom/form.html",
        bom=registro,
        productos_terminados=[],
        materias_primas=[]
    )


@produccion_bp.route("/bom/<int:bom_id>/baja", methods=["POST"])
def bom_baja(bom_id):
    _bom_o_404(bom_id)

    bom_db.actualizar_estado_bom(bom_id, INACTIVO, datetime.now())
    flash("BOM dado de baja", "exito")

    return redirect(url_for("produccion.bom"))


# Componentes del BOM

@produccion_bp.route("/bom/<int:bom_id>/componentes", methods=["POST"])
def bom_componente_agregar(bom_id):
    # Form: producto_component_id, cantidad
    _bom_o_404(bom_id)
    componentes = _componentes()

    if componentes is None:
        flash("Componente o cantidad inválidos", "error")
    else:
        nuevo = componentes[0]["producto_component_id"]
        existentes = {d.producto_component_id for d in detalle_bom.obtener_detalles_bom_por_bom(bom_id)}

        if nuevo not in _ids_materias_primas():
            flash("El componente debe ser una materia prima activa", "error")
        elif nuevo in existentes:
            flash("Ese componente ya está en el BOM; edite su cantidad", "error")
        else:
            detalle_bom.insertar_detalle_bom(bom_id, nuevo, componentes[0]["cantidad"])
            flash("Componente agregado", "exito")

    return redirect(url_for("produccion.bom_detalle", bom_id=bom_id))


@produccion_bp.route("/bom/componentes/<int:detalle_id>/actualizar", methods=["POST"])
def bom_componente_actualizar(detalle_id):
    # Form: cantidad
    detalle = detalle_bom.obtener_un_detalle_bom(detalle_id)
    if detalle is None:
        abort(404)

    cantidad = _decimal_positivo(request.form.get("cantidad"))

    if cantidad is None:
        flash("Cantidad inválida", "error")
    else:
        detalle_bom.actualizar_detalle_bom(
            detalle_id, detalle.bom_id, detalle.producto_component_id, cantidad
        )
        flash("Componente actualizado", "exito")

    return redirect(url_for("produccion.bom_detalle", bom_id=detalle.bom_id))


@produccion_bp.route("/bom/componentes/<int:detalle_id>/eliminar", methods=["POST"])
def bom_componente_eliminar(detalle_id):
    detalle = detalle_bom.obtener_un_detalle_bom(detalle_id)
    if detalle is None:
        abort(404)

    detalle_bom.eliminar_detalle_bom(detalle_id)
    flash("Componente eliminado", "exito")

    return redirect(url_for("produccion.bom_detalle", bom_id=detalle.bom_id))


# CENTROS DE TRABAJO

@produccion_bp.route("/centros-trabajo")
def centros_trabajo():
    estado = request.args.get("estado")

    if estado:
        lista = centro_trabajo.obtener_centros_trabajo_por_estado(estado)
    else:
        lista = centro_trabajo.obtener_centros_trabajo()

    return render_template(
        "produccion/centros_trabajo/index.html",
        centros=lista,
        estado=estado
    )


@produccion_bp.route("/centros-trabajo/nuevo", methods=["GET", "POST"])
def centro_trabajo_nuevo():
    # Form: codigo, nombre, maquina
    if request.method == "POST":
        codigo = _texto("codigo")
        nombre = _texto("nombre")

        if not (codigo and nombre):
            flash("Complete código y nombre", "error")
        elif centro_trabajo.obtener_centro_trabajo_por_codigo(codigo) is not None:
            flash("Ya existe un centro de trabajo con ese código", "error")
        else:
            ahora = datetime.now()
            centro_trabajo.insertar_centro_trabajo(
                codigo, nombre, _texto("maquina"), ACTIVO, ahora, ahora
            )
            flash("Centro de trabajo creado", "exito")
            return redirect(url_for("produccion.centros_trabajo"))

        return redirect(url_for("produccion.centro_trabajo_nuevo"))

    return render_template(
        "produccion/centros_trabajo/form.html",
        centro=None
    )


@produccion_bp.route("/centros-trabajo/<int:centro_id>/editar", methods=["GET", "POST"])
def centro_trabajo_editar(centro_id):
    centro = centro_trabajo.obtener_un_centro_trabajo(centro_id)
    if centro is None:
        abort(404)

    if request.method == "POST":
        codigo = _texto("codigo")
        nombre = _texto("nombre")
        otro = centro_trabajo.obtener_centro_trabajo_por_codigo(codigo) if codigo else None

        if not (codigo and nombre):
            flash("Complete código y nombre", "error")
        elif otro is not None and otro.id_centro != centro_id:
            flash("Ya existe un centro de trabajo con ese código", "error")
        else:
            centro_trabajo.actualizar_centro_trabajo(
                centro_id, codigo, nombre, _texto("maquina"),
                centro.estado, datetime.now()
            )
            flash("Centro de trabajo actualizado", "exito")
            return redirect(url_for("produccion.centros_trabajo"))

        return redirect(url_for("produccion.centro_trabajo_editar", centro_id=centro_id))

    return render_template(
        "produccion/centros_trabajo/form.html",
        centro=centro
    )


@produccion_bp.route("/centros-trabajo/<int:centro_id>/baja", methods=["POST"])
def centro_trabajo_baja(centro_id):
    if centro_trabajo.obtener_un_centro_trabajo(centro_id) is None:
        abort(404)

    centro_trabajo.actualizar_estado_centro_trabajo(centro_id, INACTIVO, datetime.now())
    flash("Centro de trabajo dado de baja", "exito")

    return redirect(url_for("produccion.centros_trabajo"))


# RUTAS DE OPERACIÓN
# Cada ruta (operacion) pertenece a una orden de produccion y a un centro de trabajo.

def _datos_ruta(ordenp_id, ruta_id=None):
    # Lee y valida el formulario de ruta; si algo falla avisa y devuelve None
    codigo = _texto("codigo")
    tiempo = _decimal_positivo(request.form.get("tiempo_estandar"))
    secuencia = request.form.get("secuencia", type=int)
    centro_id = request.form.get("centro_id", type=int)

    orden = orden_produccion.obtener_un_orden_produccion(ordenp_id) if ordenp_id else None
    centro = centro_trabajo.obtener_un_centro_trabajo(centro_id) if centro_id else None
    otra = ruta_operacion.obtener_ruta_operacion_por_codigo(codigo) if codigo else None

    if not codigo or tiempo is None or not secuencia or secuencia < 1:
        flash("Complete código, tiempo estándar (mayor a 0) y secuencia", "error")
        return None

    if orden is None or orden.estado != OP_PENDIENTE:
        flash("La orden de producción debe existir y estar pendiente", "error")
        return None

    if centro is None or centro.estado != ACTIVO:
        flash("Debe elegir un centro de trabajo activo", "error")
        return None

    if otra is not None and otra.id_ruta != ruta_id:
        flash("Ya existe una operación con ese código", "error")
        return None

    mismas = ruta_operacion.obtener_rutas_operacion_por_ordenp(ordenp_id)
    if any(r.secuencia == secuencia and r.estado == ACTIVO and r.id_ruta != ruta_id for r in mismas):
        flash("Ya hay una operación con esa secuencia en la orden", "error")
        return None

    return {
        "codigo": codigo,
        "tiempo_estandar": tiempo,
        "secuencia": secuencia,
        "centro_id": centro_id,
        "ordenp_id": ordenp_id
    }


@produccion_bp.route("/rutas")
def rutas():
    orden_id = request.args.get("orden_id", type=int)
    estado = request.args.get("estado")

    if orden_id:
        lista = ruta_operacion.obtener_rutas_operacion_por_ordenp(orden_id)
    elif estado:
        lista = ruta_operacion.obtener_rutas_operacion_por_estado(estado)
    else:
        lista = ruta_operacion.obtener_rutas_operacion()

    return render_template(
        "produccion/rutas/index.html",
        rutas=lista,
        orden_id=orden_id
    )


@produccion_bp.route("/rutas/nueva", methods=["GET", "POST"])
def ruta_nueva():
    # Form: codigo, tiempo_estandar, secuencia, centro_id, ordenp_id
    if request.method == "POST":
        ordenp_id = request.form.get("ordenp_id", type=int)
        datos = _datos_ruta(ordenp_id)

        if datos is not None:
            ahora = datetime.now()
            ruta_operacion.insertar_ruta_operacion(
                fecha_creacion=ahora,
                fecha_modificacion=ahora,
                estado=ACTIVO,
                **datos
            )
            flash("Operación creada", "exito")
            return redirect(url_for("produccion.rutas", orden_id=ordenp_id))

        return redirect(url_for("produccion.ruta_nueva", orden_id=ordenp_id))

    return render_template(
        "produccion/rutas/form.html",
        ruta=None,
        orden_id=request.args.get("orden_id", type=int),
        ordenes=orden_produccion.obtener_ordenes_produccion_por_estado(OP_PENDIENTE),
        centros=centro_trabajo.obtener_centros_trabajo_por_estado(ACTIVO)
    )


@produccion_bp.route("/rutas/<int:ruta_id>/editar", methods=["GET", "POST"])
def ruta_editar(ruta_id):
    # La orden no se cambia; solo codigo, tiempo, secuencia y centro
    ruta = ruta_operacion.obtener_un_ruta_operacion(ruta_id)
    if ruta is None:
        abort(404)

    if request.method == "POST":
        datos = _datos_ruta(ruta.ordenp_id, ruta_id)

        if datos is not None:
            ruta_operacion.actualizar_ruta_operacion(
                id_ruta=ruta_id,
                fecha_modificacion=datetime.now(),
                estado=ruta.estado,
                **datos
            )
            flash("Operación actualizada", "exito")
            return redirect(url_for("produccion.rutas", orden_id=ruta.ordenp_id))

        return redirect(url_for("produccion.ruta_editar", ruta_id=ruta_id))

    return render_template(
        "produccion/rutas/form.html",
        ruta=ruta,
        orden_id=ruta.ordenp_id,
        ordenes=[],
        centros=centro_trabajo.obtener_centros_trabajo_por_estado(ACTIVO)
    )


@produccion_bp.route("/rutas/<int:ruta_id>/baja", methods=["POST"])
def ruta_baja(ruta_id):
    ruta = ruta_operacion.obtener_un_ruta_operacion(ruta_id)
    if ruta is None:
        abort(404)

    ruta_operacion.actualizar_estado_ruta_operacion(ruta_id, INACTIVO, datetime.now())
    flash("Operación dada de baja", "exito")

    return redirect(url_for("produccion.rutas", orden_id=ruta.ordenp_id))


# ÓRDENES DE PRODUCCIÓN

@produccion_bp.route("/ordenes")
def ordenes():
    estado = request.args.get("estado")

    if estado:
        lista = orden_produccion.obtener_ordenes_produccion_por_estado(estado)
    else:
        lista = orden_produccion.obtener_ordenes_produccion()

    return render_template(
        "produccion/ordenes/index.html",
        ordenes=lista,
        estado=estado
    )


@produccion_bp.route("/ordenes/nueva", methods=["GET", "POST"])
def orden_nueva():
    # Form: producto_id, bom_id, cantidad, lote_codigo (lote del producto que se va a fabricar)
    if request.method == "POST":
        producto_id = request.form.get("producto_id", type=int)
        bom_id = request.form.get("bom_id", type=int)
        cantidad = _decimal_positivo(request.form.get("cantidad"))
        lote_codigo = _texto("lote_codigo")

        registro = bom_db.obtener_un_bom(bom_id) if bom_id else None

        if _producto_terminado_activo(producto_id) is None:
            flash("Debe elegir un producto terminado activo", "error")
        elif registro is None or registro.estado != ACTIVO or registro.producto_id != producto_id:
            flash("Debe elegir un BOM activo de ese producto", "error")
        elif cantidad is None:
            flash("La cantidad debe ser un número mayor a 0", "error")
        elif not lote_codigo:
            flash("Indique el código del lote que se va a producir", "error")
        else:
            try:
                lote_id = _obtener_o_crear_lote(lote_codigo, producto_id)
                ahora = datetime.now()
                orden_id = orden_produccion.insertar_orden_produccion(
                    cantidad, OP_PENDIENTE, ahora, ahora, producto_id, lote_id, bom_id
                )
            except (ValueError, IntegrityError) as e:
                flash("No se pudo crear la orden: " + str(e), "error")
            else:
                flash("Orden de producción creada", "exito")
                return redirect(url_for("produccion.orden_detalle", orden_id=orden_id))

        return redirect(url_for("produccion.orden_nueva"))

    return render_template(
        "produccion/ordenes/form.html",
        orden=None,
        productos_terminados=[
            p for p in producto.obtener_productos_por_estado(ACTIVO)
            if p.tipo_producto == TIPO_PRODUCTO_TERMINADO
        ],
        boms=bom_db.obtener_boms_por_estado(ACTIVO)
    )


@produccion_bp.route("/ordenes/<int:orden_id>")
def orden_detalle(orden_id):
    orden = _orden_o_404(orden_id)

    # Materia prima necesaria segun el BOM vs lo que hay en inventario
    requerimientos = []
    if orden.bom_id:
        for c in detalle_bom.obtener_detalles_bom_por_bom(orden.bom_id):
            necesaria = c.cantidad * orden.cantidad
            disponible = inventario.obtener_stock_de_producto(c.producto_component_id)
            requerimientos.append({
                "codigo": c.producto_codigo,
                "nombre": c.producto_nombre,
                "unidad": c.producto_unidad_medida,
                "necesaria": necesaria,
                "disponible": disponible,
                "suficiente": disponible >= necesaria
            })

    return render_template(
        "produccion/ordenes/detail.html",
        orden_id=orden_id,
        orden=orden,
        requerimientos=requerimientos,
        rutas=ruta_operacion.obtener_rutas_operacion_por_ordenp(orden_id),
        ejecuciones=[
            e for e in produccion.obtener_produccion_con_operador()
            if e.ordenp_id == orden_id
        ],
        editable=(orden.estado == OP_PENDIENTE)
    )


@produccion_bp.route("/ordenes/<int:orden_id>/editar", methods=["GET", "POST"])
def orden_editar(orden_id):
    # Solo mientras esta pendiente. El producto no se cambia: se cambia cantidad, BOM y lote
    orden = _orden_o_404(orden_id)

    if orden.estado != OP_PENDIENTE:
        flash("Solo se puede editar una orden pendiente", "error")
        return redirect(url_for("produccion.orden_detalle", orden_id=orden_id))

    if request.method == "POST":
        bom_id = request.form.get("bom_id", type=int)
        cantidad = _decimal_positivo(request.form.get("cantidad"))
        lote_codigo = _texto("lote_codigo")

        registro = bom_db.obtener_un_bom(bom_id) if bom_id else None

        if registro is None or registro.estado != ACTIVO or registro.producto_id != orden.producto_id:
            flash("Debe elegir un BOM activo de ese producto", "error")
        elif cantidad is None:
            flash("La cantidad debe ser un número mayor a 0", "error")
        elif not lote_codigo:
            flash("Indique el código del lote", "error")
        else:
            try:
                lote_id = _obtener_o_crear_lote(lote_codigo, orden.producto_id)
                orden_produccion.actualizar_orden_produccion(
                    id_ordenp=orden_id,
                    cantidad=cantidad,
                    estado=orden.estado,
                    fecha_modificacion=datetime.now(),
                    producto_id=orden.producto_id,
                    lote_id=lote_id,
                    bom_id=bom_id
                )
            except (ValueError, IntegrityError) as e:
                flash("No se pudo actualizar la orden: " + str(e), "error")
            else:
                flash("Orden actualizada", "exito")
                return redirect(url_for("produccion.orden_detalle", orden_id=orden_id))

        return redirect(url_for("produccion.orden_editar", orden_id=orden_id))

    return render_template(
        "produccion/ordenes/form.html",
        orden=orden,
        productos_terminados=[],
        boms=bom_db.obtener_boms_por_producto(orden.producto_id)
    )


@produccion_bp.route("/ordenes/<int:orden_id>/baja", methods=["POST"])
def orden_baja(orden_id):
    orden = _orden_o_404(orden_id)

    if orden.estado in (OP_EN_PROCESO, OP_FINALIZADA):
        flash("No se puede dar de baja una orden en proceso o finalizada", "error")
    else:
        orden_produccion.actualizar_estado_orden_produccion(orden_id, OP_CANCELADA, datetime.now())
        flash("Orden dada de baja", "exito")

    return redirect(url_for("produccion.orden_detalle", orden_id=orden_id))


# EJECUCIONES (MES)
# produccion guarda el registro de una orden: hora de inicio y fin, operador y cantidades.

@produccion_bp.route("/ejecuciones")
def ejecuciones():
    return render_template(
        "produccion/ejecuciones/index.html",
        en_curso=produccion.obtener_produccion_en_curso(),
        historial=produccion.obtener_produccion_con_operador(),
        almacenes=almacen.obtener_almacenes_por_estado(ACTIVO)
    )


@produccion_bp.route("/ejecuciones/nueva", methods=["GET", "POST"])
def ejecucion_nueva():
    # Boton "Iniciar". Form: ordenp_id. El operador sale de la sesion (session["id_usuario"])
    if request.method == "POST":
        ordenp_id = request.form.get("ordenp_id", type=int)
        usuario_id = session.get("id_usuario")
        orden = orden_produccion.obtener_un_orden_produccion(ordenp_id) if ordenp_id else None

        if not usuario_id:
            flash("Debe iniciar sesión para registrar una ejecución", "error")
        elif orden is None or orden.estado not in (OP_PENDIENTE, OP_EN_PROCESO):
            flash("Debe elegir una orden pendiente o en proceso", "error")
        elif not orden.bom_id:
            flash("La orden no tiene BOM asociado", "error")
        elif any(e.ordenp_id == ordenp_id for e in produccion.obtener_produccion_en_curso()):
            flash("Esa orden ya tiene una ejecución en curso", "error")
        else:
            transacciones.iniciar_ejecucion(ordenp_id, usuario_id, datetime.now(), OP_EN_PROCESO)
            flash("Ejecución iniciada", "exito")
            return redirect(url_for("produccion.ejecuciones"))

        return redirect(url_for("produccion.ejecucion_nueva"))

    return render_template(
        "produccion/ejecuciones/form.html",
        orden_id=request.args.get("orden_id", type=int),
        ordenes=(
            orden_produccion.obtener_ordenes_produccion_por_estado(OP_PENDIENTE)
            + orden_produccion.obtener_ordenes_produccion_por_estado(OP_EN_PROCESO)
        )
    )


@produccion_bp.route("/ejecuciones/<int:produccion_id>/terminar", methods=["POST"])
def ejecucion_terminar(produccion_id):
    # Boton "Terminar". Form: cantidad_aceptada, cantidad_rechazada, almacen_mp_id, almacen_pt_id
    # Cierra el registro, descuenta la materia prima del almacen_mp, suma el producto
    # terminado al almacen_pt y deja la orden como finalizada (todo junto)
    registro = produccion.obtener_un_produccion(produccion_id)
    if registro is None:
        abort(404)

    aceptada = request.form.get("cantidad_aceptada", type=int)
    rechazada = request.form.get("cantidad_rechazada", type=int)
    almacen_mp_id = request.form.get("almacen_mp_id", type=int)
    almacen_pt_id = request.form.get("almacen_pt_id", type=int)

    alm_mp = almacen.obtener_un_almacen(almacen_mp_id) if almacen_mp_id else None
    alm_pt = almacen.obtener_un_almacen(almacen_pt_id) if almacen_pt_id else None

    if registro.fecha_fin is not None:
        flash("Esta ejecución ya fue terminada", "error")
    elif aceptada is None or rechazada is None or aceptada < 0 or rechazada < 0 or aceptada + rechazada == 0:
        flash("Indique cantidades aceptada y rechazada válidas (enteros)", "error")
    elif alm_mp is None or alm_mp.estado != ACTIVO or alm_pt is None or alm_pt.estado != ACTIVO:
        flash("Elija los almacenes de materia prima y de producto terminado", "error")
    else:
        try:
            transacciones.finalizar_produccion(
                produccion_id, datetime.now(), aceptada, rechazada,
                almacen_mp_id, almacen_pt_id, OP_FINALIZADA
            )
        except (ValueError, IntegrityError) as e:
            flash("No se pudo terminar: " + str(e), "error")
        else:
            flash("Ejecución terminada", "exito")

    return redirect(url_for("produccion.ejecuciones"))


# REPORTE

@produccion_bp.route("/reporte")
def reporte():
    # /produccion/reporte?inicio=2026-10-01&fin=2026-10-31
    inicio = request.args.get("inicio")
    fin = request.args.get("fin")
    filas = []

    if inicio and fin:
        try:
            desde = datetime.strptime(inicio, "%Y-%m-%d")
            hasta = datetime.strptime(fin, "%Y-%m-%d") + timedelta(days=1)
        except ValueError:
            flash("Use fechas con formato AAAA-MM-DD", "error")
        else:
            filas = orden_produccion.obtener_reporte_ordenes_produccion(desde, hasta)

    return render_template(
        "produccion/reporte.html",
        reporte=filas,
        inicio=inicio,
        fin=fin
    )