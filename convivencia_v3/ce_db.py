"""
Capa de acceso a datos: PostgreSQL (DATABASE_URL) o SQLite local.
"""
import os
import secrets
from datetime import datetime

from ce_utils import hpwd

DATABASE_URL = os.environ.get("DATABASE_URL", "")
USE_PG = DATABASE_URL.startswith("postgres")

if USE_PG:
    import psycopg2
    import psycopg2.extras
else:
    import sqlite3

DATABASE_FILE = os.path.join(os.path.dirname(__file__), "convivencia.db")


def get_db():
    if USE_PG:
        url = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        conn = psycopg2.connect(url, cursor_factory=psycopg2.extras.RealDictCursor)
        conn.autocommit = False
        return conn
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def ph():
    return "%s" if USE_PG else "?"


def adapt_query(q):
    if USE_PG:
        q = q.replace("?", "%s")
        q = q.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")
        q = q.replace("last_insert_rowid()", "lastval()")
    return q


def execute(conn, q, params=(), fetch=None):
    q = adapt_query(q)
    if USE_PG:
        cur = conn.cursor()
        cur.execute(q, params)
        if fetch == "all":
            return [dict(r) for r in cur.fetchall()]
        if fetch == "one":
            r = cur.fetchone()
            return dict(r) if r else None
        if fetch == "lastid":
            cur.execute("SELECT lastval()")
            return cur.fetchone()[0]
        return cur
    cur = conn.execute(q, params)
    if fetch == "all":
        rows = cur.fetchall()
        return [dict(r) for r in rows]
    if fetch == "one":
        r = cur.fetchone()
        return dict(r) if r else None
    if fetch == "lastid":
        return cur.lastrowid
    return cur


def commit(conn):
    conn.commit()


def _sqlite_colnames(conn, table):
    rows = execute(conn, f"PRAGMA table_info({table})", fetch="all") or []
    return {r.get("name") for r in rows}


def _sqlite_add_col(conn, table, name, decl):
    if name in _sqlite_colnames(conn, table):
        return
    try:
        execute(conn, f"ALTER TABLE {table} ADD COLUMN {name} {decl}")
    except Exception:
        pass


