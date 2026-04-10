"""
Convivencia Escolar v7 — app Flask (rutas y sesión).
Lógica auxiliar: ce_db (BD), ce_queries (filtros SQL), ce_pdf, ce_export (CSV),
ce_utils, ce_sugerencias.
"""
import csv
import os
import re
import secrets
from io import StringIO
from collections import Counter
from datetime import datetime
from functools import wraps

from flask import Flask, jsonify, redirect, render_template, request, Response, send_file, session, url_for
from werkzeug.utils import secure_filename

from ce_db import USE_PG, commit, execute, get_db, init_db, ph
from ce_export import csv_response
from ce_pdf import generar_pdf_acta_proceso, generar_pdf_curso, generar_pdf_estudiante
from ce_gestion import enriquecer_falta_gestion
from ce_queries import col_nom, fq, faltas_con_notas
from ce_sugerencias import generar_sugerencias
from ce_utils import hpwd, nombre_desde_partes, solo_letras, solo_numeros

app = Flask(__name__)

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
UPLOAD_CONDUCTAS = os.path.join(UPLOAD_FOLDER, 'conductas')
PORT = int(os.environ.get('PORT', 5000))

TIPOS_DOCUMENTO = (
    'Tarjeta de identidad (TI)',
    'Cédula de ciudadanía (CC)',
    'Cédula de extranjería (CE)',
    'Pasaporte (PP)',
    'Registro civil (RC)',
    'Permiso por protección temporal (PPT)',
    'Sin documento / pendiente (SD)',
)

BARRERAS_OPCIONES = (
    'Ninguna identificada',
    'Discapacidad sensorial',
    'Discapacidad física (motora)',
    'Discapacidad cognitiva (intelectual)',
    'Trastornos del desarrollo',
    'Trastornos específicos del aprendizaje',
    'Trastornos emocionales y del comportamiento',
    'Discapacidad múltiple',
)

_CONDUCTA_TIPOS = frozenset({'conv_i', 'conv_ii', 'conv_iii'})
_SUBS_POR_TIPO = {
    'conv_i': frozenset({'conflictos_manejables', 'sin_dano'}),
    'conv_ii': frozenset({'bullying_incipiente', 'afectacion_emocional', 'conflictos_reiterados'}),
    'conv_iii': frozenset({'violencia_fisica', 'abuso_sexual', 'consumo_micro', 'intento_suicidio'}),
}
_URGENCIAS = frozenset({'baja', 'moderada', 'alta', 'critica'})
CITA_ROLES_DESTINO = frozenset({'Coordinador', 'Director', 'Orientador', 'Docente'})


def _cancelar_citas_abiertas(conn, falta_id):
    p = ph()
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    execute(
        conn,
        f"UPDATE citas_acudiente SET estado='cancelada', actualizado_en={p} "
        f"WHERE falta_id={p} AND estado IN ('pendiente_agenda','pendiente_confirmacion_acudiente')",
        (now, falta_id),
    )


def _attach_cita_falta(conn, f):
    if not f or f.get('id') is None:
        return
    p = ph()
    c = execute(
        conn,
        f"SELECT * FROM citas_acudiente WHERE falta_id={p} ORDER BY id DESC LIMIT 1",
        (f['id'],),
        fetch='one',
    )
    f['cita_acudiente'] = c


def _insert_cita_escuela(conn, falta_id, colegio_id, fecha_hora, u):
    p = ph()
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    execute(
        conn,
        f"INSERT INTO citas_acudiente (falta_id,colegio_id,origen,estado,rol_destino,fecha_hora,"
        f"creado_por_id,creado_por_nombre,creado_por_rol,agenda_por_id,agenda_por_nombre,creado_en,actualizado_en) "
        f"VALUES ({p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p})",
        (
            falta_id,
            colegio_id,
            'escuela',
            'pendiente_confirmacion_acudiente',
            '',
            fecha_hora,
            u.get('id'),
            (u.get('nombre') or '')[:200],
            (u.get('rol') or '')[:40],
            None,
            '',
            now,
            now,
        ),
    )


def _accion_conducta(tipo: str, sub: str) -> str:
    if tipo == 'conv_i':
        return 'Manejo: docente + mediación pedagógica'
    if tipo == 'conv_ii':
        return 'Activación de ruta | Remisión a orientación escolar.'
    if tipo == 'conv_iii':
        return 'Activación inmediata de ruta | Notificación a entidades externas (ICBF, salud, policía).'
    return ''


def _save_conducta_evidencia(file_storage, colegio_id: int) -> str:
    if not file_storage or not file_storage.filename:
        return ''
    os.makedirs(UPLOAD_CONDUCTAS, exist_ok=True)
    orig = secure_filename(file_storage.filename) or 'archivo'
    ext = os.path.splitext(orig)[1].lower()
    if ext not in ('.pdf', '.jpg', '.jpeg', '.png', '.webp', '.doc', '.docx'):
        raise ValueError('Evidencia: use PDF, imagen o Word (.pdf, .jpg, .png, .doc, .docx).')
    name = f"{colegio_id}_{secrets.token_hex(12)}{ext}"
    dest = os.path.join(UPLOAD_CONDUCTAS, name)
    file_storage.save(dest)
    return os.path.join('conductas', name).replace('\\', '/')

# ── Auth ──────────────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def dec(*a,**kw):
        if 'usuario' not in session: return jsonify({'error':'No autenticado'}),401
        return f(*a,**kw)
    return dec

def roles(*rs):
    def deco(f):
        @wraps(f)
        def dec(*a,**kw):
            if 'usuario' not in session: return jsonify({'error':'No autenticado'}),401
            if session['usuario']['rol'] not in rs: return jsonify({'error':'Sin permisos'}),403
            return f(*a,**kw)
        return dec
    return deco

def cu(): return session.get('usuario',{})

# ── Páginas ───────────────────────────────────────────────────────────────────
@app.route('/')
def index(): return redirect(url_for('dashboard') if 'usuario' in session else url_for('login_page'))

@app.route('/login')
def login_page():
    if 'usuario' in session: return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'usuario' not in session: return redirect(url_for('login_page'))
    return render_template('dashboard.html')

@app.route('/health')
def health(): return jsonify({'status':'ok','version':'7.0','db':'postgresql' if USE_PG else 'sqlite'})

# ── Auth API ──────────────────────────────────────────────────────────────────
@app.route('/api/login', methods=['POST'])
def api_login():
    d = request.json or {}
    conn = get_db()
    p = ph()
    u = execute(conn,
        f"SELECT u.*,c.nombre as col_nom FROM usuarios u LEFT JOIN colegios c ON c.id=u.colegio_id WHERE u.usuario={p} AND u.contrasena={p}",
        (d.get('usuario','').strip(), hpwd(d.get('contrasena',''))), fetch='one')
    conn.close()
    if not u: return jsonify({'ok':False,'error':'Usuario o contraseña incorrectos'}),401
    session['usuario'] = {'id':u['id'],'usuario':u['usuario'],'rol':u['rol'],'nombre':u['nombre'],
        'curso':u.get('curso',''),'colegio_id':u['colegio_id'],'colegio_nombre':u.get('col_nom','') or '',
        'estudiante_id':u.get('estudiante_id'),'asignatura':u.get('asignatura') or '',
        'telefono':u.get('telefono') or ''}
    return jsonify({'ok':True,'usuario':session['usuario']})

@app.route('/api/logout', methods=['POST'])
def api_logout(): session.clear(); return jsonify({'ok':True})

def _registro_publico_permitido():
    return os.environ.get('REGISTRATION_OPEN', '1').lower() in ('1', 'true', 'yes', 'on')

@app.route('/api/registrar-usuario', methods=['POST'])
def api_registrar_usuario():
    """Alta desde login (asigna al primer colegio). Desactivar en producción: REGISTRATION_OPEN=0."""
    if not _registro_publico_permitido():
        return jsonify({'ok': False, 'error': 'El registro público está desactivado.'}), 403
    d = request.json or {}
    rol = (d.get('rol') or '').strip()
    if rol in ('Superadmin', 'Acudiente', ''):
        return jsonify({'ok': False, 'error': 'Rol no permitido para este registro.'}), 400
    nombre = (d.get('nombre') or '').strip()
    usuario = (d.get('usuario') or '').strip()
    contrasena = d.get('contrasena') or ''
    curso = (d.get('curso') or '').strip()
    if rol == 'Director' and not curso:
        return jsonify({'ok': False, 'error': 'El director debe indicar curso.'}), 400
    if not nombre or not usuario or not contrasena:
        return jsonify({'ok': False, 'error': 'Faltan datos obligatorios.'}), 400
    conn = get_db()
    p = ph()
    col = execute(conn, 'SELECT id FROM colegios ORDER BY id LIMIT 1', fetch='one')
    cid = col['id'] if col else 1
    try:
        execute(
            conn,
            f"INSERT INTO usuarios (usuario,contrasena,rol,nombre,curso,colegio_id,asignatura) VALUES ({p},{p},{p},{p},{p},{p},{p})",
            (usuario, hpwd(contrasena), rol, nombre, curso if rol == 'Director' else '', cid, ''),
        )
        commit(conn)
        conn.close()
        return jsonify({'ok': True})
    except Exception:
        conn.close()
        return jsonify({'ok': False, 'error': 'El usuario ya existe o no se pudo crear.'}), 409

