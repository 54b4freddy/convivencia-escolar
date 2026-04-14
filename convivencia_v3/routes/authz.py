"""Autenticación y autorización por roles (sesión Flask)."""
from functools import wraps

from flask import jsonify, request, session


def resolve_colegio_id(u):
    """Colegio efectivo para operaciones multi-tenant.

    - Si el usuario tiene `colegio_id` en sesión, se usa (entero).
    - Si es Superadmin sin colegio asignado, debe enviar `colegio_id` en querystring
      (GET) o en JSON / form (POST/PATCH/PUT/DELETE).
    - Otros roles sin colegio en sesión: se asume `1` (compatibilidad con datos viejos).

    Retorna ``(colegio_id:int|None, error:str|None)``. Si ``error`` no es None, responder 400.
    """
    rid = u.get("colegio_id")
    if rid is not None and rid != "":
        try:
            return int(rid), None
        except (TypeError, ValueError):
            return None, "colegio_id de sesión inválido"
    if u.get("rol") == "Superadmin":
        raw = request.args.get("colegio_id")
        if raw is None and request.method in ("POST", "PATCH", "PUT", "DELETE"):
            raw = request.form.get("colegio_id")
            if raw is None:
                js = request.get_json(silent=True)
                if isinstance(js, dict):
                    raw = js.get("colegio_id")
        try:
            cid = int(raw)
        except (TypeError, ValueError):
            cid = 0
        if cid <= 0:
            return None, "Para Superadmin, envíe colegio_id"
        return cid, None
    return 1, None


def login_required(f):
    @wraps(f)
    def dec(*a, **kw):
        if "usuario" not in session:
            return jsonify({"error": "No autenticado"}), 401
        return f(*a, **kw)

    return dec


def roles(*rs):
    def deco(f):
        @wraps(f)
        def dec(*a, **kw):
            if "usuario" not in session:
                return jsonify({"error": "No autenticado"}), 401
            if session["usuario"]["rol"] not in rs:
                return jsonify({"error": "Sin permisos"}), 403
            return f(*a, **kw)

        return dec

    return deco


def cu():
    return session.get("usuario", {})
