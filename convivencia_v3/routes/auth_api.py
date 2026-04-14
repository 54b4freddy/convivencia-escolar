"""Rutas de sesión: login, logout, registro público, /api/me."""
import os

from flask import Blueprint, jsonify, request, session

from ce_db import commit, execute, get_db, ph
from ce_utils import hpwd
from routes.authz import cu, login_required

bp = Blueprint("auth_api", __name__)


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
    u = execute(
        conn,
        f"SELECT u.*,c.nombre as col_nom FROM usuarios u LEFT JOIN colegios c ON c.id=u.colegio_id WHERE u.usuario={p} AND u.contrasena={p}",
        (d.get("usuario", "").strip(), hpwd(d.get("contrasena", ""))),
        fetch="one",
    )
    conn.close()
    if not u:
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
    return jsonify({"ok": True, "usuario": session["usuario"]})


@bp.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"ok": True})


def _registro_publico_permitido():
    return os.environ.get("REGISTRATION_OPEN", "1").lower() in ("1", "true", "yes", "on")


@bp.route("/api/registrar-usuario", methods=["POST"])
def api_registrar_usuario():
    """Alta desde login (asigna al primer colegio). Desactivar en producción: REGISTRATION_OPEN=0."""
    if not _registro_publico_permitido():
        return jsonify({"ok": False, "error": "El registro público está desactivado."}), 403
    d = request.json or {}
    rol = (d.get("rol") or "").strip()
    if rol in ("Superadmin", "Acudiente", ""):
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
    return jsonify(u)