@app.route('/api/me')
@login_required
def api_me(): return jsonify(cu())

# ── Colegios ──────────────────────────────────────────────────────────────────
@app.route('/api/colegios')
@login_required
def api_colegios():
    conn=get_db(); p=ph()
    rows=execute(conn,"SELECT * FROM colegios ORDER BY nombre",fetch='all')
    result=[]
    for c in rows:
        c['num_usuarios']=execute(conn,f"SELECT COUNT(*) as n FROM usuarios WHERE colegio_id={p} AND rol!='Acudiente'",(c['id'],),fetch='one').get('n',0)
        c['num_estudiantes']=execute(conn,f"SELECT COUNT(*) as n FROM estudiantes WHERE colegio_id={p}",(c['id'],),fetch='one').get('n',0)
        c['usuarios']=execute(conn,f"SELECT id,usuario,rol,nombre,curso FROM usuarios WHERE colegio_id={p} AND rol!='Acudiente' ORDER BY rol,nombre",(c['id'],),fetch='all')
        result.append(c)
    conn.close(); return jsonify(result)

@app.route('/api/colegios', methods=['POST'])
@roles('Superadmin')
def api_colegio_crear():
    d=request.json or {}; conn=get_db(); p=ph()
    execute(conn,f"INSERT INTO colegios (nombre,nit,municipio,rector,direccion,telefono,email) VALUES ({p},{p},{p},{p},{p},{p},{p})",
        (d['nombre'],d.get('nit',''),d.get('municipio',''),d.get('rector',''),d.get('direccion',''),d.get('telefono',''),d.get('email','')))
    commit(conn); conn.close(); return jsonify({'ok':True})

@app.route('/api/colegios/<int:cid>', methods=['PATCH'])
@roles('Superadmin')
def api_colegio_editar(cid):
    d=request.json or {}; conn=get_db(); p=ph()
    execute(conn,f"UPDATE colegios SET nombre={p},nit={p},municipio={p},rector={p},direccion={p},telefono={p},email={p} WHERE id={p}",
        (d['nombre'],d.get('nit',''),d.get('municipio',''),d.get('rector',''),d.get('direccion',''),d.get('telefono',''),d.get('email',''),cid))
    commit(conn); conn.close(); return jsonify({'ok':True})

# ── Usuarios ──────────────────────────────────────────────────────────────────
@app.route('/api/usuarios')
@login_required
def api_usuarios():
    u=cu(); conn=get_db(); p=ph()
    if u['rol']=='Superadmin':
        rows=execute(conn,"SELECT u.*,c.nombre as col_nom FROM usuarios u LEFT JOIN colegios c ON c.id=u.colegio_id WHERE u.rol!='Acudiente' ORDER BY u.rol,u.nombre",fetch='all')
    else:
        rows=execute(conn,f"SELECT u.*,c.nombre as col_nom FROM usuarios u LEFT JOIN colegios c ON c.id=u.colegio_id WHERE u.colegio_id={p} AND u.rol NOT IN ('Acudiente') ORDER BY u.rol,u.nombre",(u['colegio_id'],),fetch='all')
    conn.close()
    return jsonify([{k:v for k,v in r.items() if k!='contrasena'} for r in rows])

@app.route('/api/usuarios', methods=['POST'])
@roles('Superadmin','Coordinador')
def api_usuario_crear():
    d=request.json or {}; u=cu(); conn=get_db(); p=ph()
    cid=d.get('colegio_id') if u['rol']=='Superadmin' else u['colegio_id']
    try:
        nom = (d.get('nombre') or '').strip() or nombre_desde_partes(
            d.get('apellido1', ''), d.get('apellido2', ''), d.get('nombre1', ''), d.get('nombre2', ''))
        if not nom:
            conn.close()
            return jsonify({'ok': False, 'error': 'Indique nombre o apellidos y nombres.'}), 400
        execute(conn,
            f"INSERT INTO usuarios (usuario,contrasena,rol,nombre,curso,colegio_id,asignatura,tipo_doc,documento_personal,apellido1,apellido2,nombre1,nombre2,telefono) VALUES ({p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p})",
            (d['usuario'], hpwd(d['contrasena']), d['rol'], nom, d.get('curso', ''), cid,
             d.get('asignatura', '').strip(), (d.get('tipo_doc') or '').strip()[:80],
             solo_numeros(d.get('documento_personal', '')),
             solo_letras(d.get('apellido1', '')), solo_letras(d.get('apellido2', '')),
             solo_letras(d.get('nombre1', '')), solo_letras(d.get('nombre2', '')),
             solo_numeros(d.get('telefono', ''))))
        commit(conn); conn.close(); return jsonify({'ok':True})
    except Exception as ex:
        conn.close(); return jsonify({'ok':False,'error':'El usuario ya existe'}),409

@app.route('/api/usuarios/<int:uid>', methods=['PATCH'])
@roles('Superadmin','Coordinador')
def api_usuario_editar(uid):
    d=request.json or {}; conn=get_db(); p=ph()
    asig=d.get('asignatura','')
    nom = (d.get('nombre') or '').strip() or nombre_desde_partes(
        d.get('apellido1', ''), d.get('apellido2', ''), d.get('nombre1', ''), d.get('nombre2', ''))
    if not nom:
        conn.close()
        return jsonify({'ok': False, 'error': 'Indique nombre o apellidos y nombres.'}), 400
    td = (d.get('tipo_doc') or '').strip()[:80]
    dp = solo_numeros(d.get('documento_personal', ''))
    a1, a2, n1, n2 = solo_letras(d.get('apellido1', '')), solo_letras(d.get('apellido2', '')), solo_letras(d.get('nombre1', '')), solo_letras(d.get('nombre2', ''))
    tel = solo_numeros(d.get('telefono', ''))
    if d.get('contrasena'):
        execute(conn,
            f"UPDATE usuarios SET nombre={p},rol={p},curso={p},asignatura={p},tipo_doc={p},documento_personal={p},apellido1={p},apellido2={p},nombre1={p},nombre2={p},telefono={p},contrasena={p} WHERE id={p}",
            (nom, d['rol'], d.get('curso', ''), asig.strip(), td, dp, a1, a2, n1, n2, tel, hpwd(d['contrasena']), uid))
    else:
        execute(conn,
            f"UPDATE usuarios SET nombre={p},rol={p},curso={p},asignatura={p},tipo_doc={p},documento_personal={p},apellido1={p},apellido2={p},nombre1={p},nombre2={p},telefono={p} WHERE id={p}",
            (nom, d['rol'], d.get('curso', ''), asig.strip(), td, dp, a1, a2, n1, n2, tel, uid))
    commit(conn); conn.close(); return jsonify({'ok':True})

@app.route('/api/usuarios/<int:uid>', methods=['DELETE'])
@roles('Superadmin','Coordinador')
def api_usuario_borrar(uid):
    if uid==cu()['id']: return jsonify({'ok':False,'error':'No puedes eliminarte'}),400
    conn=get_db(); p=ph()
    execute(conn,f"DELETE FROM usuarios WHERE id={p}",(uid,)); commit(conn); conn.close()
    return jsonify({'ok':True})

# ── Estudiantes ───────────────────────────────────────────────────────────────
def _crear_acudiente(conn, cedula, nombre_acu, curso, col_id, est_id):
    cedula=solo_numeros(cedula)
    if not cedula: return
    p=ph()
    ex=execute(conn,f"SELECT id FROM usuarios WHERE usuario={p}",(cedula,),fetch='one')
    if not ex:
        execute(conn,f"INSERT INTO usuarios (usuario,contrasena,rol,nombre,curso,colegio_id,estudiante_id) VALUES ({p},{p},{p},{p},{p},{p},{p})",
            (cedula,hpwd(cedula),'Acudiente',nombre_acu or 'Acudiente',curso,col_id,est_id))

@app.route('/api/estudiantes')
@login_required
def api_estudiantes():
    u=cu(); conn=get_db(); p=ph()
    curso=request.args.get('curso','')
    q=f"SELECT * FROM estudiantes WHERE colegio_id={p}"; params=[u['colegio_id'] or 1]
    if u['rol']=='Director' and u['curso'] and not curso:
        q+=f" AND curso={p}"; params.append(u['curso'])
    elif curso:
        q+=f" AND curso={p}"; params.append(curso)
    rows=execute(conn,q+" ORDER BY curso,nombre",params,fetch='all')
    conn.close(); return jsonify(rows)

def _nombre_estudiante_payload(d):
    n = nombre_desde_partes(d.get('apellido1_est', ''), d.get('apellido2_est', ''), d.get('nombre1_est', ''), d.get('nombre2_est', ''))
    if n:
        return n
    return solo_letras(d.get('nombre', ''))


