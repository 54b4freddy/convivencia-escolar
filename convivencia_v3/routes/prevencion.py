"""Panel de prevención: rankings de reiteración (faltas/asistencia)."""

import json
import re
from collections import Counter, defaultdict

from flask import Blueprint, jsonify, request

from ce_db import execute, get_db, ph
from routes.authz import cu, login_required, resolve_colegio_id

bp = Blueprint("prevencion", __name__)

_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _parse_iso(s: str) -> str:
    s = (s or "").strip()
    return s if _ISO.match(s) else ""


def _norm_vic_key(s: str) -> str:
    return " ".join(str(s or "").strip().lower().split())


def _afectados_list(aj):
    """Nombres en afectados_json (lista JSON). Tolera string doble-codificado, dicts y lista separada por comas."""
    if aj is None:
        return []
    if isinstance(aj, (bytes, bytearray)):
        try:
            aj = aj.decode("utf-8", errors="replace")
        except Exception:
            return []
    if isinstance(aj, list):
        raw_items = aj
    else:
        s = str(aj).strip()
        if not s:
            return []
        parsed = None
        try:
            parsed = json.loads(s)
        except Exception:
            if "," in s and "[" not in s and "{" not in s:
                return [p.strip()[:60] for p in s.split(",") if p.strip()][:20]
            return []
        if isinstance(parsed, str):
            try:
                parsed = json.loads(parsed.strip())
            except Exception:
                t = parsed.strip()
                return [t[:60]] if t else []
        if not isinstance(parsed, list):
            return []
        raw_items = parsed
    out = []
    for x in raw_items[:20]:
        if x is None:
            continue
        if isinstance(x, dict):
            t = str(x.get("nombre") or x.get("name") or x.get("victima") or x.get("n") or "").strip()
        else:
            t = str(x).strip()
        if t:
            out.append(t[:60])
    return out


def _reiteracion_payload(conn, tenant_id: int, desde: str, hasta: str, curso_scope: str = "") -> dict:
    """Rankings de reiteración/focos para un colegio y rango (misma lógica que /api/prevencion/reiteracion)."""
    p = ph()
    qf = (
        f"SELECT id,fecha,curso,estudiante_id,estudiante,tipo_falta,lugar,afectados_json "
        f"FROM faltas WHERE colegio_id={p} AND fecha>={p} AND fecha<={p}"
    )
    prm = [tenant_id, desde, hasta]
    if curso_scope:
        qf += f" AND curso={p}"
        prm.append(curso_scope)
    qf += " ORDER BY fecha DESC LIMIT 5000"
    faltas = execute(conn, qf, prm, fetch="all") or []

    tipoI = Counter()
    est_info = {}
    lugares = Counter()
    victimas = Counter()
    victima_etiqueta = {}

    for f in faltas:
        eid = f.get("estudiante_id")
        if eid is not None:
            try:
                eid = int(eid)
            except Exception:
                eid = None
        if eid is not None:
            est_info.setdefault(
                eid,
                {"estudiante": f.get("estudiante") or "—", "curso": f.get("curso") or "—"},
            )
        if (f.get("tipo_falta") or "") == "Tipo I" and eid is not None:
            tipoI[eid] += 1
        lug = (f.get("lugar") or "").strip()
        if lug:
            lugares[lug] += 1
        for nom in _afectados_list(f.get("afectados_json") or ""):
            vk = _norm_vic_key(nom)
            if not vk:
                continue
            victimas[vk] += 1
            victima_etiqueta.setdefault(vk, nom.strip()[:60])

    qa = (
        f"SELECT d.estudiante_id, COUNT(*) as n "
        f"FROM asistencia_detalle d "
        f"JOIN asistencia_toma t ON t.id=d.toma_id "
        f"WHERE t.colegio_id={p} AND t.fecha>={p} AND t.fecha<={p} AND d.ausente=1"
    )
    prm2 = [tenant_id, desde, hasta]
    if curso_scope:
        qa += f" AND t.curso={p}"
        prm2.append(curso_scope)
    qa += " GROUP BY d.estudiante_id"
    aus_rows = execute(conn, qa, prm2, fetch="all") or []

    aus = Counter()
    for r in aus_rows:
        try:
            eid = int(r.get("estudiante_id"))
        except Exception:
            continue
        try:
            n = int(r.get("n") or 0)
        except Exception:
            n = 0
        if eid is not None:
            aus[eid] += n

    missing_ids = [eid for eid in set(list(aus.keys()) + list(tipoI.keys())) if eid not in est_info]
    if missing_ids:
        missing_ids = missing_ids[:500]
        phs = ",".join([p] * len(missing_ids))
        q = f"SELECT id,nombre,curso FROM estudiantes WHERE colegio_id={p} AND id IN ({phs})"
        rows = execute(conn, q, [tenant_id] + missing_ids, fetch="all") or []
        for e in rows:
            try:
                eid = int(e.get("id"))
            except Exception:
                continue
            est_info[eid] = {"estudiante": e.get("nombre") or "—", "curso": e.get("curso") or "—"}

    top_aus = []
    for eid, n in aus.most_common(50):
        if n < 3:
            continue
        info = est_info.get(eid) or {"estudiante": "—", "curso": "—"}
        top_aus.append({"estudiante_id": eid, **info, "ausencias": n})

    top_tipoI = []
    for eid, n in tipoI.most_common(50):
        if n < 3:
            continue
        info = est_info.get(eid) or {"estudiante": "—", "curso": "—"}
        top_tipoI.append({"estudiante_id": eid, **info, "tipoI": n})

    top_lug = [{"lugar": k, "faltas": n} for k, n in lugares.most_common(50) if n >= 3]
    top_vic = [
        {"victima": victima_etiqueta.get(k, k), "menciones": n} for k, n in victimas.most_common(50) if n >= 1
    ]

    return {
        "scope": {"curso": curso_scope} if curso_scope else {"curso": None},
        "rank_ausencias": top_aus,
        "rank_tipoI": top_tipoI,
        "rank_lugares": top_lug,
        "rank_victimas": top_vic,
    }


