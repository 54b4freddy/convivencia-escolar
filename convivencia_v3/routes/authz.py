"""Autenticación y autorización por roles (sesión Flask)."""
from functools import wraps

from flask import jsonify, session


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
