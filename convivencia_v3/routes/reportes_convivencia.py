"""Reportes ciudadanos estudiantiles (Ley 1620): no son faltas hasta validación del comité."""
import os
import secrets
from datetime import date, datetime, timezone

from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename

from ce_db import USE_PG, commit, execute, get_db, ph
from ce_utils import hpwd, solo_numeros
from routes.authz import cu, login_required, resolve_colegio_id, roles

bp = Blueprint("reportes_convivencia", __name__)

_PKG_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
UPLOAD_REPORTES = os.path.join(_PKG_ROOT, "static", "uploads", "reportes_estudiante")
_IMG_EXT = frozenset({".jpg", ".jpeg", ".png", ".webp", ".gif"})

CAT_VISUAL = frozenset({"mal", "molestan", "mal_colegio", "peligro"})
A_QUIEN = frozenset({"yo", "amigo", "grupo"})
LUGAR_CLAVE = frozenset({"patio", "salon", "banos", "redes", "comedor", "entrada", "otro"})
URGENCIA = frozenset({"normal", "urgente"})
ESTADOS = frozenset({"pendiente_validacion", "caso_abierto", "orientacion", "descartado"})


def _now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _today_iso():
    return date.today().isoformat()


def _get_form_or_json():
    if request.content_type and "multipart/form-data" in request.content_type:
        return request.form.to_dict(), request.files.get("evidencia")
    return request.get_json(silent=True) or {}, None


def _resolve_estudiante(conn, colegio_id: int, d: dict):
    """Identifica al estudiante por token (QR/enlace) o documento + PIN."""
    p = ph()
    token = (d.get("token") or "").strip()
    documento = solo_numeros(d.get("documento_identidad") or d.get("documento") or "")
    pin = (d.get("pin") or "").strip()
    if token:
        row = execute(
            conn,
            f"SELECT * FROM estudiantes WHERE colegio_id={p} AND reporte_token={p}",
            (colegio_id, token),
            fetch="one",
        )
        if not row:
            return None, "El enlace no es válido para esta institución. Pide ayuda a orientación."
        return row, None
    if documento and pin:
        row = execute(
            conn,
            f"SELECT * FROM estudiantes WHERE colegio_id={p} AND documento_identidad={p}",
            (colegio_id, documento),
            fetch="one",
        )
        if not row:
            return None, "No encontramos ese documento en esta institución."
        ph_pin = (row.get("reporte_pin_hash") or "").strip()
        if not ph_pin:
            return None, "Tu colegio aún no activó el PIN para tu documento. Usa el enlace personal (QR) o pregunta en secretaría."
        if hpwd(pin) != ph_pin:
            return None, "PIN incorrecto."
        return row, None
    return None, "Identifícate con tu enlace personal (QR) o con tu documento y PIN."


def _save_evidencia(file_storage, colegio_id: int, rid: int) -> str:
    if not file_storage or not file_storage.filename:
        return ""
    os.makedirs(UPLOAD_REPORTES, exist_ok=True)
    orig = secure_filename(file_storage.filename) or "img"
    ext = os.path.splitext(orig)[1].lower()
    if ext not in _IMG_EXT:
        raise ValueError("La evidencia debe ser imagen (jpg, png, webp o gif).")
    name = f"{colegio_id}_{rid}_{secrets.token_hex(8)}{ext}"
    dest = os.path.join(UPLOAD_REPORTES, name)
    file_storage.save(dest)
    return os.path.join("reportes_estudiante", name).replace("\\", "/")


@bp.route("/api/public/colegios/<int:cid>", methods=["GET"])
def api_public_colegio(cid):
    """Datos mínimos para la pantalla de reporte (sin sesión)."""
    conn = get_db()
    p = ph()
    row = execute(conn, f"SELECT id, nombre FROM colegios WHERE id={p}", (cid,), fetch="one")
    conn.close()
    if not row:
        return jsonify({"ok": False, "error": "Institución no encontrada."}), 404
    return jsonify({"ok": True, "id": row["id"], "nombre": row.get("nombre") or ""})


