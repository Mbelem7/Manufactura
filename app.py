from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, session, jsonify, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

load_dotenv()

# 1. CREAR LA ÚNICA INSTANCIA DE LA APP
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
# 2. BASE DE DATOS Y SUPABASE
USER = os.getenv("user")
PASSWORD = os.getenv("password")
HOST = os.getenv("host")
PORT = os.getenv("port")
DBNAME = os.getenv("dbname")

# Construir la URL de conexión
DATABASE_URL = f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}?sslmode=require"

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,   # antes de usar una conexión, comprueba que siga viva
    'pool_recycle': 280,     # renueva las conexiones cada ~5 minutos
}

# 3. INICIALIZAR LA BASE DE DATOS
# Al estar todo en una sola app, tus módulos ahora sí la encontrarán
db = SQLAlchemy(app)

# Test rápido de conexión
with app.app_context():
    try:
        db.engine.connect()
        print("¡Conexión a Supabase exitosa, rey!")
    except Exception as e:
        print(f"Error al conectar a Supabase: {e}")

# 4. IMPORTAR MÓDULOS (Limpiamos los que estaban duplicados)
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
from modulos.produccion import *

# 5. IMPORTAR RUTAS
from routes.dashboard import dashboard_bp
from routes.inventario import inventario_bp
from routes.produccion import produccion_bp
from routes.compras import compras_bp
from routes.ventas import ventas_bp
from routes.configuracion import configuracion_bp

# 6. REGISTRAR RUTAS (Directamente en la única app)
app.register_blueprint(dashboard_bp)
app.register_blueprint(inventario_bp)
app.register_blueprint(produccion_bp)
app.register_blueprint(compras_bp)
app.register_blueprint(ventas_bp)
app.register_blueprint(configuracion_bp)

if __name__ == "__main__":
    app.run(debug=True)