"""Reportes ciudadanos estudiantiles (Ley 1620): no son faltas hasta validación del comité."""
import os
import secrets
from collections import Counter
from datetime import date, datetime, timedelta, timezone

from flask import Blueprint, jsonify, request, session
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


def _resolve_estudiante_o_sesion(conn, colegio_id: int, d: dict):
    """Sesión rol Estudiante (login con documento) o flujos públicos token/PIN."""
    su = session.get("usuario")
    if su and su.get("rol") == "Estudiante":
        eid = su.get("estudiante_id")
        if not eid:
            return None, "Sesión de estudiante inválida."
        p = ph()
        row = execute(conn, f"SELECT * FROM estudiantes WHERE id={p}", (int(eid),), fetch="one")
        if not row or int(row.get("colegio_id") or 0) != int(colegio_id):
            return None, "La institución no coincide con tu sesión. Cierra sesión e ingresa de nuevo."
        return row, None
    return _resolve_estudiante(conn, colegio_id, d)


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
    est, err = _resolve_estudiante_o_sesion(conn, colegio_id, d)
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


def _insert_bitacora(conn, colegio_id: int, rid: int, u: dict, prev_estado: str, nuevo: str, nota: str):
    p = ph()
    execute(
        conn,
        f"""INSERT INTO reportes_convivencia_bitacora (
            colegio_id, reporte_id, usuario_id, usuario_nombre, rol, estado_anterior, estado_nuevo, nota, creado_en
        ) VALUES ({p},{p},{p},{p},{p},{p},{p},{p},{p})""",
        (
            colegio_id,
            rid,
            u.get("id"),
            (u.get("nombre") or "")[:200],
            (u.get("rol") or "")[:80],
            (prev_estado or "")[:80],
            nuevo[:80],
            (nota or "")[:2000],
            _now_iso(),
        ),
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


@bp.route("/api/reportes-convivencia/patrones", methods=["GET"])
@login_required
@roles("Coordinador", "Orientador", "Superadmin")
def api_reportes_patrones():
    """Agregados por rango (fecha de recepción creado_en) para focos del canal ciudadano."""
    u = cu()
    tenant_id, terr = resolve_colegio_id(u)
    if terr:
        return jsonify({"error": terr}), 400
    desde = (request.args.get("desde") or "").strip()[:12]
    hasta = (request.args.get("hasta") or "").strip()[:12]
    if not desde or not hasta:
        hoy = date.today()
        hasta = hoy.isoformat()
        desde = (hoy - timedelta(days=30)).isoformat()
    if len(desde) < 10 or len(hasta) < 10 or desde > hasta:
        return jsonify({"error": "Rango inválido: use desde y hasta (YYYY-MM-DD)."}), 400

    conn = get_db()
    p = ph()
    rows = execute(
        conn,
        f"SELECT * FROM reportes_convivencia WHERE colegio_id={p} "
        f"AND substr(creado_en,1,10)>={p} AND substr(creado_en,1,10)<={p} "
        f"ORDER BY creado_en DESC LIMIT 5000",
        (tenant_id, desde[:10], hasta[:10]),
        fetch="all",
    ) or []
    conn.close()

    por_cat = Counter()
    por_lugar = Counter()
    por_quien = Counter()
    por_urg = Counter()
    por_est = Counter()
    por_curso = Counter()
    por_estudiante = Counter()
    nom_est = {}

    for r in rows:
        por_cat[(r.get("categoria_visual") or "").strip() or "—"] += 1
        por_lugar[(r.get("lugar_clave") or "").strip() or "—"] += 1
        por_quien[(r.get("a_quien") or "").strip() or "—"] += 1
        por_urg[(r.get("urgencia") or "").strip() or "—"] += 1
        por_est[(r.get("estado") or "").strip() or "—"] += 1
        c = (r.get("curso") or "").strip() or "—"
        por_curso[c] += 1
        try:
            eid = int(r.get("estudiante_id") or 0)
        except (TypeError, ValueError):
            eid = 0
        if eid:
            por_estudiante[eid] += 1
            nom_est[eid] = (r.get("estudiante_nombre") or "")[:120]

    top_cursos = sorted(por_curso.items(), key=lambda x: (-x[1], x[0]))[:12]
    top_est = sorted(por_estudiante.items(), key=lambda x: (-x[1], x[0]))[:12]
    top_est_out = [{"estudiante_id": eid, "nombre": nom_est.get(eid, "—"), "n": n} for eid, n in top_est]

    return jsonify(
        {
            "desde": desde[:10],
            "hasta": hasta[:10],
            "total": len(rows),
            "por_categoria": dict(por_cat),
            "por_lugar": dict(por_lugar),
            "por_a_quien": dict(por_quien),
            "por_urgencia": dict(por_urg),
            "por_estado": dict(por_est),
            "top_cursos": [{"curso": k, "n": v} for k, v in top_cursos],
            "top_estudiantes": top_est_out,
        }
    )


@bp.route("/api/reportes-convivencia/<int:rid>/bitacora", methods=["GET"])
@login_required
@roles("Coordinador", "Orientador", "Superadmin")
def api_reporte_bitacora(rid):
    u = cu()
    tenant_id, terr = resolve_colegio_id(u)
    if terr:
        return jsonify({"error": terr}), 400
    conn = get_db()
    p = ph()
    rep = execute(
        conn,
        f"SELECT id FROM reportes_convivencia WHERE id={p} AND colegio_id={p}",
        (rid, tenant_id),
        fetch="one",
    )
    if not rep:
        conn.close()
        return jsonify({"error": "No encontrado."}), 404
    bits = execute(
        conn,
        f"SELECT * FROM reportes_convivencia_bitacora WHERE reporte_id={p} AND colegio_id={p} ORDER BY id ASC",
        (rid, tenant_id),
        fetch="all",
    )
    conn.close()
    return jsonify(bits or [])


@bp.route("/api/reportes-convivencia/<int:rid>", methods=["PATCH"])
@login_required
@roles("Coordinador", "Orientador", "Superadmin")
def api_reporte_actualizar(rid):
    d = request.get_json(silent=True) or {}
    nuevo = (d.get("estado") or "").strip()
    if nuevo not in ESTADOS:
        return jsonify({"ok": False, "error": "Estado no válido."}), 400
    nota = (d.get("nota_comite") or "").strip()[:2000]

    u = cu()
    tenant_id, terr = resolve_colegio_id(u)
    if terr:
        return jsonify({"ok": False, "error": terr}), 400

    conn = get_db()
    p = ph()
    full = execute(
        conn,
        f"SELECT * FROM reportes_convivencia WHERE id={p} AND colegio_id={p}",
        (rid, tenant_id),
        fetch="one",
    )
    if not full:
        conn.close()
        return jsonify({"ok": False, "error": "No encontrado."}), 404

    prev_estado = (full.get("estado") or "").strip()
    if nuevo == prev_estado:
        conn.close()
        return jsonify({"ok": False, "error": "El reporte ya está en ese estado."}), 400
    if len(nota) < 10:
        conn.close()
        return jsonify(
            {
                "ok": False,
                "error": "Registre una nota de seguimiento (mínimo 10 caracteres) para documentar el cambio de estado.",
            }
        ), 400

    execute(
        conn,
        f"UPDATE reportes_convivencia SET estado={p}, nota_comite={p}, actualizado_en={p} WHERE id={p}",
        (nuevo, nota, _now_iso(), rid),
    )
    _insert_bitacora(conn, tenant_id, rid, u, prev_estado, nuevo, nota)
    commit(conn)
    conn.close()
    return jsonify({"ok": True})
