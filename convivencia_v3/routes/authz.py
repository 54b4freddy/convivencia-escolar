"""Autenticación y autorización por roles (sesión Flask)."""
import logging
from datetime import datetime, timezone
from functools import wraps

from flask import jsonify, request, session

logger = logging.getLogger(__name__)

ERR_SESION_SIN_COLEGIO = (
    "sesión inválida: colegio_id no encontrado. Cierre sesión y vuelva a ingresar."
)


def resolve_colegio_id(u):
    """Colegio efectivo para operaciones multi-tenant.

    - Si el usuario tiene `colegio_id` en sesión (entero > 0), se usa.
    - Si es Superadmin sin colegio en sesión o con valor inválido, debe enviar
      `colegio_id` en querystring (GET) o en JSON / form (POST/PATCH/PUT/DELETE).
    - Otros roles sin colegio resoluble en sesión: error explícito (no hay fallback
      a otro colegio).

    Retorna ``(colegio_id:int|None, error:str|None)``. Si ``error`` no es None, responder 400.
    """
    rid = u.get("colegio_id")
    if rid is not None and rid != "":
        try:
            cid = int(rid)
        except (TypeError, ValueError):
            return None, "colegio_id de sesión inválido"
        if cid > 0:
            return cid, None
        # 0 o negativo: no es tenant válido; Superadmin puede seguir con el request
        if u.get("rol") != "Superadmin":
            logger.warning(
                "resolve_colegio_id: staff sin colegio_id resoluble en sesión (usuario_id=%s, rol=%s, ts=%s)",
                u.get("id"),
                u.get("rol"),
                datetime.now(timezone.utc).isoformat(),
            )
            return None, ERR_SESION_SIN_COLEGIO
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
    logger.warning(
        "resolve_colegio_id: staff sin colegio_id resoluble en sesión (usuario_id=%s, rol=%s, ts=%s)",
        u.get("id"),
        u.get("rol"),
        datetime.now(timezone.utc).isoformat(),
    )
    return None, ERR_SESION_SIN_COLEGIO


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
