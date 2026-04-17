"""Rutas de sesión: login, logout, registro público, /api/me."""
import os

from flask import Blueprint, jsonify, request, session

from ce_db import commit, execute, get_db, ph
from ce_utils import clave_portal_estudiante_por_defecto, hpwd, solo_numeros
from routes.authz import cu, login_required

bp = Blueprint("auth_api", __name__)


def _norm_nombre_inst(s: str) -> str:
    return " ".join((s or "").lower().split())


def _coincide_nombre_inst(nombre_colegio: str, busqueda: str) -> bool:
    """Compara nombre oficial del colegio con lo que escribe el estudiante (carnet)."""
    nom = _norm_nombre_inst(nombre_colegio)
    t = _norm_nombre_inst(busqueda)
    if len(t) < 2:
        return False
    if t in nom:
        return True
    words = [w for w in t.split() if len(w) >= 2]
    if not words:
        return False
    return all(w in nom for w in words)


def _login_estudiante_por_documento(conn, d):
    """Documento + contraseña. Si hay varios colegios, puede acotar con colegio_id o nombre de institución."""
    doc = solo_numeros((d.get("usuario") or "").strip())
    if len(doc) < 5:
        return None, None
    pwd_h = hpwd(d.get("contrasena") or "")
    p = ph()
    base = (
        f"SELECT u.*, c.nombre AS col_nom, e.documento_identidad AS est_documento FROM usuarios u "
        f"JOIN estudiantes e ON e.id = u.estudiante_id "
        f"LEFT JOIN colegios c ON c.id = u.colegio_id "
        f"WHERE u.rol = 'Estudiante' AND e.documento_identidad = {p} AND u.contrasena = {p}"
    )
    raw_c = d.get("colegio_id")
    cid = None
    if raw_c is not None and str(raw_c).strip() != "":
        try:
            cid = int(raw_c)
        except (TypeError, ValueError):
            cid = None
    if cid and cid > 0:
        u = execute(conn, base + f" AND e.colegio_id = {p}", (doc, pwd_h, cid), fetch="one")
        return (u, None) if u else (None, None)

    rows = execute(conn, base, (doc, pwd_h), fetch="all") or []
    nombre_filtro = (d.get("colegio_nombre") or d.get("institucion") or "").strip()

    if len(rows) > 1 and nombre_filtro:
        rows = [r for r in rows if _coincide_nombre_inst(r.get("col_nom") or "", nombre_filtro)]
        if len(rows) == 1:
            return rows[0], None
        if len(rows) == 0:
            return None, "bad_institucion"
        return None, "ambiguous"

    if len(rows) == 1:
        return rows[0], None
    if len(rows) > 1:
        return None, "ambiguous"
    return None, None


def _norm_colegio_id(v):
    """Entero o None (JSON estable para multi-colegio)."""
    if v is None or v == "":
        return None
    try:
        i = int(v)
        return i if i > 0 else None
    except (TypeError, ValueError):
        return None


@bp.route("/api/login", methods=["POST"])
def api_login():
    d = request.json or {}
    conn = get_db()
    p = ph()
    usuario_in = (d.get("usuario") or "").strip()
    u = execute(
        conn,
        f"SELECT u.*,c.nombre as col_nom FROM usuarios u LEFT JOIN colegios c ON c.id=u.colegio_id WHERE u.usuario={p} AND u.contrasena={p}",
        (usuario_in, hpwd(d.get("contrasena", ""))),
        fetch="one",
    )
    amb = None
    if not u:
        u, amb = _login_estudiante_por_documento(conn, d)
    conn.close()
    if not u:
        if amb == "ambiguous":
            return jsonify(
                {
                    "ok": False,
                    "error": "Este documento está en más de un colegio. Escriba el nombre de su institución (como en el carnet).",
                    "need_institucion": True,
                }
            ), 401
        if amb == "bad_institucion":
            return jsonify(
                {
                    "ok": False,
                    "error": "Ese nombre no coincide con ninguno de los colegios donde figura su documento. Pruebe más palabras del nombre oficial.",
                    "need_institucion": True,
                }
            ), 401
        return jsonify({"ok": False, "error": "Usuario o contraseña incorrectos"}), 401
    session["usuario"] = {
        "id": u["id"],
        "usuario": u["usuario"],
        "rol": u["rol"],
        "nombre": u["nombre"],
        "curso": u.get("curso", ""),
        "colegio_id": _norm_colegio_id(u.get("colegio_id")),
        "colegio_nombre": u.get("col_nom", "") or "",
        "estudiante_id": u.get("estudiante_id"),
        "asignatura": u.get("asignatura") or "",
        "telefono": u.get("telefono") or "",
    }
    out = {"ok": True, "usuario": session["usuario"]}
    if u.get("rol") == "Estudiante":
        doc_est = solo_numeros(str(u.get("est_documento") or ""))
        ch = str(u.get("contrasena") or "")
        if doc_est and ch == hpwd(clave_portal_estudiante_por_defecto(doc_est)):
            out["sugerir_cambio_clave_estudiante"] = True
    return jsonify(out)


