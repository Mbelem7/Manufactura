from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, session, jsonify, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

app = Flask(__name__)
load_dotenv()

#MODULOS
from modulos.producto import *
from modulos.bom import *
from modulos.lote import *
from modulos.orden_produccion import *
from modulos.ruta_operacion import *
from modulos.detalle_bom import *
from modulos.inventario import *
from modulos.detalle_orden_compra import *
from modulos.almacen import *
from modulos.detalle_orden_venta import *
from modulos.orden_venta import *
from modulos.cliente import *
from modulos.despacho import *
from modulos.detalle_despacho import *
from modulos.detalle_recepcion import *
from modulos.usuario import *
from modulos.recepcion import *
from modulos.orden_compra import *
from modulos.proveedor import *
from modulos.persona import *  
from modulos.detalle_despacho import *
from modulos.detalle_recepcion import *
from modulos.usuario import *
from modulos.produccion import *   
from modulos.recepcion import *
from modulos.orden_compra import *

from routes.dashboard import dashboard_bp
from routes.inventario import inventario_bp
from routes.produccion import produccion_bp
from routes.compras import compras_bp
from routes.ventas import ventas_bp
from routes.configuracion import configuracion_bp

def create_app():
    app = Flask(__name__)

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(inventario_bp)
    app.register_blueprint(produccion_bp)
    app.register_blueprint(compras_bp)
    app.register_blueprint(ventas_bp)
    app.register_blueprint(configuracion_bp)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)