def _nombre_acudiente_payload(d):
    n = nombre_desde_partes(d.get('apellido1_acu', ''), d.get('apellido2_acu', ''), d.get('nombre1_acu', ''), d.get('nombre2_acu', ''))
    if n:
        return n
    return solo_letras(d.get('acudiente', ''))


@app.route('/api/estudiantes', methods=['POST'])
@roles('Superadmin','Coordinador','Director')
def api_estudiante_crear():
    d=request.json or {}; u=cu(); conn=get_db(); p=ph()
    col_id=u['colegio_id'] or 1
    nombre=_nombre_estudiante_payload(d)
    acudiente=_nombre_acudiente_payload(d)
    cedula=solo_numeros(d.get('cedula_acudiente','') or d.get('documento_acudiente',''))
    doc_id=solo_numeros(d.get('documento_identidad',''))
    barr = (d.get('barreras') or d.get('discapacidad') or '').strip()[:200]
    if not barr:
        barr = 'Ninguna identificada'
    if not nombre or not d.get('curso'):
        conn.close(); return jsonify({'ok':False,'error':'Apellidos/nombres del estudiante y curso son obligatorios'}),400
    if not acudiente or not cedula or len(cedula) < 5:
        conn.close(); return jsonify({'ok':False,'error':'Datos completos del acudiente (nombres y documento) son obligatorios'}),400
    execute(conn,
        f"INSERT INTO estudiantes (documento_identidad,nombre,curso,discapacidad,acudiente,cedula_acudiente,telefono,direccion,colegio_id,"
        f"tipo_doc_est,apellido1_est,apellido2_est,nombre1_est,nombre2_est,barreras,"
        f"tipo_doc_acu,apellido1_acu,apellido2_acu,nombre1_acu,nombre2_acu,parentesco_acu) VALUES ({p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p})",
        (doc_id, nombre, d['curso'], barr, acudiente, cedula,
         solo_numeros(d.get('telefono', '')), d.get('direccion', '').strip(), col_id,
         (d.get('tipo_doc_est') or '')[:80],
         solo_letras(d.get('apellido1_est', '')), solo_letras(d.get('apellido2_est', '')),
         solo_letras(d.get('nombre1_est', '')), solo_letras(d.get('nombre2_est', '')), barr[:200],
         (d.get('tipo_doc_acu') or '')[:80],
         solo_letras(d.get('apellido1_acu', '')), solo_letras(d.get('apellido2_acu', '')),
         solo_letras(d.get('nombre1_acu', '')), solo_letras(d.get('nombre2_acu', '')),
         solo_letras(d.get('parentesco_acu', d.get('parentesco', '')))[:60]))
    if USE_PG:
        eid=execute(conn,"SELECT lastval() as lid",fetch='one')['lid']
    else:
        eid=execute(conn,"SELECT last_insert_rowid() as lid",fetch='one')['lid']
    _crear_acudiente(conn,cedula,acudiente,d['curso'],col_id,eid)
    commit(conn); conn.close(); return jsonify({'ok':True,'id':eid})

@app.route('/api/estudiantes/<int:eid>', methods=['PATCH'])
@roles('Superadmin','Coordinador','Director')
def api_estudiante_editar(eid):
    d=request.json or {}; conn=get_db(); p=ph()
    nombre=_nombre_estudiante_payload(d)
    acudiente=_nombre_acudiente_payload(d)
    cedula=solo_numeros(d.get('cedula_acudiente','') or d.get('documento_acudiente',''))
    doc_id=solo_numeros(d.get('documento_identidad',''))
    est=execute(conn,f"SELECT * FROM estudiantes WHERE id={p}",(eid,),fetch='one')
    barr = (d.get('barreras') or d.get('discapacidad') or '').strip()[:200]
    if not barr:
        barr = est.get('barreras') or est.get('discapacidad') or 'Ninguna identificada'
    if not nombre or not d.get('curso'):
        conn.close(); return jsonify({'ok':False,'error':'Apellidos/nombres del estudiante y curso son obligatorios'}),400
    execute(conn,
        f"UPDATE estudiantes SET documento_identidad={p},nombre={p},curso={p},discapacidad={p},acudiente={p},cedula_acudiente={p},telefono={p},direccion={p},"
        f"tipo_doc_est={p},apellido1_est={p},apellido2_est={p},nombre1_est={p},nombre2_est={p},barreras={p},"
        f"tipo_doc_acu={p},apellido1_acu={p},apellido2_acu={p},nombre1_acu={p},nombre2_acu={p},parentesco_acu={p} WHERE id={p}",
        (doc_id, nombre, d['curso'], barr, acudiente, cedula,
         solo_numeros(d.get('telefono', '')), d.get('direccion', '').strip(),
         (d.get('tipo_doc_est') or '')[:80],
         solo_letras(d.get('apellido1_est', '')), solo_letras(d.get('apellido2_est', '')),
         solo_letras(d.get('nombre1_est', '')), solo_letras(d.get('nombre2_est', '')), barr[:200],
         (d.get('tipo_doc_acu') or '')[:80],
         solo_letras(d.get('apellido1_acu', '')), solo_letras(d.get('apellido2_acu', '')),
         solo_letras(d.get('nombre1_acu', '')), solo_letras(d.get('nombre2_acu', '')),
         solo_letras(d.get('parentesco_acu', d.get('parentesco', '')))[:60], eid))
    if cedula and cedula!=solo_numeros(est.get('cedula_acudiente','') or ''):
        _crear_acudiente(conn,cedula,acudiente,d['curso'],est.get('colegio_id',1),eid)
    elif cedula:
        execute(conn,f"UPDATE usuarios SET nombre={p} WHERE usuario={p} AND rol='Acudiente'",(acudiente,cedula))
    commit(conn); conn.close(); return jsonify({'ok':True})

@app.route('/api/estudiantes/<int:eid>', methods=['DELETE'])
@roles('Superadmin','Coordinador')
def api_estudiante_borrar(eid):
    conn=get_db(); p=ph()
    execute(conn,f"DELETE FROM estudiantes WHERE id={p}",(eid,)); commit(conn); conn.close()
    return jsonify({'ok':True})

def _row_csv(linea):
    linea = linea.strip()
    if not linea:
        return []
    try:
        return next(csv.reader(StringIO(linea)))
    except Exception:
        return [x.strip() for x in linea.split(',')]


def _import_insert_estudiante(conn, col_id, curso, doc_id, nombre, barr, acudiente, cedula, telefono, direccion,
                              tipo_doc_est, ap1e, ap2e, n1e, n2e, tipo_doc_acu, ap1a, ap2a, n1a, n2a, parentesco):
    p = ph()
    execute(conn,
        f"INSERT INTO estudiantes (documento_identidad,nombre,curso,discapacidad,acudiente,cedula_acudiente,telefono,direccion,colegio_id,"
        f"tipo_doc_est,apellido1_est,apellido2_est,nombre1_est,nombre2_est,barreras,"
        f"tipo_doc_acu,apellido1_acu,apellido2_acu,nombre1_acu,nombre2_acu,parentesco_acu) VALUES ({p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p})",
        (doc_id, nombre, curso, barr, acudiente, cedula, telefono, direccion, col_id,
         (tipo_doc_est or '')[:80], ap1e, ap2e, n1e, n2e, barr[:200],
         (tipo_doc_acu or '')[:80], ap1a, ap2a, n1a, n2a, parentesco[:60]))
    if USE_PG:
        eid = execute(conn, "SELECT lastval() as lid", fetch='one')['lid']
    else:
        eid = execute(conn, "SELECT last_insert_rowid() as lid", fetch='one')['lid']
    if cedula:
        _crear_acudiente(conn, cedula, acudiente, curso, col_id, eid)
    return eid