def _migrate_schema(conn):
    """Columnas/tablas nuevas en bases ya existentes."""
    if USE_PG:
        for stmt in (
            "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS asignatura TEXT DEFAULT ''",
            "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS tipo_doc TEXT DEFAULT ''",
            "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS documento_personal TEXT DEFAULT ''",
            "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS apellido1 TEXT DEFAULT ''",
            "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS apellido2 TEXT DEFAULT ''",
            "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS nombre1 TEXT DEFAULT ''",
            "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS nombre2 TEXT DEFAULT ''",
            "ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS telefono TEXT DEFAULT ''",
            "ALTER TABLE estudiantes ADD COLUMN IF NOT EXISTS tipo_doc_est TEXT DEFAULT ''",
            "ALTER TABLE estudiantes ADD COLUMN IF NOT EXISTS apellido1_est TEXT DEFAULT ''",
            "ALTER TABLE estudiantes ADD COLUMN IF NOT EXISTS apellido2_est TEXT DEFAULT ''",
            "ALTER TABLE estudiantes ADD COLUMN IF NOT EXISTS nombre1_est TEXT DEFAULT ''",
            "ALTER TABLE estudiantes ADD COLUMN IF NOT EXISTS nombre2_est TEXT DEFAULT ''",
            "ALTER TABLE estudiantes ADD COLUMN IF NOT EXISTS barreras TEXT DEFAULT ''",
            "ALTER TABLE estudiantes ADD COLUMN IF NOT EXISTS tipo_doc_acu TEXT DEFAULT ''",
            "ALTER TABLE estudiantes ADD COLUMN IF NOT EXISTS apellido1_acu TEXT DEFAULT ''",
            "ALTER TABLE estudiantes ADD COLUMN IF NOT EXISTS apellido2_acu TEXT DEFAULT ''",
            "ALTER TABLE estudiantes ADD COLUMN IF NOT EXISTS nombre1_acu TEXT DEFAULT ''",
            "ALTER TABLE estudiantes ADD COLUMN IF NOT EXISTS nombre2_acu TEXT DEFAULT ''",
            "ALTER TABLE estudiantes ADD COLUMN IF NOT EXISTS parentesco_acu TEXT DEFAULT ''",
            "ALTER TABLE senales_atencion ADD COLUMN IF NOT EXISTS tipo_conducta TEXT DEFAULT ''",
            "ALTER TABLE senales_atencion ADD COLUMN IF NOT EXISTS subtipo_clave TEXT DEFAULT ''",
            "ALTER TABLE senales_atencion ADD COLUMN IF NOT EXISTS accion_derivada TEXT DEFAULT ''",
            "ALTER TABLE senales_atencion ADD COLUMN IF NOT EXISTS urgencia TEXT DEFAULT ''",
            "ALTER TABLE senales_atencion ADD COLUMN IF NOT EXISTS evidencia_path TEXT DEFAULT ''",
            "ALTER TABLE faltas ADD COLUMN IF NOT EXISTS gestion_coordinador TEXT DEFAULT NULL",
            "ALTER TABLE faltas ADD COLUMN IF NOT EXISTS lugar TEXT DEFAULT ''",
            "ALTER TABLE faltas ADD COLUMN IF NOT EXISTS afectados_json TEXT DEFAULT ''",
            "ALTER TABLE estudiantes ADD COLUMN IF NOT EXISTS reporte_token TEXT DEFAULT ''",
            "ALTER TABLE estudiantes ADD COLUMN IF NOT EXISTS reporte_pin_hash TEXT DEFAULT ''",
            """CREATE TABLE IF NOT EXISTS reportes_convivencia (
                id SERIAL PRIMARY KEY,
                colegio_id INTEGER NOT NULL REFERENCES colegios(id),
                estudiante_id INTEGER REFERENCES estudiantes(id) ON DELETE SET NULL,
                estudiante_nombre TEXT NOT NULL,
                curso TEXT DEFAULT '',
                categoria_visual TEXT NOT NULL,
                a_quien TEXT NOT NULL,
                descripcion TEXT NOT NULL,
                fue_hoy INTEGER DEFAULT 1,
                fecha_incidente TEXT DEFAULT '',
                lugar_clave TEXT NOT NULL,
                urgencia TEXT NOT NULL,
                evidencia_path TEXT DEFAULT '',
                estado TEXT DEFAULT 'pendiente_validacion',
                nota_comite TEXT DEFAULT '',
                creado_en TEXT NOT NULL,
                actualizado_en TEXT DEFAULT ''
            )""",
            """CREATE TABLE IF NOT EXISTS reportes_convivencia_bitacora (
                id SERIAL PRIMARY KEY,
                colegio_id INTEGER NOT NULL REFERENCES colegios(id),
                reporte_id INTEGER NOT NULL REFERENCES reportes_convivencia(id) ON DELETE CASCADE,
                usuario_id INTEGER REFERENCES usuarios(id),
                usuario_nombre TEXT DEFAULT '',
                rol TEXT DEFAULT '',
                estado_anterior TEXT DEFAULT '',
                estado_nuevo TEXT NOT NULL,
                nota TEXT NOT NULL,
                creado_en TEXT NOT NULL
            )""",
            """CREATE TABLE IF NOT EXISTS promocion_actividades (
                id SERIAL PRIMARY KEY,
                colegio_id INTEGER NOT NULL REFERENCES colegios(id),
                titulo TEXT NOT NULL,
                tema TEXT NOT NULL,
                fecha TEXT NOT NULL,
                lugar TEXT DEFAULT '',
                recursos TEXT DEFAULT '',
                descripcion TEXT DEFAULT '',
                publico_tipo TEXT NOT NULL,
                publico_curso TEXT DEFAULT '',
                publico_json TEXT DEFAULT '',
                evidencia_path TEXT DEFAULT '',
                creado_por_id INTEGER,
                creado_por_nombre TEXT DEFAULT '',
                creado_por_rol TEXT DEFAULT '',
                creado_en TEXT NOT NULL
            )""",
            """CREATE TABLE IF NOT EXISTS promocion_evidencias (
                id SERIAL PRIMARY KEY,
                actividad_id INTEGER NOT NULL REFERENCES promocion_actividades(id) ON DELETE CASCADE,
                colegio_id INTEGER NOT NULL REFERENCES colegios(id),
                stored_path TEXT NOT NULL,
                nombre_original TEXT DEFAULT '',
                mime TEXT DEFAULT '',
                subido_por_id INTEGER,
                subido_por_nombre TEXT DEFAULT '',
                creado_en TEXT NOT NULL
            )""",
            "DROP TABLE IF EXISTS acta_descargos CASCADE",
            """CREATE TABLE IF NOT EXISTS citas_acudiente (
                id SERIAL PRIMARY KEY,
                falta_id INTEGER NOT NULL REFERENCES faltas(id) ON DELETE CASCADE,
                colegio_id INTEGER NOT NULL REFERENCES colegios(id),
                origen TEXT NOT NULL,
                estado TEXT NOT NULL,
                rol_destino TEXT DEFAULT '',
                fecha_hora TEXT DEFAULT '',
                creado_por_id INTEGER,
                creado_por_nombre TEXT DEFAULT '',
                creado_por_rol TEXT DEFAULT '',
                agenda_por_id INTEGER,
                agenda_por_nombre TEXT DEFAULT '',
                creado_en TEXT NOT NULL,
                actualizado_en TEXT NOT NULL
            )""",
            """CREATE TABLE IF NOT EXISTS falta_adjuntos (
                id SERIAL PRIMARY KEY,
                falta_id INTEGER NOT NULL REFERENCES faltas(id) ON DELETE CASCADE,
                colegio_id INTEGER NOT NULL REFERENCES colegios(id),
                categoria TEXT NOT NULL,
                stored_path TEXT NOT NULL,
                nombre_original TEXT DEFAULT '',
                mime TEXT DEFAULT '',
                subido_por_id INTEGER REFERENCES usuarios(id),
                subido_por_nombre TEXT DEFAULT '',
                creado_en TEXT NOT NULL
            )""",
        ):
            try:
                execute(conn, stmt)
            except Exception:
                pass
        return
    for t, name, decl in (
        ("usuarios", "asignatura", "TEXT DEFAULT ''"),
        ("usuarios", "tipo_doc", "TEXT DEFAULT ''"),
        ("usuarios", "documento_personal", "TEXT DEFAULT ''"),
        ("usuarios", "apellido1", "TEXT DEFAULT ''"),
        ("usuarios", "apellido2", "TEXT DEFAULT ''"),
        ("usuarios", "nombre1", "TEXT DEFAULT ''"),
        ("usuarios", "nombre2", "TEXT DEFAULT ''"),
        ("usuarios", "telefono", "TEXT DEFAULT ''"),
        ("estudiantes", "tipo_doc_est", "TEXT DEFAULT ''"),
        ("estudiantes", "apellido1_est", "TEXT DEFAULT ''"),
        ("estudiantes", "apellido2_est", "TEXT DEFAULT ''"),
        ("estudiantes", "nombre1_est", "TEXT DEFAULT ''"),
        ("estudiantes", "nombre2_est", "TEXT DEFAULT ''"),
        ("estudiantes", "barreras", "TEXT DEFAULT ''"),
        ("estudiantes", "tipo_doc_acu", "TEXT DEFAULT ''"),
        ("estudiantes", "apellido1_acu", "TEXT DEFAULT ''"),
        ("estudiantes", "apellido2_acu", "TEXT DEFAULT ''"),
        ("estudiantes", "nombre1_acu", "TEXT DEFAULT ''"),
        ("estudiantes", "nombre2_acu", "TEXT DEFAULT ''"),
        ("estudiantes", "parentesco_acu", "TEXT DEFAULT ''"),
        ("senales_atencion", "tipo_conducta", "TEXT DEFAULT ''"),
        ("senales_atencion", "subtipo_clave", "TEXT DEFAULT ''"),
        ("senales_atencion", "accion_derivada", "TEXT DEFAULT ''"),
        ("senales_atencion", "urgencia", "TEXT DEFAULT ''"),
        ("senales_atencion", "evidencia_path", "TEXT DEFAULT ''"),
        ("faltas", "gestion_coordinador", "TEXT DEFAULT NULL"),
        ("faltas", "lugar", "TEXT DEFAULT ''"),
        ("faltas", "afectados_json", "TEXT DEFAULT ''"),
        ("estudiantes", "reporte_token", "TEXT DEFAULT ''"),
        ("estudiantes", "reporte_pin_hash", "TEXT DEFAULT ''"),
    ):
        _sqlite_add_col(conn, t, name, decl)
    try:
        execute(
            conn,
            """CREATE TABLE IF NOT EXISTS citas_acudiente (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                falta_id INTEGER NOT NULL REFERENCES faltas(id),
                colegio_id INTEGER NOT NULL REFERENCES colegios(id),
                origen TEXT NOT NULL,
                estado TEXT NOT NULL,
                rol_destino TEXT DEFAULT '',
                fecha_hora TEXT DEFAULT '',
                creado_por_id INTEGER,
                creado_por_nombre TEXT DEFAULT '',
                creado_por_rol TEXT DEFAULT '',
                agenda_por_id INTEGER,
                agenda_por_nombre TEXT DEFAULT '',
                creado_en TEXT NOT NULL,
                actualizado_en TEXT NOT NULL
            )""",
        )
    except Exception:
        pass
    try:
        execute(conn, "DROP TABLE IF EXISTS acta_descargos")
    except Exception:
        pass
    try:
        execute(
            conn,
            """CREATE TABLE IF NOT EXISTS falta_adjuntos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                falta_id INTEGER NOT NULL REFERENCES faltas(id) ON DELETE CASCADE,
                colegio_id INTEGER NOT NULL REFERENCES colegios(id),
                categoria TEXT NOT NULL,
                stored_path TEXT NOT NULL,
                nombre_original TEXT DEFAULT '',
                mime TEXT DEFAULT '',
                subido_por_id INTEGER REFERENCES usuarios(id),
                subido_por_nombre TEXT DEFAULT '',
                creado_en TEXT NOT NULL
            )""",
        )
    except Exception:
        pass
    try:
        execute(
            conn,
            """CREATE TABLE IF NOT EXISTS reportes_convivencia (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                colegio_id INTEGER NOT NULL REFERENCES colegios(id),
                estudiante_id INTEGER REFERENCES estudiantes(id),
                estudiante_nombre TEXT NOT NULL,
                curso TEXT DEFAULT '',
                categoria_visual TEXT NOT NULL,
                a_quien TEXT NOT NULL,
                descripcion TEXT NOT NULL,
                fue_hoy INTEGER DEFAULT 1,
                fecha_incidente TEXT DEFAULT '',
                lugar_clave TEXT NOT NULL,
                urgencia TEXT NOT NULL,
                evidencia_path TEXT DEFAULT '',
                estado TEXT DEFAULT 'pendiente_validacion',
                nota_comite TEXT DEFAULT '',
                creado_en TEXT NOT NULL,
                actualizado_en TEXT DEFAULT ''
            )""",
        )
    except Exception:
        pass
    try:
        execute(
            conn,
            """CREATE TABLE IF NOT EXISTS reportes_convivencia_bitacora (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                colegio_id INTEGER NOT NULL REFERENCES colegios(id),
                reporte_id INTEGER NOT NULL REFERENCES reportes_convivencia(id) ON DELETE CASCADE,
                usuario_id INTEGER,
                usuario_nombre TEXT DEFAULT '',
                rol TEXT DEFAULT '',
                estado_anterior TEXT DEFAULT '',
                estado_nuevo TEXT NOT NULL,
                nota TEXT NOT NULL,
                creado_en TEXT NOT NULL
            )""",
        )
    except Exception:
        pass
    try:
        execute(
            conn,
            """CREATE TABLE IF NOT EXISTS promocion_actividades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                colegio_id INTEGER NOT NULL REFERENCES colegios(id),
                titulo TEXT NOT NULL,
                tema TEXT NOT NULL,
                fecha TEXT NOT NULL,
                lugar TEXT DEFAULT '',
                recursos TEXT DEFAULT '',
                descripcion TEXT DEFAULT '',
                publico_tipo TEXT NOT NULL,
                publico_curso TEXT DEFAULT '',
                publico_json TEXT DEFAULT '',
                evidencia_path TEXT DEFAULT '',
                creado_por_id INTEGER,
                creado_por_nombre TEXT DEFAULT '',
                creado_por_rol TEXT DEFAULT '',
                creado_en TEXT NOT NULL
            )""",
        )
    except Exception:
        pass
    try:
        execute(
            conn,
            """CREATE TABLE IF NOT EXISTS promocion_evidencias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                actividad_id INTEGER NOT NULL REFERENCES promocion_actividades(id) ON DELETE CASCADE,
                colegio_id INTEGER NOT NULL REFERENCES colegios(id),
                stored_path TEXT NOT NULL,
                nombre_original TEXT DEFAULT '',
                mime TEXT DEFAULT '',
                subido_por_id INTEGER,
                subido_por_nombre TEXT DEFAULT '',
                creado_en TEXT NOT NULL
            )""",
        )
    except Exception:
        pass


