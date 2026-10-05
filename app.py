from flask import Flask

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