@bp.route("/api/reportes-convivencia", methods=["POST"])
def api_reporte_crear():
    """Alta pública: alerta ciudadana estudiantil (no crea falta)."""
    d, file_ev = _get_form_or_json()
    try:
        colegio_id = int(d.get("colegio_id") or 0)
    except (TypeError, ValueError):
        colegio_id = 0
    if colegio_id <= 0:
        return jsonify({"ok": False, "error": "Falta institución (colegio_id)."}), 400

    cat = (d.get("categoria_visual") or "").strip()
    quien = (d.get("a_quien") or "").strip()
    desc = (d.get("descripcion") or "").strip()
    lugar = (d.get("lugar_clave") or "").strip()
    urg = (d.get("urgencia") or "").strip()
    fue_hoy = str(d.get("fue_hoy", "1")).lower() in ("1", "true", "yes", "si", "sí")
    fecha_otra = (d.get("fecha_incidente") or "").strip()[:12]

    if cat not in CAT_VISUAL:
        return jsonify({"ok": False, "error": "Elige una categoría válida."}), 400
    if quien not in A_QUIEN:
        return jsonify({"ok": False, "error": "Indica a quién le pasó (yo, amigo o grupo)."}), 400
    if lugar not in LUGAR_CLAVE:
        return jsonify({"ok": False, "error": "Indica un lugar del colegio."}), 400
    if urg not in URGENCIA:
        return jsonify({"ok": False, "error": "Indica cómo te sientes respecto a la espera."}), 400
    if len(desc) < 8:
        return jsonify({"ok": False, "error": "Cuéntanos un poco más (al menos 8 caracteres)."}), 400
    if len(desc) > 500:
        return jsonify({"ok": False, "error": "El texto es muy largo (máximo 500 caracteres)."}), 400

    fecha_inc = _today_iso() if fue_hoy else (fecha_otra or _today_iso())

    conn = get_db()
    est, err = _resolve_estudiante(conn, colegio_id, d)
    if err:
        conn.close()
        return jsonify({"ok": False, "error": err}), 400

    p = ph()
    creado = _now_iso()
    execute(
        conn,
        f"""INSERT INTO reportes_convivencia (
            colegio_id, estudiante_id, estudiante_nombre, curso,
            categoria_visual, a_quien, descripcion, fue_hoy, fecha_incidente,
            lugar_clave, urgencia, evidencia_path, estado, nota_comite, creado_en, actualizado_en
        ) VALUES ({p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p})""",
        (
            colegio_id,
            est["id"],
            (est.get("nombre") or "")[:200],
            (est.get("curso") or "")[:80],
            cat,
            quien,
            desc,
            1 if fue_hoy else 0,
            fecha_inc[:10],
            lugar,
            urg,
            "",
            "pendiente_validacion",
            "",
            creado,
            creado,
        ),
    )
    if USE_PG:
        rid = int(execute(conn, "SELECT lastval() as lid", fetch="one")["lid"])
    else:
        rid = int(execute(conn, "SELECT last_insert_rowid() as lid", fetch="one")["lid"])

    ev_path = ""
    if file_ev and file_ev.filename:
        try:
            ev_path = _save_evidencia(file_ev, colegio_id, rid)
            if ev_path:
                execute(
                    conn,
                    f"UPDATE reportes_convivencia SET evidencia_path={p}, actualizado_en={p} WHERE id={p}",
                    (ev_path, _now_iso(), rid),
                )
        except ValueError as e:
            conn.close()
            return jsonify({"ok": False, "error": str(e)}), 400

    commit(conn)
    conn.close()

    # Notificación push al orientador: pendiente de integración (bandera urgente en listado).
    return jsonify(
        {
            "ok": True,
            "id": rid,
            "mensaje_confirmacion": _mensaje_confirmacion(urg == "urgente"),
            "urgencia": urg,
        }
    )


def _mensaje_confirmacion(urgente: bool):
    if urgente:
        return (
            "Recibimos tu mensaje como urgente. Un adulto de confianza del colegio lo verá pronto. "
            "Si estás en peligro inmediato, busca a un docente o ve a portería ahora."
        )
    return (
        "Gracias por confiar en nosotros. Lo que escribiste es confidencial dentro del equipo de convivencia. "
        "Un profesional lo revisará y, si hace falta, te contactará por los medios que el colegio tiene registrados."
    )


@bp.route("/api/reportes-convivencia", methods=["GET"])
@login_required
@roles("Coordinador", "Orientador", "Superadmin")
def api_reportes_listar():
    u = cu()
    tenant_id, terr = resolve_colegio_id(u)
    if terr:
        return jsonify({"error": terr}), 400
    estado = (request.args.get("estado") or "").strip()
    conn = get_db()
    p = ph()
    q = f"SELECT * FROM reportes_convivencia WHERE colegio_id={p}"
    params = [tenant_id]
    if estado in ESTADOS:
        q += f" AND estado={p}"
        params.append(estado)
    q += " ORDER BY urgencia DESC, creado_en DESC LIMIT 200"
    rows = execute(conn, q, params, fetch="all")
    conn.close()
    return jsonify(rows or [])


@bp.route("/api/reportes-convivencia/<int:rid>", methods=["PATCH"])
@login_required
@roles("Coordinador", "Orientador", "Superadmin")
def api_reporte_actualizar(rid):
    d = request.get_json(silent=True) or {}
    nuevo = (d.get("estado") or "").strip()
    if nuevo not in ESTADOS:
        return jsonify({"ok": False, "error": "Estado no válido."}), 400
    nota = (d.get("nota_comite") or "").strip()[:2000]
    if nuevo == "descartado" and len(nota) < 3:
        return jsonify({"ok": False, "error": "Para descartar, registre brevemente el motivo (auditoría)."}), 400

    u = cu()
    tenant_id, terr = resolve_colegio_id(u)
    if terr:
        return jsonify({"ok": False, "error": terr}), 400

    conn = get_db()
    p = ph()
    row = execute(
        conn,
        f"SELECT id FROM reportes_convivencia WHERE id={p} AND colegio_id={p}",
        (rid, tenant_id),
        fetch="one",
    )
    if not row:
        conn.close()
        return jsonify({"ok": False, "error": "No encontrado."}), 404

    execute(
        conn,
        f"UPDATE reportes_convivencia SET estado={p}, nota_comite={p}, actualizado_en={p} WHERE id={p}",
        (nuevo, nota, _now_iso(), rid),
    )
    commit(conn)
    conn.close()
    return jsonify({"ok": True})