def _backfill_reporte_tokens(conn):
    """Asigna token de enlace/QR a estudiantes que aún no lo tengan."""
    rows = execute(conn, "SELECT id, reporte_token FROM estudiantes", fetch="all") or []
    p = ph()
    for r in rows:
        tok = (r.get("reporte_token") or "").strip()
        if tok:
            continue
        nt = secrets.token_urlsafe(24)
        execute(conn, f"UPDATE estudiantes SET reporte_token={p} WHERE id={p}", (nt, r["id"]))


DDL_PG = """
CREATE TABLE IF NOT EXISTS colegios (
    id SERIAL PRIMARY KEY, nombre TEXT NOT NULL, nit TEXT DEFAULT '',
    municipio TEXT DEFAULT '', rector TEXT DEFAULT '',
    direccion TEXT DEFAULT '', telefono TEXT DEFAULT '', email TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY, usuario TEXT UNIQUE NOT NULL,
    contrasena TEXT NOT NULL, rol TEXT NOT NULL, nombre TEXT NOT NULL,
    curso TEXT DEFAULT '', colegio_id INTEGER REFERENCES colegios(id),
    estudiante_id INTEGER DEFAULT NULL,
    asignatura TEXT DEFAULT '', tipo_doc TEXT DEFAULT '', documento_personal TEXT DEFAULT '',
    apellido1 TEXT DEFAULT '', apellido2 TEXT DEFAULT '', nombre1 TEXT DEFAULT '', nombre2 TEXT DEFAULT '',
    telefono TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS estudiantes (
    id SERIAL PRIMARY KEY, documento_identidad TEXT DEFAULT '',
    nombre TEXT NOT NULL, curso TEXT NOT NULL, discapacidad TEXT DEFAULT '',
    acudiente TEXT DEFAULT '', cedula_acudiente TEXT DEFAULT '',
    telefono TEXT DEFAULT '', direccion TEXT DEFAULT '',
    colegio_id INTEGER REFERENCES colegios(id),
    tipo_doc_est TEXT DEFAULT '', apellido1_est TEXT DEFAULT '', apellido2_est TEXT DEFAULT '',
    nombre1_est TEXT DEFAULT '', nombre2_est TEXT DEFAULT '', barreras TEXT DEFAULT '',
    tipo_doc_acu TEXT DEFAULT '', apellido1_acu TEXT DEFAULT '', apellido2_acu TEXT DEFAULT '',
    nombre1_acu TEXT DEFAULT '', nombre2_acu TEXT DEFAULT '', parentesco_acu TEXT DEFAULT '',
    reporte_token TEXT DEFAULT '', reporte_pin_hash TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS catalogo_faltas (
    id SERIAL PRIMARY KEY, tipo TEXT NOT NULL, descripcion TEXT NOT NULL,
    protocolo TEXT DEFAULT '', sancion TEXT DEFAULT '',
    colegio_id INTEGER REFERENCES colegios(id)
);
CREATE TABLE IF NOT EXISTS faltas (
    id SERIAL PRIMARY KEY, anio INTEGER NOT NULL, fecha TEXT NOT NULL,
    curso TEXT NOT NULL, estudiante TEXT NOT NULL,
    estudiante_id INTEGER DEFAULT NULL, tipo_falta TEXT NOT NULL,
    falta_especifica TEXT NOT NULL, descripcion TEXT NOT NULL,
    proceso_inicial TEXT NOT NULL, protocolo_aplicado TEXT DEFAULT '',
    sancion_aplicada TEXT DEFAULT '', docente TEXT NOT NULL,
    colegio_id INTEGER REFERENCES colegios(id),
    gestion_coordinador TEXT DEFAULT NULL,
    lugar TEXT DEFAULT '',
    afectados_json TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS anotaciones (
    id SERIAL PRIMARY KEY, falta_id INTEGER REFERENCES faltas(id),
    rol TEXT NOT NULL, autor TEXT NOT NULL,
    fecha TEXT NOT NULL, texto TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS citas_acudiente (
    id SERIAL PRIMARY KEY,
    falta_id INTEGER NOT NULL REFERENCES faltas(id) ON DELETE CASCADE,
    colegio_id INTEGER NOT NULL REFERENCES colegios(id),
    origen TEXT NOT NULL,
    estado TEXT NOT NULL,
    rol_destino TEXT DEFAULT '',
    fecha_hora TEXT DEFAULT '',
    creado_por_id INTEGER,
    creado_por_nombre TEXT DEFAULT '',
    creado_por_rol TEXT DEFAULT '',
    agenda_por_id INTEGER,
    agenda_por_nombre TEXT DEFAULT '',
    creado_en TEXT NOT NULL,
    actualizado_en TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS senales_atencion (
    id SERIAL PRIMARY KEY,
    colegio_id INTEGER NOT NULL REFERENCES colegios(id),
    estudiante_id INTEGER REFERENCES estudiantes(id),
    estudiante_nombre TEXT NOT NULL,
    curso TEXT DEFAULT '',
    categoria TEXT NOT NULL,
    observacion TEXT NOT NULL,
    registrado_por_id INTEGER REFERENCES usuarios(id),
    registrado_por_nombre TEXT DEFAULT '',
    registrado_rol TEXT DEFAULT '',
    fecha_registro TEXT NOT NULL,
    estado TEXT DEFAULT 'abierta',
    nota_seguimiento TEXT DEFAULT '',
    tipo_conducta TEXT DEFAULT '', subtipo_clave TEXT DEFAULT '', accion_derivada TEXT DEFAULT '',
    urgencia TEXT DEFAULT '', evidencia_path TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS reportes_convivencia (
    id SERIAL PRIMARY KEY,
    colegio_id INTEGER NOT NULL REFERENCES colegios(id),
    estudiante_id INTEGER REFERENCES estudiantes(id) ON DELETE SET NULL,
    estudiante_nombre TEXT NOT NULL,
    curso TEXT DEFAULT '',
    categoria_visual TEXT NOT NULL,
    a_quien TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    fue_hoy INTEGER DEFAULT 1,
    fecha_incidente TEXT DEFAULT '',
    lugar_clave TEXT NOT NULL,
    urgencia TEXT NOT NULL,
    evidencia_path TEXT DEFAULT '',
    estado TEXT DEFAULT 'pendiente_validacion',
    nota_comite TEXT DEFAULT '',
    creado_en TEXT NOT NULL,
    actualizado_en TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS reportes_convivencia_bitacora (
    id SERIAL PRIMARY KEY,
    colegio_id INTEGER NOT NULL REFERENCES colegios(id),
    reporte_id INTEGER NOT NULL REFERENCES reportes_convivencia(id) ON DELETE CASCADE,
    usuario_id INTEGER REFERENCES usuarios(id),
    usuario_nombre TEXT DEFAULT '',
    rol TEXT DEFAULT '',
    estado_anterior TEXT DEFAULT '',
    estado_nuevo TEXT NOT NULL,
    nota TEXT NOT NULL,
    creado_en TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS asistencia_toma (
    id SERIAL PRIMARY KEY,
    colegio_id INTEGER NOT NULL REFERENCES colegios(id),
    fecha TEXT NOT NULL,
    curso TEXT NOT NULL,
    asignatura TEXT DEFAULT '',
    docente_id INTEGER REFERENCES usuarios(id),
    docente_nombre TEXT DEFAULT '',
    creado_en TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS asistencia_detalle (
    id SERIAL PRIMARY KEY,
    toma_id INTEGER NOT NULL REFERENCES asistencia_toma(id) ON DELETE CASCADE,
    estudiante_id INTEGER REFERENCES estudiantes(id),
    estudiante_nombre TEXT NOT NULL,
    ausente INTEGER DEFAULT 1,
    justificada INTEGER
);
CREATE TABLE IF NOT EXISTS promocion_actividades (
    id SERIAL PRIMARY KEY,
    colegio_id INTEGER NOT NULL REFERENCES colegios(id),
    titulo TEXT NOT NULL,
    tema TEXT NOT NULL,
    fecha TEXT NOT NULL,
    lugar TEXT DEFAULT '',
    recursos TEXT DEFAULT '',
    descripcion TEXT DEFAULT '',
    publico_tipo TEXT NOT NULL,
    publico_curso TEXT DEFAULT '',
    publico_json TEXT DEFAULT '',
    evidencia_path TEXT DEFAULT '',
    creado_por_id INTEGER,
    creado_por_nombre TEXT DEFAULT '',
    creado_por_rol TEXT DEFAULT '',
    creado_en TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS promocion_evidencias (
    id SERIAL PRIMARY KEY,
    actividad_id INTEGER NOT NULL REFERENCES promocion_actividades(id) ON DELETE CASCADE,
    colegio_id INTEGER NOT NULL REFERENCES colegios(id),
    stored_path TEXT NOT NULL,
    nombre_original TEXT DEFAULT '',
    mime TEXT DEFAULT '',
    subido_por_id INTEGER,
    subido_por_nombre TEXT DEFAULT '',
    creado_en TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS falta_adjuntos (
    id SERIAL PRIMARY KEY,
    falta_id INTEGER NOT NULL REFERENCES faltas(id) ON DELETE CASCADE,
    colegio_id INTEGER NOT NULL REFERENCES colegios(id),
    categoria TEXT NOT NULL,
    stored_path TEXT NOT NULL,
    nombre_original TEXT DEFAULT '',
    mime TEXT DEFAULT '',
    subido_por_id INTEGER REFERENCES usuarios(id),
    subido_por_nombre TEXT DEFAULT '',
    creado_en TEXT NOT NULL
);
"""