@app.route('/api/estudiantes/importar', methods=['POST'])
@roles('Superadmin','Coordinador','Director')
def api_importar_estudiantes():
    d = request.json or {}
    u = cu()
    conn = get_db()
    col_id = u['colegio_id'] or 1
    curso_def = (d.get('curso_default') or '').strip()
    count = 0
    errores = []
    for i, raw in enumerate(d.get('texto', '').split('\n'), 1):
        linea = raw.strip()
        if not linea or linea.startswith('#'):
            continue
        pts = [x.strip() for x in _row_csv(linea)]
        if not pts:
            continue
        low0 = pts[0].lower().replace('_', ' ')
        if low0 in ('tipo doc est', 'tipo_doc_est'):
            continue
        # Formato extendido (17 columnas): alineado al formulario de estudiante
        if len(pts) >= 15:
            tipo_doc_est = pts[0]
            doc_id = solo_numeros(pts[1])
            ap1e = solo_letras(pts[2])
            ap2e = solo_letras(pts[3])
            n1e = solo_letras(pts[4])
            n2e = solo_letras(pts[5]) if len(pts) > 5 else ''
            curso = (pts[6] or '').strip() or curso_def
            barr = (pts[7] or '').strip()[:200] if len(pts) > 7 else ''
            if not barr:
                barr = 'Ninguna identificada'
            tipo_doc_acu = pts[8] if len(pts) > 8 else ''
            cedula = solo_numeros(pts[9]) if len(pts) > 9 else ''
            ap1a = solo_letras(pts[10]) if len(pts) > 10 else ''
            ap2a = solo_letras(pts[11]) if len(pts) > 11 else ''
            n1a = solo_letras(pts[12]) if len(pts) > 12 else ''
            n2a = solo_letras(pts[13]) if len(pts) > 13 else ''
            parentesco = (pts[14] or '').strip()[:60] if len(pts) > 14 else ''
            telefono = solo_numeros(pts[15]) if len(pts) > 15 else ''
            direccion = pts[16].strip() if len(pts) > 16 else ''
            nombre = nombre_desde_partes(ap1e, ap2e, n1e, n2e)
            acudiente = nombre_desde_partes(ap1a, ap2a, n1a, n2a)
            if not ap1e or not n1e or not curso:
                errores.append(f'Línea {i}: estudiante requiere apellido 1, nombre 1 y curso')
                continue
            if not acudiente or len(cedula) < 5:
                errores.append(f'Línea {i}: acudiente (nombres) y documento (mín. 5 dígitos) obligatorios')
                continue
            _import_insert_estudiante(conn, col_id, curso, doc_id, nombre, barr, acudiente, cedula, telefono, direccion,
                                      tipo_doc_est, ap1e, ap2e, n1e, n2e, tipo_doc_acu, ap1a, ap2a, n1a, n2a, parentesco)
            count += 1
            continue
        # Formato legado (8 columnas): nombre completo, curso, barreras/discapacidad, acudiente completo, doc acudiente, tel, dir, doc estudiante
        nombre = solo_letras(pts[0]) if pts else ''
        curso = (pts[1] or '').strip() or curso_def
        barr = (pts[2] or '').strip()[:200] if len(pts) > 2 else ''
        if not barr:
            barr = 'Ninguna identificada'
        acudiente = solo_letras(pts[3]) if len(pts) > 3 else ''
        cedula = solo_numeros(pts[4]) if len(pts) > 4 else ''
        telefono = solo_numeros(pts[5]) if len(pts) > 5 else ''
        direccion = pts[6].strip() if len(pts) > 6 else ''
        doc_id = solo_numeros(pts[7]) if len(pts) > 7 else ''
        if not nombre or not curso:
            errores.append(f'Línea {i}: falta nombre completo o curso (o use formato extendido de 17 columnas)')
            continue
        if not acudiente or len(cedula) < 5:
            errores.append(f'Línea {i}: acudiente y documento del acudiente (mín. 5 dígitos) obligatorios')
            continue
        _import_insert_estudiante(conn, col_id, curso, doc_id, nombre, barr, acudiente, cedula, telefono, direccion,
                                  '', '', '', '', '', '', '', '', '', '', '')
        count += 1
    commit(conn)
    conn.close()
    return jsonify({'ok': True, 'insertados': count, 'errores': errores})

# ── Señales de atención (bienestar; no constituye diagnóstico) ───────────────
_SENALES_CAT = frozenset({'alimentacion','familia_acomp','abandono_riesgo','bienestar_general','discapacidad_apoyo','otro'})

@app.route('/api/senales-atencion')
@login_required
def api_senales_listar():
    u=cu()
    if u['rol']=='Acudiente':
        return jsonify({'error':'Sin permisos'}),403
    conn=get_db(); p=ph()
    if u['rol']=='Superadmin' and not u.get('colegio_id'):
        rows=execute(conn,"SELECT s.* FROM senales_atencion s ORDER BY s.fecha_registro DESC LIMIT 200",fetch='all')
    else:
        q=f"SELECT s.* FROM senales_atencion s WHERE s.colegio_id={p}"; prm=[u['colegio_id'] or 1]
        if u['rol']=='Docente':
            q+=f" AND s.registrado_por_id={p}"; prm.append(u['id'])
        elif u['rol']=='Director' and u.get('curso'):
            q+=f" AND s.curso={p}"; prm.append(u['curso'])
        q+=" ORDER BY s.fecha_registro DESC LIMIT 200"
        rows=execute(conn,q,prm,fetch='all')
    conn.close()
    return jsonify(rows)

@app.route('/api/senales-atencion', methods=['POST'])
@roles('Superadmin','Coordinador','Orientador','Director','Docente')
def api_senales_crear():
    u = cu()
    file_storage = None
    if request.content_type and 'multipart/form-data' in (request.content_type or ''):
        d = {k: (request.form.get(k) or '').strip() for k in request.form}
        file_storage = request.files.get('evidencia')
    else:
        d = request.json or {}
    conn = get_db()
    p = ph()
    cid = u['colegio_id'] or 1
    fe = datetime.now().strftime('%Y-%m-%d')

    tipo_con = (d.get('tipo_conducta') or '').strip()
    if tipo_con:
        if tipo_con not in _CONDUCTA_TIPOS:
            conn.close()
            return jsonify({'ok': False, 'error': 'Tipo de conducta no válido'}), 400
        sub = (d.get('subtipo') or d.get('subtipo_clave') or '').strip()
        if sub not in _SUBS_POR_TIPO.get(tipo_con, frozenset()):
            conn.close()
            return jsonify({'ok': False, 'error': 'La opción no corresponde al tipo seleccionado.'}), 400
        urg = (d.get('urgencia') or '').strip()
        if urg not in _URGENCIAS:
            conn.close()
            return jsonify({'ok': False, 'error': 'Nivel de urgencia no válido.'}), 400
        obs = (d.get('descripcion_objetiva') or d.get('observacion') or '').strip()
        if len(obs) < 10:
            conn.close()
            return jsonify({'ok': False, 'error': 'La descripción objetiva requiere al menos 10 caracteres.'}), 400
        try:
            eid = int(d.get('estudiante_id') or 0)
        except (TypeError, ValueError):
            eid = 0
        if not eid:
            conn.close()
            return jsonify({'ok': False, 'error': 'Seleccione estudiante'}), 400
        est = execute(conn, f"SELECT * FROM estudiantes WHERE id={p} AND colegio_id={p}", (eid, cid), fetch='one')
        if not est:
            conn.close()
            return jsonify({'ok': False, 'error': 'Estudiante no encontrado'}), 404
        if u['rol'] == 'Director' and u.get('curso') and est.get('curso') != u['curso']:
            conn.close()
            return jsonify({'ok': False, 'error': 'Estudiante fuera de su curso'}), 403
        ev_path = ''
        if file_storage and file_storage.filename:
            try:
                ev_path = _save_conducta_evidencia(file_storage, cid)
            except ValueError as ex:
                conn.close()
                return jsonify({'ok': False, 'error': str(ex)}), 400
        acc = _accion_conducta(tipo_con, sub)
        execute(
            conn,
            f"INSERT INTO senales_atencion (colegio_id,estudiante_id,estudiante_nombre,curso,categoria,observacion,"
            f"registrado_por_id,registrado_por_nombre,registrado_rol,fecha_registro,estado,nota_seguimiento,"
            f"tipo_conducta,subtipo_clave,accion_derivada,urgencia,evidencia_path) VALUES ({p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p})",
            (
                cid,
                eid,
                est['nombre'],
                est.get('curso') or '',
                'conducta_riesgo',
                obs,
                u['id'],
                u['nombre'],
                u['rol'],
                fe,
                'abierta',
                '',
                tipo_con,
                sub,
                acc,
                urg,
                ev_path,
            ),
        )
        if USE_PG:
            nid = execute(conn, "SELECT lastval() as lid", fetch='one')['lid']
        else:
            nid = execute(conn, "SELECT last_insert_rowid() as lid", fetch='one')['lid']
        commit(conn)
        conn.close()
        return jsonify({'ok': True, 'id': nid})

    cat = (d.get('categoria') or '').strip()
    if cat not in _SENALES_CAT:
        conn.close()
        return jsonify({'ok': False, 'error': 'Categoría no válida'}), 400
    obs = (d.get('observacion') or '').strip()
    if len(obs) < 10:
        conn.close()
        return jsonify({'ok': False, 'error': 'Amplíe la observación (mínimo 10 caracteres). No incluya diagnósticos clínicos.'}), 400
    eid = d.get('estudiante_id')
    if not eid:
        conn.close()
        return jsonify({'ok': False, 'error': 'Seleccione estudiante'}), 400
    est = execute(conn, f"SELECT * FROM estudiantes WHERE id={p} AND colegio_id={p}", (eid, cid), fetch='one')
    if not est:
        conn.close()
        return jsonify({'ok': False, 'error': 'Estudiante no encontrado'}), 404
    if u['rol'] == 'Director' and u.get('curso') and est.get('curso') != u['curso']:
        conn.close()
        return jsonify({'ok': False, 'error': 'Estudiante fuera de su curso'}), 403
    execute(
        conn,
        f"INSERT INTO senales_atencion (colegio_id,estudiante_id,estudiante_nombre,curso,categoria,observacion,registrado_por_id,registrado_por_nombre,registrado_rol,fecha_registro,estado,nota_seguimiento) VALUES ({p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p})",
        (cid, eid, est['nombre'], est.get('curso') or '', cat, obs, u['id'], u['nombre'], u['rol'], fe, 'abierta', ''),
    )
    if USE_PG:
        nid = execute(conn, "SELECT lastval() as lid", fetch='one')['lid']
    else:
        nid = execute(conn, "SELECT last_insert_rowid() as lid", fetch='one')['lid']
    commit(conn)
    conn.close()
    return jsonify({'ok': True, 'id': nid})