@bp.route("/api/prevencion/reiteracion")
@login_required
def api_prevencion_reiteracion():
    """
    Retorna rankings por rango de fechas (panel Conductas de riesgo → Reiteración y focos):
      - ausencias (>=3) por estudiante
      - Tipo I (>=3) por estudiante
      - lugares (>=3) por lugar
      - víctimas (>=1) por nombre (afectados_json)
    Director ve solo su curso; coordinación/orientación ven todo el colegio.
    """
    u = cu()
    if u["rol"] not in ("Superadmin", "Coordinador", "Orientador", "Director"):
        return jsonify({"error": "Sin permisos"}), 403

    tenant_id, terr = resolve_colegio_id(u)
    if terr:
        return jsonify({"error": terr}), 400

    desde = _parse_iso(request.args.get("desde", ""))
    hasta = _parse_iso(request.args.get("hasta", ""))
    if not desde or not hasta:
        return jsonify({"error": "Parámetros requeridos: desde y hasta (YYYY-MM-DD)"}), 400
    if desde > hasta:
        return jsonify({"error": "Rango inválido: desde > hasta"}), 400

    curso_scope = ""
    if u["rol"] == "Director" and u.get("curso"):
        curso_scope = u["curso"]

    conn = get_db()
    try:
        payload = _reiteracion_payload(conn, int(tenant_id), desde, hasta, curso_scope)
    finally:
        conn.close()

    return jsonify({"desde": desde, "hasta": hasta, **payload})