DDL_SQLITE = """
CREATE TABLE IF NOT EXISTS colegios (
    id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL, nit TEXT DEFAULT '',
    municipio TEXT DEFAULT '', rector TEXT DEFAULT '',
    direccion TEXT DEFAULT '', telefono TEXT DEFAULT '', email TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT, usuario TEXT UNIQUE NOT NULL,
    contrasena TEXT NOT NULL, rol TEXT NOT NULL, nombre TEXT NOT NULL,
    curso TEXT DEFAULT '', colegio_id INTEGER REFERENCES colegios(id),
    estudiante_id INTEGER DEFAULT NULL,
    asignatura TEXT DEFAULT '', tipo_doc TEXT DEFAULT '', documento_personal TEXT DEFAULT '',
    apellido1 TEXT DEFAULT '', apellido2 TEXT DEFAULT '', nombre1 TEXT DEFAULT '', nombre2 TEXT DEFAULT '',
    telefono TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS estudiantes (
    id INTEGER PRIMARY KEY AUTOINCREMENT, documento_identidad TEXT DEFAULT '',
    nombre TEXT NOT NULL, curso TEXT NOT NULL, discapacidad TEXT DEFAULT '',
    acudiente TEXT DEFAULT '', cedula_acudiente TEXT DEFAULT '',
    telefono TEXT DEFAULT '', direccion TEXT DEFAULT '',
    colegio_id INTEGER REFERENCES colegios(id),
    tipo_doc_est TEXT DEFAULT '', apellido1_est TEXT DEFAULT '', apellido2_est TEXT DEFAULT '',
    nombre1_est TEXT DEFAULT '', nombre2_est TEXT DEFAULT '', barreras TEXT DEFAULT '',
    tipo_doc_acu TEXT DEFAULT '', apellido1_acu TEXT DEFAULT '', apellido2_acu TEXT DEFAULT '',
    nombre1_acu TEXT DEFAULT '', nombre2_acu TEXT DEFAULT '', parentesco_acu TEXT DEFAULT '',
    reporte_token TEXT DEFAULT '', reporte_pin_hash TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS catalogo_faltas (
    id INTEGER PRIMARY KEY AUTOINCREMENT, tipo TEXT NOT NULL, descripcion TEXT NOT NULL,
    protocolo TEXT DEFAULT '', sancion TEXT DEFAULT '',
    colegio_id INTEGER REFERENCES colegios(id)
);
CREATE TABLE IF NOT EXISTS faltas (
    id INTEGER PRIMARY KEY AUTOINCREMENT, anio INTEGER NOT NULL, fecha TEXT NOT NULL,
    curso TEXT NOT NULL, estudiante TEXT NOT NULL,
    estudiante_id INTEGER DEFAULT NULL, tipo_falta TEXT NOT NULL,
    falta_especifica TEXT NOT NULL, descripcion TEXT NOT NULL,
    proceso_inicial TEXT NOT NULL, protocolo_aplicado TEXT DEFAULT '',
    sancion_aplicada TEXT DEFAULT '', docente TEXT NOT NULL,
    colegio_id INTEGER REFERENCES colegios(id),
    gestion_coordinador TEXT DEFAULT NULL,
    lugar TEXT DEFAULT '',
    afectados_json TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS anotaciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT, falta_id INTEGER REFERENCES faltas(id),
    rol TEXT NOT NULL, autor TEXT NOT NULL,
    fecha TEXT NOT NULL, texto TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS citas_acudiente (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    falta_id INTEGER NOT NULL REFERENCES faltas(id),
    colegio_id INTEGER NOT NULL REFERENCES colegios(id),
    origen TEXT NOT NULL,
    estado TEXT NOT NULL,
    rol_destino TEXT DEFAULT '',
    fecha_hora TEXT DEFAULT '',
    creado_por_id INTEGER,
    creado_por_nombre TEXT DEFAULT '',
    creado_por_rol TEXT DEFAULT '',
    agenda_por_id INTEGER,
    agenda_por_nombre TEXT DEFAULT '',
    creado_en TEXT NOT NULL,
    actualizado_en TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS senales_atencion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    colegio_id INTEGER NOT NULL REFERENCES colegios(id),
    estudiante_id INTEGER REFERENCES estudiantes(id),
    estudiante_nombre TEXT NOT NULL,
    curso TEXT DEFAULT '',
    categoria TEXT NOT NULL,
    observacion TEXT NOT NULL,
    registrado_por_id INTEGER REFERENCES usuarios(id),
    registrado_por_nombre TEXT DEFAULT '',
    registrado_rol TEXT DEFAULT '',
    fecha_registro TEXT NOT NULL,
    estado TEXT DEFAULT 'abierta',
    nota_seguimiento TEXT DEFAULT '',
    tipo_conducta TEXT DEFAULT '', subtipo_clave TEXT DEFAULT '', accion_derivada TEXT DEFAULT '',
    urgencia TEXT DEFAULT '', evidencia_path TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS reportes_convivencia (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    colegio_id INTEGER NOT NULL REFERENCES colegios(id),
    estudiante_id INTEGER REFERENCES estudiantes(id),
    estudiante_nombre TEXT NOT NULL,
    curso TEXT DEFAULT '',
    categoria_visual TEXT NOT NULL,
    a_quien TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    fue_hoy INTEGER DEFAULT 1,
    fecha_incidente TEXT DEFAULT '',
    lugar_clave TEXT NOT NULL,
    urgencia TEXT NOT NULL,
    evidencia_path TEXT DEFAULT '',
    estado TEXT DEFAULT 'pendiente_validacion',
    nota_comite TEXT DEFAULT '',
    creado_en TEXT NOT NULL,
    actualizado_en TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS reportes_convivencia_bitacora (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    colegio_id INTEGER NOT NULL REFERENCES colegios(id),
    reporte_id INTEGER NOT NULL REFERENCES reportes_convivencia(id) ON DELETE CASCADE,
    usuario_id INTEGER,
    usuario_nombre TEXT DEFAULT '',
    rol TEXT DEFAULT '',
    estado_anterior TEXT DEFAULT '',
    estado_nuevo TEXT NOT NULL,
    nota TEXT NOT NULL,
    creado_en TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS asistencia_toma (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    colegio_id INTEGER NOT NULL REFERENCES colegios(id),
    fecha TEXT NOT NULL,
    curso TEXT NOT NULL,
    asignatura TEXT DEFAULT '',
    docente_id INTEGER REFERENCES usuarios(id),
    docente_nombre TEXT DEFAULT '',
    creado_en TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS asistencia_detalle (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    toma_id INTEGER NOT NULL REFERENCES asistencia_toma(id) ON DELETE CASCADE,
    estudiante_id INTEGER REFERENCES estudiantes(id),
    estudiante_nombre TEXT NOT NULL,
    ausente INTEGER DEFAULT 1,
    justificada INTEGER
);
CREATE TABLE IF NOT EXISTS promocion_actividades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    colegio_id INTEGER NOT NULL REFERENCES colegios(id),
    titulo TEXT NOT NULL,
    tema TEXT NOT NULL,
    fecha TEXT NOT NULL,
    lugar TEXT DEFAULT '',
    recursos TEXT DEFAULT '',
    descripcion TEXT DEFAULT '',
    publico_tipo TEXT NOT NULL,
    publico_curso TEXT DEFAULT '',
    publico_json TEXT DEFAULT '',
    evidencia_path TEXT DEFAULT '',
    creado_por_id INTEGER,
    creado_por_nombre TEXT DEFAULT '',
    creado_por_rol TEXT DEFAULT '',
    creado_en TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS promocion_evidencias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    actividad_id INTEGER NOT NULL REFERENCES promocion_actividades(id) ON DELETE CASCADE,
    colegio_id INTEGER NOT NULL REFERENCES colegios(id),
    stored_path TEXT NOT NULL,
    nombre_original TEXT DEFAULT '',
    mime TEXT DEFAULT '',
    subido_por_id INTEGER,
    subido_por_nombre TEXT DEFAULT '',
    creado_en TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS falta_adjuntos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    falta_id INTEGER NOT NULL REFERENCES faltas(id) ON DELETE CASCADE,
    colegio_id INTEGER NOT NULL REFERENCES colegios(id),
    categoria TEXT NOT NULL,
    stored_path TEXT NOT NULL,
    nombre_original TEXT DEFAULT '',
    mime TEXT DEFAULT '',
    subido_por_id INTEGER REFERENCES usuarios(id),
    subido_por_nombre TEXT DEFAULT '',
    creado_en TEXT NOT NULL
);
"""


