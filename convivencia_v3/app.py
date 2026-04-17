"""
Convivencia Escolar v7 — app Flask (rutas y sesión).
API por dominio: routes/* (blueprints). Auxiliares: ce_db, ce_queries, ce_pdf, etc.
"""
import os
from flask import Flask, jsonify, redirect, render_template, session, url_for

from ce_constants import BARRERAS_OPCIONES, TIPOS_DOCUMENTO
from ce_db import USE_PG, init_db
from routes import register_blueprints

app = Flask(__name__)


@app.context_processor
def _inject_form_constants():
    return {"tipos_documento": TIPOS_DOCUMENTO, "barreras_opciones": BARRERAS_OPCIONES}

# ── Config / seguridad base ────────────────────────────────────────────────────
APP_ENV = (os.environ.get('APP_ENV') or os.environ.get('FLASK_ENV') or 'development').lower()
IS_PROD = APP_ENV in ('prod', 'production')

_sk = os.environ.get('SECRET_KEY')
if IS_PROD and not _sk:
    raise RuntimeError("Falta SECRET_KEY en producción (defínela como variable de entorno).")
app.secret_key = _sk or 'dev-insecure-secret-key-change-me'

# Cookies de sesión (mejoras básicas; Secure solo si HTTPS)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE=os.environ.get('SESSION_COOKIE_SAMESITE', 'Lax'),
    SESSION_COOKIE_SECURE=(os.environ.get('SESSION_COOKIE_SECURE', '1') == '1') if IS_PROD else False,
)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
PORT = int(os.environ.get('PORT', 5000))

# ── Páginas ───────────────────────────────────────────────────────────────────
def _redirect_si_estudiante():
    if session.get('usuario', {}).get('rol') == 'Estudiante':
        return redirect(url_for('estudiante_reportar'))
    return None


@app.route('/')
def index():
    if 'usuario' not in session:
        return redirect(url_for('login_page'))
    r = _redirect_si_estudiante()
    return r if r is not None else redirect(url_for('dashboard'))


@app.route('/login')
def login_page():
    if 'usuario' in session:
        r = _redirect_si_estudiante()
        return r if r is not None else redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'usuario' not in session: return redirect(url_for('login_page'))
    r = _redirect_si_estudiante()
    return r if r is not None else render_template('dashboard.html')


@app.route('/estudiante/reportar')
def estudiante_reportar():
    if 'usuario' not in session or session.get('usuario', {}).get('rol') != 'Estudiante':
        return redirect(url_for('login_page'))
    cid = int(session['usuario'].get('colegio_id') or 0)
    if cid <= 0:
        return redirect(url_for('login_page'))
    return render_template('reporte_estudiante.html', colegio_id=cid, reporte_token='', sesion_estudiante=True)


@app.route('/reporte/<int:colegio_id>')
def reporte_estudiante_pagina(colegio_id):
    """Canal estudiantil público: documento + contraseña del portal (sin sesión)."""
    return render_template(
        'reporte_estudiante.html', colegio_id=colegio_id, reporte_token='', sesion_estudiante=False
    )


@app.route('/reporte/<int:colegio_id>/t/<path:reporte_token>')
def reporte_estudiante_con_token(colegio_id, reporte_token):
    """Enlaces con token quedaron obsoletos: se redirige al formulario con documento y contraseña."""
    return redirect(url_for('reporte_estudiante_pagina', colegio_id=colegio_id))


@app.route('/health')
def health(): return jsonify({'status':'ok','version':'7.0','db':'postgresql' if USE_PG else 'sqlite'})

register_blueprints(app)

# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(__file__),'logs'), exist_ok=True)
    init_db()
    debug = (os.environ.get('FLASK_DEBUG', '0') == '1') and not IS_PROD
    app.run(debug=debug, host='0.0.0.0', port=PORT, use_reloader=False)