@bp.route("/api/prevencion/reiteracion-mt")
@login_required
def api_prevencion_reiteracion_multitenant():
    """Superadmin: mismos rankings que reiteración/focos, por cada institución en una sola respuesta."""
    u = cu()
    if u.get("rol") != "Superadmin":
        return jsonify({"error": "Solo Superadmin"}), 403

    desde = _parse_iso(request.args.get("desde", ""))
    hasta = _parse_iso(request.args.get("hasta", ""))
    if not desde or not hasta:
        return jsonify({"error": "Parámetros requeridos: desde y hasta (YYYY-MM-DD)"}), 400
    if desde > hasta:
        return jsonify({"error": "Rango inválido: desde > hasta"}), 400

    conn = get_db()
    try:
        cols = execute(conn, "SELECT id, nombre FROM colegios ORDER BY nombre, id", fetch="all") or []
        instituciones = []
        for c in cols:
            cid = int(c["id"])
            block = _reiteracion_payload(conn, cid, desde, hasta, "")
            instituciones.append(
                {
                    "colegio_id": cid,
                    "nombre": (c.get("nombre") or "").strip() or f"Institución {cid}",
                    **block,
                }
            )
    finally:
        conn.close()

    return jsonify({"desde": desde, "hasta": hasta, "instituciones": instituciones})


@bp.route("/api/prevencion/reiteracion/detalle")
@login_required
def api_prevencion_reiteracion_detalle():
    """
    Devuelve lista de faltas asociadas al ítem seleccionado en el panel de prevención.
    Parámetros:
      - desde, hasta (YYYY-MM-DD)
      - kind: 'estudiante' | 'lugar' | 'victima'
      - estudiante_id | lugar | victima
      - colegio_id (opcional, Superadmin sin institución en sesión)
    """
    u = cu()
    if u["rol"] not in ("Superadmin", "Coordinador", "Orientador", "Director"):
        return jsonify({"error": "Sin permisos"}), 403

    tenant_id, terr = resolve_colegio_id(u)
    if u.get("rol") == "Superadmin" and terr:
        raw_c = request.args.get("colegio_id")
        try:
            oc = int(raw_c) if raw_c is not None else 0
        except (TypeError, ValueError):
            oc = 0
        if oc > 0:
            tenant_id, terr = oc, None
    if terr:
        return jsonify({"error": terr}), 400

    desde = _parse_iso(request.args.get("desde", ""))
    hasta = _parse_iso(request.args.get("hasta", ""))
    if not desde or not hasta:
        return jsonify({"error": "Parámetros requeridos: desde y hasta (YYYY-MM-DD)"}), 400
    if desde > hasta:
        return jsonify({"error": "Rango inválido: desde > hasta"}), 400

    kind = (request.args.get("kind") or "").strip()
    if kind not in ("estudiante", "lugar", "victima"):
        return jsonify({"error": "kind debe ser estudiante, lugar o victima"}), 400

    curso_scope = ""
    if u["rol"] == "Director" and u.get("curso"):
        curso_scope = u["curso"]

    conn = get_db()
    p = ph()
    try:
        q = (
            f"SELECT id,fecha,curso,estudiante_id,estudiante,tipo_falta,falta_especifica,lugar "
            f"FROM faltas WHERE colegio_id={p} AND fecha>={p} AND fecha<={p}"
        )
        prm = [tenant_id, desde, hasta]
        if curso_scope:
            q += f" AND curso={p}"
            prm.append(curso_scope)
        if kind == "estudiante":
            try:
                eid = int(request.args.get("estudiante_id") or 0)
            except (TypeError, ValueError):
                eid = 0
            if not eid:
                return jsonify({"error": "estudiante_id requerido"}), 400
            q += f" AND estudiante_id={p}"
            prm.append(eid)
        elif kind == "lugar":
            lug = (request.args.get("lugar") or "").strip()
            if not lug:
                return jsonify({"error": "lugar requerido"}), 400
            q += f" AND lugar={p}"
            prm.append(lug[:80])
        else:  # victima
            vic = (request.args.get("victima") or "").strip()
            if not vic:
                return jsonify({"error": "victima requerido"}), 400
            # match conservador: buscar el string dentro del JSON
            q += f" AND afectados_json LIKE {p}"
            prm.append(f'%{vic.replace("%", "").replace("_", "")}%')
        q += " ORDER BY fecha DESC, id DESC LIMIT 200"
        rows = execute(conn, q, prm, fetch="all") or []
    finally:
        conn.close()
    return jsonify({"desde": desde, "hasta": hasta, "kind": kind, "items": rows})