def init_db():
    conn = get_db()
    ddl = DDL_PG if USE_PG else DDL_SQLITE
    if USE_PG:
        cur = conn.cursor()
        for stmt in [s.strip() for s in ddl.split(";") if s.strip()]:
            cur.execute(stmt)
    else:
        conn.executescript(ddl)

    _migrate_schema(conn)
    _backfill_reporte_tokens(conn)

    # Índices para escalar (multi-colegio + filtros frecuentes).
    # Se crean de forma idempotente; si fallan (p.ej. por esquema viejo), se ignoran.
    for stmt in (
        # faltas
        "CREATE INDEX IF NOT EXISTS idx_faltas_colegio_anio_fecha ON faltas(colegio_id, anio, fecha)",
        "CREATE INDEX IF NOT EXISTS idx_faltas_colegio_curso ON faltas(colegio_id, curso)",
        "CREATE INDEX IF NOT EXISTS idx_faltas_colegio_docente ON faltas(colegio_id, docente)",
        "CREATE INDEX IF NOT EXISTS idx_faltas_estudiante_id ON faltas(estudiante_id)",
        # estudiantes
        "CREATE INDEX IF NOT EXISTS idx_estudiantes_colegio_curso ON estudiantes(colegio_id, curso)",
        "CREATE INDEX IF NOT EXISTS idx_estudiantes_colegio_nombre ON estudiantes(colegio_id, nombre)",
        # catálogo
        "CREATE INDEX IF NOT EXISTS idx_catalogo_colegio_tipo ON catalogo_faltas(colegio_id, tipo)",
        # señales
        "CREATE INDEX IF NOT EXISTS idx_senales_colegio_fecha ON senales_atencion(colegio_id, fecha_registro)",
        "CREATE INDEX IF NOT EXISTS idx_senales_colegio_est ON senales_atencion(colegio_id, estudiante_id)",
        # asistencia
        "CREATE INDEX IF NOT EXISTS idx_asist_toma_colegio_fecha ON asistencia_toma(colegio_id, fecha)",
        "CREATE INDEX IF NOT EXISTS idx_asist_toma_colegio_curso ON asistencia_toma(colegio_id, curso)",
        "CREATE INDEX IF NOT EXISTS idx_asist_det_toma ON asistencia_detalle(toma_id)",
        # citas
        "CREATE INDEX IF NOT EXISTS idx_citas_colegio_estado ON citas_acudiente(colegio_id, estado)",
        "CREATE INDEX IF NOT EXISTS idx_citas_falta ON citas_acudiente(falta_id)",
        "CREATE INDEX IF NOT EXISTS idx_falta_adjuntos_falta ON falta_adjuntos(falta_id)",
        "CREATE INDEX IF NOT EXISTS idx_reportes_colegio_estado ON reportes_convivencia(colegio_id, estado)",
        "CREATE INDEX IF NOT EXISTS idx_rep_bit_colegio_reporte ON reportes_convivencia_bitacora(colegio_id, reporte_id)",
        "CREATE INDEX IF NOT EXISTS idx_promo_colegio_fecha ON promocion_actividades(colegio_id, fecha)",
        "CREATE INDEX IF NOT EXISTS idx_promo_evid_act ON promocion_evidencias(actividad_id)",
    ):
        try:
            execute(conn, stmt)
        except Exception:
            pass

    p = ph()

    cnt = execute(conn, "SELECT COUNT(*) as c FROM colegios", fetch="one")
    if (cnt or {}).get("c", 0) == 0:
        execute(
            conn,
            f"INSERT INTO colegios (nombre,nit,municipio,rector,direccion,telefono,email) VALUES ({p},{p},{p},{p},{p},{p},{p})",
            (
                "Colegio San José",
                "890.123.456-7",
                "Medellín",
                "Dr. Luis Gómez",
                "Calle 50 # 40-20",
                "604-2345678",
                "info@sanjose.edu.co",
            ),
        )

    cnt = execute(conn, "SELECT COUNT(*) as c FROM usuarios", fetch="one")
    if (cnt or {}).get("c", 0) == 0:
        for u in [
            ("superadmin", hpwd("super123"), "Superadmin", "Super Administrador", "", None),
            ("admin", hpwd("admin123"), "Coordinador", "Ana Coordinadora", "", 1),
            ("director1", hpwd("dir123"), "Director", "Carlos Director", "6A", 1),
            ("orientador1", hpwd("ori123"), "Orientador", "Pilar Orientadora", "", 1),
            ("docente1", hpwd("doc123"), "Docente", "María Docente", "", 1),
        ]:
            execute(
                conn,
                f"INSERT INTO usuarios (usuario,contrasena,rol,nombre,curso,colegio_id) VALUES ({p},{p},{p},{p},{p},{p})",
                u,
            )

    cnt = execute(conn, "SELECT COUNT(*) as c FROM catalogo_faltas", fetch="one")
    if (cnt or {}).get("c", 0) == 0:
        for c in [
            ("Tipo I", "Llegar tarde al aula de clase", "El docente realiza llamado verbal y registra en el observador.", "Llamado verbal. Registro en observador.", 1),
            ("Tipo I", "No portar el uniforme completo", "Diálogo formativo y comunicación al acudiente.", "Llamado escrito. Comunicación al acudiente.", 1),
            ("Tipo I", "Uso inadecuado del celular en clase", "El docente retiene el dispositivo.", "Retención del dispositivo. Llamado escrito.", 1),
            ("Tipo I", "Vocabulario inapropiado", "Reflexión pedagógica inmediata.", "Compromiso escrito. Comunicación al acudiente.", 1),
            ("Tipo II", "Agresión verbal a compañeros", "Intervención del director. Citación al acudiente. Remisión a orientación.", "Llamado escrito con firma. Compromiso de convivencia.", 1),
            ("Tipo II", "Daño a propiedad de la institución", "Notificación a coordinación y acudiente.", "Reparación del bien. Trabajo comunitario.", 1),
            ("Tipo II", "Falsificación de firmas o documentos", "Remisión a coordinación. Proceso disciplinar formal.", "Suspensión 1 a 3 días. Compromiso formal.", 1),
            ("Tipo III", "Agresión física", "Activación de la Ruta de Atención Integral. Notificación a rector.", "Suspensión inmediata. Remisión al Comité.", 1),
            ("Tipo III", "Porte de sustancias psicoactivas", "Llamado a padres y Policía de Infancia. RAI.", "Suspensión inmediata. Comité Municipal.", 1),
            ("Tipo III", "Acoso escolar comprobado", "Activación RAI. Orientación y autoridades.", "Matrícula en observación. Seguimiento psicosocial.", 1),
        ]:
            execute(conn, f"INSERT INTO catalogo_faltas (tipo,descripcion,protocolo,sancion,colegio_id) VALUES ({p},{p},{p},{p},{p})", c)

    cnt = execute(conn, "SELECT COUNT(*) as c FROM estudiantes", fetch="one")
    if (cnt or {}).get("c", 0) == 0:
        for e in [
            ("1001234567", "Alejandro Pérez", "6A", "Ninguna", "Roberto Pérez", "1234567", "3001234567", "Calle 10 # 5-20", 1),
            ("1007654321", "Valentina Torres", "6A", "Ninguna", "Claudia Torres", "7654321", "3107654321", "Carrera 8 # 12-45", 1),
            ("1008901234", "Sebastián García", "6A", "", "Luis García", "8901234", "3208901234", "Calle 15 # 8-10", 1),
            ("1005678901", "Daniela Martínez", "6B", "Hipoacusia leve", "Gloria Martínez", "5678901", "3115678901", "Av. 30 # 25-60", 1),
            ("1009012345", "Isabella López", "7A", "", "Carmen López", "9012345", "3209012345", "Carrera 45 # 10-20", 1),
            ("1003456789", "Samuel Hernández", "7A", "TDAH", "Ana Hernández", "3456789", "3113456789", "Calle 5 # 2-15", 1),
        ]:
            cur2 = execute(
                conn,
                f"INSERT INTO estudiantes (documento_identidad,nombre,curso,discapacidad,acudiente,cedula_acudiente,telefono,direccion,colegio_id) VALUES ({p},{p},{p},{p},{p},{p},{p},{p},{p})",
                e,
            )
            if USE_PG:
                eid_row = execute(conn, "SELECT lastval() as lid", fetch="one")
                eid = eid_row["lid"]
            else:
                eid = cur2.lastrowid
            cedula = str(e[5])
            ex = execute(conn, f"SELECT id FROM usuarios WHERE usuario={p}", (cedula,), fetch="one")
            if not ex:
                execute(
                    conn,
                    f"INSERT INTO usuarios (usuario,contrasena,rol,nombre,curso,colegio_id,estudiante_id) VALUES ({p},{p},{p},{p},{p},{p},{p})",
                    (cedula, hpwd(cedula), "Acudiente", e[4], e[2], 1, eid),
                )

    cnt = execute(conn, "SELECT COUNT(*) as c FROM faltas", fetch="one")
    if (cnt or {}).get("c", 0) == 0:
        _y = datetime.now().year
        for f in [
            (_y, f"{_y}-02-10", "6A", "Alejandro Pérez", 1, "Tipo I", "Llegar tarde al aula de clase", "Llegó 20 minutos tarde.", "Llamado verbal.", "", "", "María Docente", 1),
            (_y, f"{_y}-02-20", "6A", "Alejandro Pérez", 1, "Tipo I", "Uso inadecuado del celular en clase", "Usando celular en clase.", "Se retuvo el celular.", "", "", "María Docente", 1),
            (_y, f"{_y}-03-05", "6A", "Alejandro Pérez", 1, "Tipo I", "Vocabulario inapropiado", "Usó palabras soeces.", "Reflexión y compromiso verbal.", "", "", "María Docente", 1),
            (_y, f"{_y}-03-15", "6A", "Valentina Torres", 2, "Tipo II", "Agresión verbal a compañeros", "Discusión fuerte en recreo.", "Llamado escrito.", "Intervención del director. Citación al acudiente.", "Llamado escrito con firma. Compromiso de convivencia.", "María Docente", 1),
            (_y, f"{_y}-03-20", "6B", "Daniela Martínez", 4, "Tipo III", "Agresión física", "Golpeó a compañero.", "Se notificó coordinación.", "Activación RAI.", "Suspensión 3 días. Comité de Convivencia.", "Carlos Director", 1),
        ]:
            cur3 = execute(
                conn,
                f"INSERT INTO faltas (anio,fecha,curso,estudiante,estudiante_id,tipo_falta,falta_especifica,descripcion,proceso_inicial,protocolo_aplicado,sancion_aplicada,docente,colegio_id) VALUES ({p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p})",
                f,
            )
            if USE_PG:
                fid_row = execute(conn, "SELECT lastval() as lid", fetch="one")
                fid = fid_row["lid"]
            else:
                fid = cur3.lastrowid
            if f[5] == "Tipo II":
                for a in [
                    (fid, "Director", "Carlos Director", f"{_y}-03-16", "Se citó al acudiente. Reunión realizada. Compromiso firmado."),
                    (fid, "Coordinador", "Ana Coordinadora", f"{_y}-03-18", "Reunión con acudiente exitosa. Seguimiento mensual."),
                    (fid, "Orientador", "Pilar Orientadora", f"{_y}-03-19", "Primera sesión. Conflicto con grupo de pares identificado."),
                ]:
                    execute(conn, f"INSERT INTO anotaciones (falta_id,rol,autor,fecha,texto) VALUES ({p},{p},{p},{p},{p})", a)
            elif f[5] == "Tipo III":
                for a in [
                    (fid, "Coordinador", "Ana Coordinadora", f"{_y}-03-20", "RAI activada. Padres notificados."),
                    (fid, "Orientador", "Pilar Orientadora", f"{_y}-03-21", "Sesión de crisis. Remisión a psicología externa."),
                ]:
                    execute(conn, f"INSERT INTO anotaciones (falta_id,rol,autor,fecha,texto) VALUES ({p},{p},{p},{p},{p})", a)
    _backfill_reporte_tokens(conn)
    commit(conn)
    conn.close()