@app.route('/api/senales-atencion/<int:sid>', methods=['PATCH'])
@roles('Superadmin','Coordinador','Orientador')
def api_senales_actualizar(sid):
    d=request.json or {}; u=cu()
    conn=get_db(); p=ph()
    s=execute(conn,f"SELECT * FROM senales_atencion WHERE id={p}",(sid,),fetch='one')
    if not s or (s['colegio_id']!=(u.get('colegio_id') or 1) and u['rol']!='Superadmin'):
        conn.close(); return jsonify({'error':'No encontrada'}),404
    estado=d.get('estado')
    nota=(d.get('nota_seguimiento') or '').strip()
    if estado and estado not in ('abierta','en_seguimiento','cerrada'):
        conn.close(); return jsonify({'error':'Estado inválido'}),400
    if estado:
        execute(conn,f"UPDATE senales_atencion SET estado={p},nota_seguimiento={p} WHERE id={p}",(estado,nota,sid))
    elif nota is not None:
        execute(conn,f"UPDATE senales_atencion SET nota_seguimiento={p} WHERE id={p}",(nota,sid))
    commit(conn); conn.close()
    return jsonify({'ok':True})


@app.route('/api/senales-atencion/<int:sid>/evidencia')
@login_required
def api_senales_evidencia(sid):
    u = cu()
    if u['rol'] == 'Acudiente':
        return jsonify({'error': 'Sin permisos'}), 403
    conn = get_db()
    p = ph()
    s = execute(conn, f"SELECT * FROM senales_atencion WHERE id={p}", (sid,), fetch='one')
    conn.close()
    if not s:
        return jsonify({'error': 'No encontrada'}), 404
    if s.get('colegio_id') != (u.get('colegio_id') or 1) and u['rol'] != 'Superadmin':
        return jsonify({'error': 'No autorizado'}), 403
    if u['rol'] == 'Docente' and s.get('registrado_por_id') != u.get('id'):
        return jsonify({'error': 'No autorizado'}), 403
    if u['rol'] == 'Director' and u.get('curso') and s.get('curso') != u['curso']:
        return jsonify({'error': 'No autorizado'}), 403
    rel = (s.get('evidencia_path') or '').strip()
    if not rel or '..' in rel:
        return jsonify({'error': 'Sin evidencia'}), 404
    full = os.path.normpath(os.path.join(UPLOAD_FOLDER, rel.replace('/', os.sep)))
    if not full.startswith(os.path.normpath(UPLOAD_FOLDER)):
        return jsonify({'error': 'Ruta inválida'}), 400
    if not os.path.isfile(full):
        return jsonify({'error': 'Archivo no encontrado'}), 404
    return send_file(full, as_attachment=True, download_name=os.path.basename(full))


# ── Asistencia ────────────────────────────────────────────────────────────────
@app.route('/api/asistencia/tomas')
@login_required
def api_asistencia_tomas():
    u=cu()
    if u['rol']=='Acudiente':
        return jsonify({'error':'Sin permisos'}),403
    conn=get_db(); p=ph(); cid=u['colegio_id'] or 1
    q=f"SELECT t.* FROM asistencia_toma t WHERE t.colegio_id={p}"; prm=[cid]
    if u['rol']=='Director' and u.get('curso'):
        q+=f" AND t.curso={p}"; prm.append(u['curso'])
    if u['rol']=='Docente':
        q+=f" AND t.docente_id={p}"; prm.append(u['id'])
    cur=request.args.get('curso','')
    if cur:
        q+=f" AND t.curso={p}"; prm.append(cur)
    fd=request.args.get('desde','')
    if fd:
        q+=f" AND t.fecha>={p}"; prm.append(fd)
    fh=request.args.get('hasta','')
    if fh:
        q+=f" AND t.fecha<={p}"; prm.append(fh)
    q+=" ORDER BY t.fecha DESC, t.id DESC LIMIT 100"
    tomas=execute(conn,q,prm,fetch='all')
    for t in tomas:
        t['detalles']=execute(conn,f"SELECT * FROM asistencia_detalle WHERE toma_id={p} ORDER BY estudiante_nombre",(t['id'],),fetch='all')
    conn.close()
    return jsonify(tomas)

@app.route('/api/asistencia/toma', methods=['POST'])
@roles('Superadmin','Coordinador','Director','Docente')
def api_asistencia_crear_toma():
    d=request.json or {}; u=cu()
    fecha=(d.get('fecha') or '').strip()
    curso=(d.get('curso') or '').strip()
    asignatura=(d.get('asignatura') or '').strip() or (u.get('asignatura') or '')
    lineas=d.get('lineas') or []
    if not fecha or not curso:
        return jsonify({'ok':False,'error':'Fecha y curso obligatorios'}),400
    if u['rol']=='Director' and u.get('curso') and curso!=u['curso']:
        return jsonify({'ok':False,'error':'Solo su curso asignado'}),403
    conn=get_db(); p=ph(); cid=u['colegio_id'] or 1
    creado=datetime.now().strftime('%Y-%m-%d %H:%M')
    execute(conn,f"INSERT INTO asistencia_toma (colegio_id,fecha,curso,asignatura,docente_id,docente_nombre,creado_en) VALUES ({p},{p},{p},{p},{p},{p},{p})",
        (cid,fecha,curso,asignatura,u['id'],u['nombre'],creado))
    if USE_PG:
        tid=execute(conn,"SELECT lastval() as lid",fetch='one')['lid']
    else:
        tid=execute(conn,"SELECT last_insert_rowid() as lid",fetch='one')['lid']
    for ln in lineas:
        eid=ln.get('estudiante_id')
        if not eid: continue
        est=execute(conn,f"SELECT nombre,curso FROM estudiantes WHERE id={p} AND colegio_id={p}",(eid,cid),fetch='one')
        if not est or est['curso']!=curso: continue
        jus=ln.get('justificada')
        ji=1 if jus is True else (0 if jus is False else None)
        execute(conn,f"INSERT INTO asistencia_detalle (toma_id,estudiante_id,estudiante_nombre,ausente,justificada) VALUES ({p},{p},{p},{p},{p})",
            (tid,eid,est['nombre'],1,ji))
    commit(conn); conn.close()
    return jsonify({'ok':True,'toma_id':tid})

@app.route('/api/asistencia/linea/<int:lid>', methods=['PATCH'])
@roles('Superadmin','Coordinador','Director')
def api_asistencia_linea_justificar(lid):
    d=request.json or {}; u=cu()
    jus=d.get('justificada')
    if jus not in (True,False):
        return jsonify({'error':'justificada debe ser true o false'}),400
    conn=get_db(); p=ph()
    row=execute(conn,
        f"SELECT d.*,t.curso,t.colegio_id FROM asistencia_detalle d JOIN asistencia_toma t ON t.id=d.toma_id WHERE d.id={p}",(lid,),fetch='one')
    if not row or row['colegio_id']!=(u.get('colegio_id') or 1):
        conn.close(); return jsonify({'error':'No encontrada'}),404
    if u['rol']=='Director' and u.get('curso') and row['curso']!=u['curso']:
        conn.close(); return jsonify({'error':'Sin permisos'}),403
    ji=1 if jus else 0
    execute(conn,f"UPDATE asistencia_detalle SET justificada={p} WHERE id={p}",(ji,lid))
    commit(conn); conn.close()
    return jsonify({'ok':True})

@app.route('/api/me/asignatura', methods=['PATCH'])
@login_required
def api_me_asignatura():
    u=cu()
    if u['rol']!='Docente':
        return jsonify({'error':'Solo docentes'}),403
    asig=(request.json or {}).get('asignatura','')
    asig=str(asig).strip()[:120]
    conn=get_db(); p=ph()
    execute(conn,f"UPDATE usuarios SET asignatura={p} WHERE id={p}",(asig,u['id']))
    commit(conn); conn.close()
    session['usuario']['asignatura']=asig
    return jsonify({'ok':True})