@bp.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"ok": True})


def _registro_publico_permitido():
    """Por defecto cerrado: los accesos se crean desde gestión (usuarios / estudiantes). REGISTRATION_OPEN=1 solo para entornos de prueba."""
    return os.environ.get("REGISTRATION_OPEN", "0").lower() in ("1", "true", "yes", "on")


@bp.route("/api/registrar-usuario", methods=["POST"])
def api_registrar_usuario():
    """Alta desde login (legado; desactivado por defecto). Activar solo con REGISTRATION_OPEN=1."""
    if not _registro_publico_permitido():
        return jsonify({"ok": False, "error": "El registro público está desactivado."}), 403
    d = request.json or {}
    rol = (d.get("rol") or "").strip()
    if rol in ("Superadmin", "Acudiente", "Estudiante", ""):
        return jsonify({"ok": False, "error": "Rol no permitido para este registro."}), 400
    nombre = (d.get("nombre") or "").strip()
    usuario = (d.get("usuario") or "").strip()
    contrasena = d.get("contrasena") or ""
    curso = (d.get("curso") or "").strip()
    if rol == "Director" and not curso:
        return jsonify({"ok": False, "error": "El director debe indicar curso."}), 400
    if not nombre or not usuario or not contrasena:
        return jsonify({"ok": False, "error": "Faltan datos obligatorios."}), 400
    conn = get_db()
    p = ph()
    col = execute(conn, "SELECT id FROM colegios ORDER BY id LIMIT 1", fetch="one")
    cid = col["id"] if col else 1
    try:
        execute(
            conn,
            f"INSERT INTO usuarios (usuario,contrasena,rol,nombre,curso,colegio_id,asignatura) VALUES ({p},{p},{p},{p},{p},{p},{p})",
            (usuario, hpwd(contrasena), rol, nombre, curso if rol == "Director" else "", cid, ""),
        )
        commit(conn)
        conn.close()
        return jsonify({"ok": True})
    except Exception:
        conn.close()
        return jsonify({"ok": False, "error": "El usuario ya existe o no se pudo crear."}), 409


@bp.route("/api/me")
@login_required
def api_me():
    u = dict(cu())
    u["colegio_id"] = _norm_colegio_id(u.get("colegio_id"))
    if u.get("rol") == "Estudiante" and u.get("estudiante_id"):
        conn = get_db()
        p = ph()
        row = execute(
            conn,
            f"SELECT u.contrasena, e.documento_identidad FROM usuarios u "
            f"JOIN estudiantes e ON e.id = u.estudiante_id WHERE u.id = {p} AND u.rol = 'Estudiante'",
            (int(u["id"]),),
            fetch="one",
        )
        conn.close()
        if row:
            doc_est = solo_numeros(str(row.get("documento_identidad") or ""))
            ch = str(row.get("contrasena") or "")
            u["sugerir_cambio_clave_estudiante"] = bool(
                doc_est and ch == hpwd(clave_portal_estudiante_por_defecto(doc_est))
            )
    return jsonify(u)


@bp.route("/api/me/cambiar-clave-estudiante", methods=["POST"])
@login_required
def api_me_cambiar_clave_estudiante():
    """Solo rol Estudiante: cambiar contraseña del portal (mín. 4 caracteres)."""
    me = cu()
    if me.get("rol") != "Estudiante":
        return jsonify({"ok": False, "error": "Solo aplica a sesión de estudiante."}), 403
    d = request.json or {}
    actual = d.get("contrasena_actual") or ""
    nueva = (d.get("contrasena_nueva") or "").strip()
    if len(nueva) < 4:
        return jsonify({"ok": False, "error": "La nueva contraseña debe tener al menos 4 caracteres."}), 400
    if len(nueva) > 80:
        return jsonify({"ok": False, "error": "Contraseña demasiado larga."}), 400
    conn = get_db()
    p = ph()
    row = execute(conn, f"SELECT id, contrasena FROM usuarios WHERE id={p} AND rol='Estudiante'", (int(me["id"]),), fetch="one")
    if not row or row.get("contrasena") != hpwd(actual):
        conn.close()
        return jsonify({"ok": False, "error": "Contraseña actual incorrecta."}), 400
    execute(conn, f"UPDATE usuarios SET contrasena={p} WHERE id={p}", (hpwd(nueva), int(me["id"])))
    commit(conn)
    conn.close()
    return jsonify({"ok": True})
