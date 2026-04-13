"""Señales de atención / conductas de riesgo (bienestar; no constituye diagnóstico)."""
import os
import secrets
from datetime import datetime

from flask import Blueprint, jsonify, request, send_file
from werkzeug.utils import secure_filename

from ce_db import USE_PG, commit, execute, get_db, ph
from routes.authz import cu, login_required, roles

_PKG_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
UPLOAD_FOLDER = os.path.join(_PKG_ROOT, "static", "uploads")
UPLOAD_CONDUCTAS = os.path.join(UPLOAD_FOLDER, "conductas")

_SENALES_CAT = frozenset(
    {"alimentacion", "familia_acomp", "abandono_riesgo", "bienestar_general", "discapacidad_apoyo", "otro"}
)
_CONDUCTA_TIPOS = frozenset({"conv_i", "conv_ii", "conv_iii"})
_SUBS_POR_TIPO = {
    "conv_i": frozenset({"conflictos_manejables", "sin_dano"}),
    "conv_ii": frozenset({"bullying_incipiente", "afectacion_emocional", "conflictos_reiterados"}),
    "conv_iii": frozenset({"violencia_fisica", "abuso_sexual", "consumo_micro", "intento_suicidio"}),
}
_URGENCIAS = frozenset({"baja", "moderada", "alta", "critica"})

bp = Blueprint("senales", __name__)


def _accion_conducta(tipo: str, sub: str) -> str:
    if tipo == "conv_i":
        return "Manejo: docente + mediación pedagógica"
    if tipo == "conv_ii":
        return "Activación de ruta | Remisión a orientación escolar."
    if tipo == "conv_iii":
        return "Activación inmediata de ruta | Notificación a entidades externas (ICBF, salud, policía)."
    return ""


def _save_conducta_evidencia(file_storage, colegio_id: int) -> str:
    if not file_storage or not file_storage.filename:
        return ""
    os.makedirs(UPLOAD_CONDUCTAS, exist_ok=True)
    orig = secure_filename(file_storage.filename) or "archivo"
    ext = os.path.splitext(orig)[1].lower()
    if ext not in (".pdf", ".jpg", ".jpeg", ".png", ".webp", ".doc", ".docx"):
        raise ValueError("Evidencia: use PDF, imagen o Word (.pdf, .jpg, .png, .doc, .docx).")
    name = f"{colegio_id}_{secrets.token_hex(12)}{ext}"
    dest = os.path.join(UPLOAD_CONDUCTAS, name)
    file_storage.save(dest)
    return os.path.join("conductas", name).replace("\\", "/")


@bp.route("/api/senales-atencion")
@login_required
def api_senales_listar():
    u = cu()
    if u["rol"] == "Acudiente":
        return jsonify({"error": "Sin permisos"}), 403
    conn = get_db()
    p = ph()
    if u["rol"] == "Superadmin" and not u.get("colegio_id"):
        rows = execute(conn, "SELECT s.* FROM senales_atencion s ORDER BY s.fecha_registro DESC LIMIT 200", fetch="all")
    else:
        q = f"SELECT s.* FROM senales_atencion s WHERE s.colegio_id={p}"
        prm = [u["colegio_id"] or 1]
        if u["rol"] == "Docente":
            q += f" AND s.registrado_por_id={p}"
            prm.append(u["id"])
        elif u["rol"] == "Director" and u.get("curso"):
            q += f" AND s.curso={p}"
            prm.append(u["curso"])
        q += " ORDER BY s.fecha_registro DESC LIMIT 200"
        rows = execute(conn, q, prm, fetch="all")
    conn.close()
    return jsonify(rows)