# ── Catálogo ──────────────────────────────────────────────────────────────────
@app.route('/api/catalogo')
@login_required
def api_catalogo():
    u=cu(); conn=get_db(); p=ph()
    tipo=request.args.get('tipo','')
    q=f"SELECT * FROM catalogo_faltas WHERE colegio_id={p}"; params=[u['colegio_id'] or 1]
    if tipo: q+=f" AND tipo={p}"; params.append(tipo)
    rows=execute(conn,q+" ORDER BY tipo,descripcion",params,fetch='all')
    conn.close(); return jsonify(rows)

@app.route('/api/catalogo', methods=['POST'])
@roles('Superadmin','Coordinador')
def api_catalogo_crear():
    d=request.json or {}; u=cu(); conn=get_db(); p=ph()
    execute(conn,f"INSERT INTO catalogo_faltas (tipo,descripcion,protocolo,sancion,colegio_id) VALUES ({p},{p},{p},{p},{p})",
        (d['tipo'],d['descripcion'],d.get('protocolo',''),d.get('sancion',''),u['colegio_id'] or 1))
    commit(conn); conn.close(); return jsonify({'ok':True})

@app.route('/api/catalogo/<int:cid>', methods=['PATCH'])
@roles('Superadmin','Coordinador')
def api_catalogo_editar(cid):
    d=request.json or {}; conn=get_db(); p=ph()
    execute(conn,f"UPDATE catalogo_faltas SET protocolo={p},sancion={p} WHERE id={p}",
        (d.get('protocolo',''),d.get('sancion',''),cid))
    commit(conn); conn.close(); return jsonify({'ok':True})

@app.route('/api/catalogo/<int:cid>', methods=['DELETE'])
@roles('Superadmin','Coordinador')
def api_catalogo_borrar(cid):
    conn=get_db(); p=ph()
    execute(conn,f"DELETE FROM catalogo_faltas WHERE id={p}",(cid,)); commit(conn); conn.close()
    return jsonify({'ok':True})


@app.route('/api/catalogo/importar', methods=['POST'])
@roles('Superadmin', 'Coordinador')
def api_catalogo_importar():
    d = request.json or {}
    u = cu()
    cid = u['colegio_id'] or 1
    items = d.get('items')
    if not items and d.get('texto'):
        items = []
        for i, linea in enumerate(d.get('texto', '').split('\n'), 1):
            linea = linea.strip()
            if not linea or linea.startswith('#'):
                continue
            parts = [x.strip() for x in linea.split(',')]
            if len(parts) < 2:
                continue
            items.append({'tipo': parts[0], 'descripcion': parts[1]})
    if not items:
        return jsonify({'ok': False, 'error': 'Envíe items[] o texto con líneas: Tipo I,Descripción'}), 400
    conn = get_db()
    p = ph()
    n = 0
    for it in items:
        tipo = (it.get('tipo') or '').strip()
        desc = (it.get('descripcion') or '').strip()
        if tipo not in ('Tipo I', 'Tipo II', 'Tipo III') or not desc:
            continue
        execute(
            conn,
            f"INSERT INTO catalogo_faltas (tipo,descripcion,protocolo,sancion,colegio_id) VALUES ({p},{p},{p},{p},{p})",
            (tipo, desc[:500], '', '', cid),
        )
        n += 1
    commit(conn)
    conn.close()
    return jsonify({'ok': True, 'insertados': n})


# ── Faltas ────────────────────────────────────────────────────────────────────
@app.route('/api/faltas')
@login_required
def api_faltas():
    u=cu(); anio=request.args.get('anio',str(datetime.now().year))
    conn=get_db(); q,p=fq(u,anio)
    faltas=execute(conn,q,p,fetch='all')
    ph_=ph()
    for f in faltas:
        f['anotaciones']=execute(conn,f"SELECT * FROM anotaciones WHERE falta_id={ph_} ORDER BY id",(f['id'],),fetch='all')
        _attach_cita_falta(conn, f)
        enriquecer_falta_gestion(f)
    conn.close(); return jsonify(faltas)

@app.route('/api/faltas/<int:fid>')
@login_required
def api_falta_detalle(fid):
    u=cu(); conn=get_db(); p=ph()
    f=execute(conn,
        f"SELECT f.*,e.acudiente,e.cedula_acudiente,e.telefono as tel_acudiente,e.discapacidad,e.documento_identidad "
        f"FROM faltas f LEFT JOIN estudiantes e ON e.id=f.estudiante_id WHERE f.id={p}",(fid,),fetch='one')
    if not f: conn.close(); return jsonify({'error':'No encontrada'}),404
    if u['rol']=='Acudiente' and f.get('estudiante_id')!=u.get('estudiante_id'):
        conn.close(); return jsonify({'error':'Sin permisos'}),403
    f['anotaciones']=execute(conn,f"SELECT * FROM anotaciones WHERE falta_id={p} ORDER BY id",(fid,),fetch='all')
    _attach_cita_falta(conn, f)
    enriquecer_falta_gestion(f)
    conn.close(); return jsonify(f)


@app.route('/api/faltas/<int:fid>/gestion', methods=['PATCH'])
@roles('Coordinador', 'Superadmin')
def api_falta_gestion(fid):
    d = request.json or {}
    if 'decision' not in d:
        return jsonify({'ok': False, 'error': 'Indique decision: cerrada, en_revision o null (automático)'}), 400
    dec = d.get('decision')
    if dec in (None, '', 'null', 'automatico'):
        val = None
    elif dec in ('cerrada', 'en_revision'):
        val = dec
    else:
        return jsonify({'ok': False, 'error': 'decision debe ser cerrada, en_revision o null'}), 400
    u = cu()
    conn = get_db()
    p = ph()
    f = execute(conn, f"SELECT * FROM faltas WHERE id={p}", (fid,), fetch='one')
    if not f:
        conn.close()
        return jsonify({'ok': False, 'error': 'No encontrada'}), 404
    if u['rol'] != 'Superadmin' and f.get('colegio_id') != (u.get('colegio_id') or 1):
        conn.close()
        return jsonify({'ok': False, 'error': 'Sin permisos'}), 403
    execute(conn, f"UPDATE faltas SET gestion_coordinador={p} WHERE id={p}", (val, fid))
    commit(conn)
    conn.close()
    return jsonify({'ok': True})

@app.route('/api/faltas', methods=['POST'])
@roles('Superadmin','Coordinador','Director','Docente')
def api_falta_crear():
    d=request.json or {}; u=cu(); conn=get_db(); p=ph()
    cid=u['colegio_id'] or 1
    try:
        anio=int(d.get('anio', datetime.now().year))
    except (TypeError, ValueError):
        anio=datetime.now().year
    est_id=d.get('estudiante_id')
    est_nom=(d.get('estudiante') or '').strip()
    if est_id:
        row=execute(conn,f"SELECT id,nombre FROM estudiantes WHERE id={p} AND colegio_id={p}",(int(est_id),cid),fetch='one')
        if row:
            est_id=row['id']
            est_nom=row.get('nombre') or est_nom
    if not est_nom:
        est=execute(conn,f"SELECT id,nombre FROM estudiantes WHERE nombre={p} AND colegio_id={p}",(d.get('estudiante',''),cid),fetch='one')
        if est:
            est_id=est['id']
            est_nom=est['nombre']
    if not est_nom:
        conn.close()
        return jsonify({'ok':False,'error':'Estudiante no válido'}),400
    cat=execute(conn,f"SELECT protocolo,sancion FROM catalogo_faltas WHERE descripcion={p} AND colegio_id={p}",
        (d['falta_especifica'],cid),fetch='one')
    execute(conn,
        f"INSERT INTO faltas (anio,fecha,curso,estudiante,estudiante_id,tipo_falta,falta_especifica,"
        f"descripcion,proceso_inicial,protocolo_aplicado,sancion_aplicada,docente,colegio_id) "
        f"VALUES ({p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p})",
        (anio,datetime.now().strftime('%Y-%m-%d'),d['curso'],est_nom,est_id,
         d['tipo_falta'],d['falta_especifica'],d['descripcion'],d['proceso_inicial'],
         cat.get('protocolo','') if cat else '',cat.get('sancion','') if cat else '',
         u['nombre'],cid))
    if USE_PG:
        fid = execute(conn, "SELECT lastval() as lid", fetch='one')['lid']
    else:
        fid = execute(conn, "SELECT last_insert_rowid() as lid", fetch='one')['lid']
    cc = d.get('cita_acudiente') or {}
    if isinstance(cc, dict) and cc.get('activar'):
        fh = (cc.get('fecha_hora') or '').strip()
        if fh:
            try:
                _cancelar_citas_abiertas(conn, fid)
                _insert_cita_escuela(conn, fid, cid, fh, u)
            except Exception:
                pass
    commit(conn); conn.close(); return jsonify({'ok': True, 'id': fid})

