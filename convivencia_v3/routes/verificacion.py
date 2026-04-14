"""Verificación pública de integridad del acta de descargos (sin sesión)."""
import json

from flask import Blueprint, current_app, jsonify

from ce_acta_descargos import normalize_acta_datos, verify_integrity
from ce_db import execute, get_db, ph

bp = Blueprint("verificacion", __name__)


@bp.route("/api/verificar-descargos/<token>")
def api_verificar_descargos(token):
    tok = (token or "").strip()
    if len(tok) < 12:
        return jsonify({"ok": False, "error": "Token inválido"}), 400
    conn = get_db()
    p = ph()
    row = execute(
        conn,
        f"SELECT a.*, c.nombre as colegio_nombre FROM acta_descargos a "
        f"JOIN colegios c ON c.id=a.colegio_id WHERE a.verificacion_token={p}",
        (tok,),
        fetch="one",
    )
    conn.close()
    if not row:
        return jsonify({"ok": False, "error": "No se encontró un acta con este código"}), 404
    try:
        datos = json.loads(row.get("datos_json") or "{}")
    except json.JSONDecodeError:
        datos = {}
    datos_n = normalize_acta_datos(datos)
    fid = int(row.get("falta_id") or 0)
    cid = int(row.get("colegio_id") or 0)
    ok = verify_integrity(
        current_app.secret_key,
        fid,
        cid,
        datos_n,
        row.get("content_hash") or "",
        row.get("firma_hmac") or "",
    )
    return jsonify(
        {
            "ok": True,
            "integridad": "válida" if ok else "no_válida",
            "registro_falta_id": fid,
            "institucion": row.get("colegio_nombre") or "",
            "acta_registrada": row.get("registrado_en"),
            "acta_actualizada": row.get("actualizado_en"),
            "mensaje": (
                "Los datos almacenados coinciden con la huella criptográfica registrada."
                if ok
                else "Los datos no coinciden con la firma registrada (posible alteración o clave distinta)."
            ),
        }
    )