@bp.route("/api/senales-atencion", methods=["POST"])
@roles("Superadmin", "Coordinador", "Orientador", "Director", "Docente")
def api_senales_crear():
    u = cu()
    file_storage = None
    if request.content_type and "multipart/form-data" in (request.content_type or ""):
        d = {k: (request.form.get(k) or "").strip() for k in request.form}
        file_storage = request.files.get("evidencia")
    else:
        d = request.json or {}
    conn = get_db()
    p = ph()
    cid = u["colegio_id"] or 1
    fe = datetime.now().strftime("%Y-%m-%d")

    tipo_con = (d.get("tipo_conducta") or "").strip()
    if tipo_con:
        if tipo_con not in _CONDUCTA_TIPOS:
            conn.close()
            return jsonify({"ok": False, "error": "Tipo de conducta no válido"}), 400
        sub = (d.get("subtipo") or d.get("subtipo_clave") or "").strip()
        if sub not in _SUBS_POR_TIPO.get(tipo_con, frozenset()):
            conn.close()
            return jsonify({"ok": False, "error": "La opción no corresponde al tipo seleccionado."}), 400
        urg = (d.get("urgencia") or "").strip()
        if urg not in _URGENCIAS:
            conn.close()
            return jsonify({"ok": False, "error": "Nivel de urgencia no válido."}), 400
        obs = (d.get("descripcion_objetiva") or d.get("observacion") or "").strip()
        if len(obs) < 10:
            conn.close()
            return jsonify({"ok": False, "error": "La descripción objetiva requiere al menos 10 caracteres."}), 400
        try:
            eid = int(d.get("estudiante_id") or 0)
        except (TypeError, ValueError):
            eid = 0
        if not eid:
            conn.close()
            return jsonify({"ok": False, "error": "Seleccione estudiante"}), 400
        est = execute(conn, f"SELECT * FROM estudiantes WHERE id={p} AND colegio_id={p}", (eid, cid), fetch="one")
        if not est:
            conn.close()
            return jsonify({"ok": False, "error": "Estudiante no encontrado"}), 404
        if u["rol"] == "Director" and u.get("curso") and est.get("curso") != u["curso"]:
            conn.close()
            return jsonify({"ok": False, "error": "Estudiante fuera de su curso"}), 403
        ev_path = ""
        if file_storage and file_storage.filename:
            try:
                ev_path = _save_conducta_evidencia(file_storage, cid)
            except ValueError as ex:
                conn.close()
                return jsonify({"ok": False, "error": str(ex)}), 400
        acc = _accion_conducta(tipo_con, sub)
        execute(
            conn,
            f"INSERT INTO senales_atencion (colegio_id,estudiante_id,estudiante_nombre,curso,categoria,observacion,"
            f"registrado_por_id,registrado_por_nombre,registrado_rol,fecha_registro,estado,nota_seguimiento,"
            f"tipo_conducta,subtipo_clave,accion_derivada,urgencia,evidencia_path) VALUES ({p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p})",
            (
                cid,
                eid,
                est["nombre"],
                est.get("curso") or "",
                "conducta_riesgo",
                obs,
                u["id"],
                u["nombre"],
                u["rol"],
                fe,
                "abierta",
                "",
                tipo_con,
                sub,
                acc,
                urg,
                ev_path,
            ),
        )
        if USE_PG:
            nid = execute(conn, "SELECT lastval() as lid", fetch="one")["lid"]
        else:
            nid = execute(conn, "SELECT last_insert_rowid() as lid", fetch="one")["lid"]
        commit(conn)
        conn.close()
        return jsonify({"ok": True, "id": nid})

    cat = (d.get("categoria") or "").strip()
    if cat not in _SENALES_CAT:
        conn.close()
        return jsonify({"ok": False, "error": "Categoría no válida"}), 400
    obs = (d.get("observacion") or "").strip()
    if len(obs) < 10:
        conn.close()
        return jsonify(
            {"ok": False, "error": "Amplíe la observación (mínimo 10 caracteres). No incluya diagnósticos clínicos."}
        ), 400
    eid = d.get("estudiante_id")
    if not eid:
        conn.close()
        return jsonify({"ok": False, "error": "Seleccione estudiante"}), 400
    est = execute(conn, f"SELECT * FROM estudiantes WHERE id={p} AND colegio_id={p}", (eid, cid), fetch="one")
    if not est:
        conn.close()
        return jsonify({"ok": False, "error": "Estudiante no encontrado"}), 404
    if u["rol"] == "Director" and u.get("curso") and est.get("curso") != u["curso"]:
        conn.close()
        return jsonify({"ok": False, "error": "Estudiante fuera de su curso"}), 403
    execute(
        conn,
        f"INSERT INTO senales_atencion (colegio_id,estudiante_id,estudiante_nombre,curso,categoria,observacion,registrado_por_id,registrado_por_nombre,registrado_rol,fecha_registro,estado,nota_seguimiento) VALUES ({p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p})",
        (cid, eid, est["nombre"], est.get("curso") or "", cat, obs, u["id"], u["nombre"], u["rol"], fe, "abierta", ""),
    )
    if USE_PG:
        nid = execute(conn, "SELECT lastval() as lid", fetch="one")["lid"]
    else:
        nid = execute(conn, "SELECT last_insert_rowid() as lid", fetch="one")["lid"]
    commit(conn)
    conn.close()
    return jsonify({"ok": True, "id": nid})


