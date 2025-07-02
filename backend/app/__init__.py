from flask import Flask
from flask_cors import CORS
from .db import mysql
from .routes import register_blueprints

def create_app():
    app = Flask(__name__)
    
    # CORS
    CORS(app, resources={r"/api/*": {"origins": "https://angelesc03.github.io"}})
    
    # Configuración
    app.config.from_object('app.config.Config')

    # Inicializar MySQL
    mysql.init_app(app)

    # Registrar rutas
    register_blueprints(app)

    return app
