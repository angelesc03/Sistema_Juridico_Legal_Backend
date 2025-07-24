from .auth import auth_bp
from .admin import admin_bp
from .demandas import demandas_bp
from .autoridad import autoridad_bp

def register_blueprints(app):
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(demandas_bp, url_prefix='/api/demandas')
    app.register_blueprint(autoridad_bp, url_prefix='/api/autoridad')
