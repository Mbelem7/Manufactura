from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, session, jsonify, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

app = Flask(__name__)
load_dotenv()
#Espcio paa la coneccion con la base de datos


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


if __name__ == "__main__":
    app.run(debug=True)