@bp.route("/api/senales-atencion/<int:sid>", methods=["PATCH"])
@roles("Superadmin", "Coordinador", "Orientador")
def api_senales_actualizar(sid):
    d = request.json or {}
    u = cu()
    conn = get_db()
    p = ph()
    s = execute(conn, f"SELECT * FROM senales_atencion WHERE id={p}", (sid,), fetch="one")
    if not s or (s["colegio_id"] != (u.get("colegio_id") or 1) and u["rol"] != "Superadmin"):
        conn.close()
        return jsonify({"error": "No encontrada"}), 404
    estado = d.get("estado")
    nota = (d.get("nota_seguimiento") or "").strip()
    if estado and estado not in ("abierta", "en_seguimiento", "cerrada"):
        conn.close()
        return jsonify({"error": "Estado inválido"}), 400
    if estado:
        execute(conn, f"UPDATE senales_atencion SET estado={p},nota_seguimiento={p} WHERE id={p}", (estado, nota, sid))
    elif nota is not None:
        execute(conn, f"UPDATE senales_atencion SET nota_seguimiento={p} WHERE id={p}", (nota, sid))
    commit(conn)
    conn.close()
    return jsonify({"ok": True})


@bp.route("/api/senales-atencion/<int:sid>/evidencia")
@login_required
def api_senales_evidencia(sid):
    u = cu()
    if u["rol"] == "Acudiente":
        return jsonify({"error": "Sin permisos"}), 403
    conn = get_db()
    p = ph()
    s = execute(conn, f"SELECT * FROM senales_atencion WHERE id={p}", (sid,), fetch="one")
    conn.close()
    if not s:
        return jsonify({"error": "No encontrada"}), 404
    if s.get("colegio_id") != (u.get("colegio_id") or 1) and u["rol"] != "Superadmin":
        return jsonify({"error": "No autorizado"}), 403
    if u["rol"] == "Docente" and s.get("registrado_por_id") != u.get("id"):
        return jsonify({"error": "No autorizado"}), 403
    if u["rol"] == "Director" and u.get("curso") and s.get("curso") != u["curso"]:
        return jsonify({"error": "No autorizado"}), 403
    rel = (s.get("evidencia_path") or "").strip()
    if not rel or ".." in rel:
        return jsonify({"error": "Sin evidencia"}), 404
    full = os.path.normpath(os.path.join(UPLOAD_FOLDER, rel.replace("/", os.sep)))
    if not full.startswith(os.path.normpath(UPLOAD_FOLDER)):
        return jsonify({"error": "Ruta inválida"}), 400
    if not os.path.isfile(full):
        return jsonify({"error": "Archivo no encontrado"}), 404
    return send_file(full, as_attachment=True, download_name=os.path.basename(full))