@app.route('/api/faltas/<int:fid>/anotaciones', methods=['POST'])
@roles('Superadmin','Coordinador','Director','Orientador','Docente')
def api_anotacion(fid):
    d=request.json or {}; u=cu(); txt=d.get('texto','').strip()
    if not txt: return jsonify({'error':'Texto vacío'}),400
    conn=get_db(); p=ph()
    f=execute(conn,f"SELECT * FROM faltas WHERE id={p}",(fid,),fetch='one')
    if not f: conn.close(); return jsonify({'error':'No encontrada'}),404
    if u['rol']=='Docente' and f.get('docente')!=u['nombre']:
        conn.close(); return jsonify({'error':'Sin permisos'}),403
    execute(conn,f"INSERT INTO anotaciones (falta_id,rol,autor,fecha,texto) VALUES ({p},{p},{p},{p},{p})",
        (fid,u['rol'],u['nombre'],datetime.now().strftime('%Y-%m-%d'),txt))
    commit(conn); conn.close(); return jsonify({'ok':True})


@app.route('/api/me/citas-pendientes')
@login_required
def api_me_citas_pendientes():
    u = cu()
    cid = u.get('colegio_id') or 1
    conn = get_db()
    p = ph()
    por_confirmar = []
    por_agendar = []
    if u['rol'] == 'Acudiente':
        eid = u.get('estudiante_id')
        if eid:
            por_confirmar = execute(
                conn,
                f"SELECT c.*, f.estudiante, f.falta_especifica, f.fecha as falta_fecha, f.curso "
                f"FROM citas_acudiente c JOIN faltas f ON f.id=c.falta_id "
                f"WHERE f.estudiante_id={p} AND f.colegio_id={p} AND c.estado='pendiente_confirmacion_acudiente'",
                (eid, cid),
                fetch='all',
            ) or []
    elif u['rol'] in CITA_ROLES_DESTINO:
        por_agendar = execute(
            conn,
            f"SELECT c.*, f.estudiante, f.falta_especifica, f.fecha as falta_fecha, f.curso "
            f"FROM citas_acudiente c JOIN faltas f ON f.id=c.falta_id "
            f"WHERE c.colegio_id={p} AND c.estado='pendiente_agenda' AND c.rol_destino={p}",
            (cid, u['rol']),
            fetch='all',
        ) or []
    conn.close()
    return jsonify({'por_confirmar': por_confirmar, 'por_agendar': por_agendar})


@app.route('/api/faltas/<int:fid>/cita/solicitud', methods=['POST'])
@roles('Acudiente')
def api_cita_solicitud(fid):
    d = request.json or {}
    rol_dest = (d.get('rol_destino') or '').strip()
    if rol_dest not in CITA_ROLES_DESTINO:
        return jsonify({'ok': False, 'error': 'Rol no válido'}), 400
    u = cu()
    eid = u.get('estudiante_id')
    if not eid:
        return jsonify({'ok': False, 'error': 'Sin estudiante asociado'}), 400
    conn = get_db()
    p = ph()
    cid = u.get('colegio_id') or 1
    f = execute(conn, f"SELECT * FROM faltas WHERE id={p} AND colegio_id={p}", (fid, cid), fetch='one')
    if not f or int(f.get('estudiante_id') or 0) != int(eid):
        conn.close()
        return jsonify({'ok': False, 'error': 'Falta no encontrada'}), 404
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    _cancelar_citas_abiertas(conn, fid)
    execute(
        conn,
        f"INSERT INTO citas_acudiente (falta_id,colegio_id,origen,estado,rol_destino,fecha_hora,"
        f"creado_por_id,creado_por_nombre,creado_por_rol,agenda_por_id,agenda_por_nombre,creado_en,actualizado_en) "
        f"VALUES ({p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p})",
        (
            fid,
            cid,
            'acudiente',
            'pendiente_agenda',
            rol_dest,
            '',
            u.get('id'),
            (u.get('nombre') or '')[:200],
            'Acudiente',
            None,
            '',
            now,
            now,
        ),
    )
    commit(conn)
    conn.close()
    return jsonify({'ok': True})


@app.route('/api/citas/<int:cid>', methods=['PATCH'])
@login_required
def api_cita_patch(cid):
    d = request.json or {}
    u = cu()
    conn = get_db()
    p = ph()
    c = execute(conn, f"SELECT * FROM citas_acudiente WHERE id={p}", (cid,), fetch='one')
    if not c:
        conn.close()
        return jsonify({'ok': False, 'error': 'No encontrada'}), 404
    if c.get('colegio_id') != (u.get('colegio_id') or 1) and u['rol'] != 'Superadmin':
        conn.close()
        return jsonify({'ok': False, 'error': 'Sin permisos'}), 403

    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    estado = c.get('estado') or ''

    if u['rol'] == 'Acudiente':
        frow = execute(conn, f"SELECT * FROM faltas WHERE id={p}", (c['falta_id'],), fetch='one')
        if not frow or int(frow.get('estudiante_id') or 0) != int(u.get('estudiante_id') or 0):
            conn.close()
            return jsonify({'ok': False, 'error': 'Sin permisos'}), 403
        acc = (d.get('accion') or '').strip().lower()
        if estado != 'pendiente_confirmacion_acudiente':
            conn.close()
            return jsonify({'ok': False, 'error': 'Estado de cita no permite esta acción'}), 400
        if acc == 'confirmar':
            execute(conn, f"UPDATE citas_acudiente SET estado='confirmada', actualizado_en={p} WHERE id={p}", (now, cid))
        elif acc == 'rechazar':
            execute(conn, f"UPDATE citas_acudiente SET estado='rechazada', actualizado_en={p} WHERE id={p}", (now, cid))
        else:
            conn.close()
            return jsonify({'ok': False, 'error': 'Use accion: confirmar o rechazar'}), 400
        commit(conn)
        conn.close()
        return jsonify({'ok': True})

    if u['rol'] not in CITA_ROLES_DESTINO and u['rol'] != 'Superadmin':
        conn.close()
        return jsonify({'ok': False, 'error': 'Sin permisos'}), 403

    if estado == 'pendiente_agenda' and (u['rol'] == c.get('rol_destino') or u['rol'] == 'Superadmin'):
        fh = (d.get('fecha_hora') or '').strip()
        if not fh:
            conn.close()
            return jsonify({'ok': False, 'error': 'Indique fecha_hora (formato fecha y hora local)'}), 400
        execute(
            conn,
            f"UPDATE citas_acudiente SET fecha_hora={p}, estado='pendiente_confirmacion_acudiente', "
            f"agenda_por_id={p}, agenda_por_nombre={p}, actualizado_en={p} WHERE id={p}",
            (fh, u.get('id'), (u.get('nombre') or '')[:200], now, cid),
        )
        commit(conn)
        conn.close()
        return jsonify({'ok': True})

    conn.close()
    return jsonify({'ok': False, 'error': 'No puede actualizar esta cita en su estado actual'}), 400


# ── Reportes JSON ─────────────────────────────────────────────────────────────
@app.route('/api/reportes')
@login_required
def api_reportes():
    u=cu(); anio=request.args.get('anio',str(datetime.now().year))
    conn=get_db(); q,p=fq(u,anio)
    faltas=execute(conn,q,p,fetch='all'); conn.close()
    ests_t1=Counter(f['estudiante'] for f in faltas if f['tipo_falta']=='Tipo I')
    reincidencias_t1=[{'estudiante':e,'count':n,'sugerencia':'Activar proceso Tipo II: citación de acudiente y compromiso formal.'} for e,n in ests_t1.items() if n>=3]
    ests_all=Counter(f['estudiante'] for f in faltas)
    tipos=Counter(f['tipo_falta'] for f in faltas)
    cursos=Counter(f['curso'] for f in faltas)
    docs=Counter(f['docente'] for f in faltas)
    meses=Counter(f['fecha'][5:7] for f in faltas if f['fecha'])
    sugerencias=generar_sugerencias(faltas)
    return jsonify({'total':len(faltas),'por_tipo':dict(tipos),'por_curso':dict(cursos),
        'top_estudiantes':ests_all.most_common(10),'por_docente':dict(docs),'por_mes':dict(meses),
        'reincidentes':[e for e,n in ests_all.items() if n>=4],
        'reincidencias_tipo_i':reincidencias_t1,'sugerencias':sugerencias})

# ── Export CSV ────────────────────────────────────────────────────────────────
@app.route('/api/exportar-csv')
@login_required
def api_exportar_csv():
    u = cu()
    anio = request.args.get('anio', str(datetime.now().year))
    conn = get_db()
    q, params = fq(u, anio)
    faltas = execute(conn, q, params, fetch='all')
    conn.close()
    header = ['id', 'anio', 'fecha', 'curso', 'estudiante', 'tipo_falta', 'falta_especifica',
              'descripcion', 'proceso_inicial', 'protocolo_aplicado', 'sancion_aplicada', 'docente', 'colegio_id']
    rows = (
        [f.get('id'), f.get('anio'), f.get('fecha'), f.get('curso'), f.get('estudiante'), f.get('tipo_falta'),
         f.get('falta_especifica'), f.get('descripcion'), f.get('proceso_inicial'),
         f.get('protocolo_aplicado', ''), f.get('sancion_aplicada', ''), f.get('docente'), f.get('colegio_id')]
        for f in faltas
    )
    return csv_response(f'faltas_{anio}.csv', header, rows)

