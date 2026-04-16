"""Blueprints registrados en la app Flask."""


def register_blueprints(flask_app):
    from routes.asistencia import bp as asistencia_bp
    from routes.auth_api import bp as auth_api_bp
    from routes.catalogo import bp as catalogo_bp
    from routes.estudiantes import bp as estudiantes_bp
    from routes.faltas import bp as faltas_bp
    from routes.institucion import bp as institucion_bp
    from routes.prevencion import bp as prevencion_bp
    from routes.promocion import bp as promocion_bp
    from routes.reportes_convivencia import bp as reportes_conv_bp
    from routes.reportes import bp as reportes_bp
    from routes.senales import bp as senales_bp
    flask_app.register_blueprint(auth_api_bp)
    flask_app.register_blueprint(institucion_bp)
    flask_app.register_blueprint(estudiantes_bp)
    flask_app.register_blueprint(faltas_bp)
    flask_app.register_blueprint(senales_bp)
    flask_app.register_blueprint(prevencion_bp)
    flask_app.register_blueprint(reportes_conv_bp)
    flask_app.register_blueprint(promocion_bp)
    flask_app.register_blueprint(asistencia_bp)
    flask_app.register_blueprint(catalogo_bp)
    flask_app.register_blueprint(reportes_bp)