@app.route('/api/reporte-estudiante')
@login_required
def api_reporte_estudiante():
    u = cu()
    estudiante = (request.args.get('estudiante') or '').strip()
    anio = request.args.get('anio', 'todos')
    if not estudiante:
        return jsonify({'error': 'Estudiante requerido'}), 400

    conn = get_db()
    p = ph()
    # En acudiente, forzamos el estudiante propio (aunque manden otro nombre)
    if u['rol'] == 'Acudiente':
        est = execute(conn, f"SELECT nombre FROM estudiantes WHERE id={p}", (u.get('estudiante_id'),), fetch='one')
        if not est:
            conn.close()
            return jsonify({'error': 'Sin estudiante asociado'}), 400
        estudiante = est['nombre']

    where = f"f.colegio_id={p} AND f.estudiante={p}"
    params = [u['colegio_id'] or 1, estudiante]
    if anio != 'todos':
        where += f" AND f.anio={p}"
        params.append(anio)

    # Respetar alcance por rol: misma lógica que fq (Docente solo su nombre; Director curso o su docente)
    if u['rol'] == 'Director':
        where += f" AND (f.curso={p} OR f.docente={p})"
        params += [u.get('curso', ''), u.get('nombre', '')]
    elif u['rol'] == 'Docente':
        where += f" AND f.docente={p}"
        params.append(u.get('nombre', ''))

    faltas = faltas_con_notas(conn, where, params)
    conn.close()

    header = ['id', 'anio', 'fecha', 'curso', 'estudiante', 'tipo_falta', 'falta_especifica',
              'descripcion', 'proceso_inicial', 'docente', 'notas']
    rows = (
        [f.get('id'), f.get('anio'), f.get('fecha'), f.get('curso'), f.get('estudiante'), f.get('tipo_falta'),
         f.get('falta_especifica'), f.get('descripcion'), f.get('proceso_inicial'), f.get('docente'),
         f.get('notas') or '']
        for f in faltas
    )
    safe_name = re.sub(r'[^a-zA-Z0-9_-]+', '_', estudiante).strip('_') or 'estudiante'
    return csv_response(f'historial_{safe_name}.csv', header, rows)

@app.route('/api/mejoramiento')
@login_required
def api_mejoramiento():
    """Panel de mejoramiento para Director, Coordinador, Orientador"""
    u=cu()
    if u['rol'] not in ('Director','Coordinador','Orientador','Superadmin'):
        return jsonify({'error':'Sin permisos'}),403
    anio=request.args.get('anio',str(datetime.now().year))
    conn=get_db(); q,p=fq(u,anio)
    faltas=execute(conn,q,p,fetch='all'); conn.close()
    # Por curso
    por_curso={}
    for f in faltas:
        c=f['curso']
        if c not in por_curso: por_curso[c]={'total':0,'t1':0,'t2':0,'t3':0,'faltas':[],'reincidentes_t1':[]}
        por_curso[c]['total']+=1
        por_curso[c]['faltas'].append(f)
        if f['tipo_falta']=='Tipo I': por_curso[c]['t1']+=1
        elif f['tipo_falta']=='Tipo II': por_curso[c]['t2']+=1
        elif f['tipo_falta']=='Tipo III': por_curso[c]['t3']+=1
    result={}
    for curso,data in por_curso.items():
        t1_est=Counter(f['estudiante'] for f in data['faltas'] if f['tipo_falta']=='Tipo I')
        data['reincidentes_t1']=[{'estudiante':e,'count':n} for e,n in t1_est.items() if n>=3]
        data['sugerencias']=generar_sugerencias(data['faltas'])
        del data['faltas']
        result[curso]=data
    return jsonify(result)

# ── PDFs ──────────────────────────────────────────────────────────────────────
@app.route('/api/pdf/curso')
@login_required
def api_pdf_curso():
    u=cu(); curso=request.args.get('curso',''); anio=request.args.get('anio',str(datetime.now().year))
    if not curso: return jsonify({'error':'Curso requerido'}),400
    conn=get_db(); p=ph()
    faltas=faltas_con_notas(conn,f"f.colegio_id={p} AND f.anio={p} AND f.curso={p}",[u['colegio_id'] or 1,anio,curso])
    conn.close()
    buf=generar_pdf_curso(col_nom(u['colegio_id']),curso,anio,faltas)
    return Response(buf.read(),mimetype='application/pdf',
        headers={'Content-Disposition':f'attachment;filename=faltas_{curso.replace(" ","_")}_{anio}.pdf'})

@app.route('/api/pdf/estudiante')
@login_required
def api_pdf_estudiante():
    u=cu(); est_id=request.args.get('est_id'); nombre_est=request.args.get('estudiante',''); anio=request.args.get('anio','todos')
    conn=get_db(); p=ph()
    est_info=None
    if est_id:
        est_info=execute(conn,f"SELECT * FROM estudiantes WHERE id={p}",(est_id,),fetch='one')
        if est_info: nombre_est=est_info['nombre']
    elif nombre_est:
        est_info=execute(conn,f"SELECT * FROM estudiantes WHERE nombre={p} AND colegio_id={p}",(nombre_est,u['colegio_id'] or 1),fetch='one')
    where=f"f.colegio_id={p} AND f.estudiante={p}"; params=[u['colegio_id'] or 1,nombre_est]
    if anio!='todos': where+=f" AND f.anio={p}"; params.append(anio)
    faltas=faltas_con_notas(conn,where,params); conn.close()
    buf=generar_pdf_estudiante(col_nom(u['colegio_id']),nombre_est,faltas,est_info)
    return Response(buf.read(),mimetype='application/pdf',
        headers={'Content-Disposition':f'attachment;filename=historial_{nombre_est.replace(" ","_")}.pdf'})

@app.route('/api/pdf/general')
@login_required
def api_pdf_general():
    u=cu(); anio=request.args.get('anio',str(datetime.now().year))
    conn=get_db()
    # Adaptar para incluir notas
    ph_=ph()
    where=f"f.colegio_id={ph_} AND f.anio={ph_}"
    params=[u['colegio_id'] or 1,anio]
    if u['rol']=='Director': where+=f" AND (f.curso={ph_} OR f.docente={ph_})"; params+=[u['curso'],u['nombre']]
    elif u['rol']=='Docente': where+=f" AND f.docente={ph_}"; params.append(u['nombre'])
    faltas=faltas_con_notas(conn,where,params); conn.close()
    buf=generar_pdf_curso(col_nom(u['colegio_id']),'Todos los cursos',anio,faltas)
    return Response(buf.read(),mimetype='application/pdf',
        headers={'Content-Disposition':f'attachment;filename=reporte_general_{anio}.pdf'})

def _puede_descargar_acta(u, f):
    if u['rol'] == 'Superadmin':
        return True
    if (u.get('colegio_id') or 1) != (f.get('colegio_id') or 1):
        return False
    if u['rol'] == 'Acudiente':
        return f.get('estudiante_id') == u.get('estudiante_id')
    if u['rol'] == 'Docente':
        return f.get('docente') == u['nombre']
    if u['rol'] == 'Director':
        return f.get('curso') == u.get('curso') or f.get('docente') == u.get('nombre')
    return True

@app.route('/api/pdf/acta/<int:fid>')
@login_required
def api_pdf_acta(fid):
    u = cu()
    conn = get_db()
    p = ph()
    f = execute(conn, f"SELECT * FROM faltas WHERE id={p}", (fid,), fetch='one')
    if not f:
        conn.close()
        return jsonify({'error': 'No encontrada'}), 404
    if not _puede_descargar_acta(u, f):
        conn.close()
        return jsonify({'error': 'Sin permisos'}), 403
    anots = execute(conn, f"SELECT * FROM anotaciones WHERE falta_id={p} ORDER BY id", (fid,), fetch='all')
    conn.close()
    buf = generar_pdf_acta_proceso(col_nom(u['colegio_id']), f, anots or [])
    safe = re.sub(r'[^a-zA-Z0-9_-]+', '_', str(f.get('estudiante', 'acta'))).strip('_') or 'acta'
    return Response(
        buf.read(),
        mimetype='application/pdf',
        headers={'Content-Disposition': f'attachment;filename=acta_falta_{fid}_{safe}.pdf'},
    )

@app.route('/api/cerrar-anio', methods=['POST'])
@roles('Superadmin','Coordinador')
def api_cerrar_anio():
    d=request.json or {}; u=cu(); conn=get_db(); p=ph()
    if d.get('limpiar_estudiantes'):
        execute(conn,f"DELETE FROM estudiantes WHERE colegio_id={p}",(u['colegio_id'],))
    commit(conn); conn.close(); return jsonify({'ok':True})

# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(__file__),'logs'), exist_ok=True)
    init_db()
    debug = (os.environ.get('FLASK_DEBUG', '0') == '1') and not IS_PROD
    app.run(debug=debug, host='0.0.0.0', port=PORT, use_reloader=False)
