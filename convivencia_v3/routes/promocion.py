"""Promoción: actividades institucionales (planeación, público objetivo, evidencias)."""
import os
import secrets
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta

from flask import Blueprint, jsonify, request, send_file
from werkzeug.utils import secure_filename

from ce_db import USE_PG, commit, execute, get_db, ph
from routes.authz import cu, login_required, resolve_colegio_id, roles

bp = Blueprint("promocion", __name__)

_PKG_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
UPLOAD_PROMO = os.path.join(_PKG_ROOT, "static", "uploads", "promocion")
ALLOWED = frozenset({".pdf", ".jpg", ".jpeg", ".png", ".webp", ".doc", ".docx"})

TEMAS = frozenset(
    {
        "relaciones_respetuosas",
        "normas_convivencia",
        "gestion_emocional",
        "ambiente_fisico_seguro",
        "participacion_activa",
        "prevencion_conflictos",
    }
)
PUB_TIPOS = frozenset({"colegio", "curso", "estudiantes"})


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def _puede_ver(u):
    return u.get("rol") not in ("Acudiente", "Estudiante")

def _puede_editar(u):
    return u.get("rol") in ("Superadmin", "Coordinador", "Director", "Orientador", "Docente")


@bp.route("/api/promocion/actividades")
@login_required
def api_prom_listar():
    u = cu()
    if not _puede_ver(u):
        return jsonify({"error": "Sin permisos"}), 403
    cid, terr = resolve_colegio_id(u)
    if terr:
        return jsonify({"error": terr}), 400
    conn = get_db()
    p = ph()
    q = f"SELECT * FROM promocion_actividades WHERE colegio_id={p}"
    params = [cid]
    tema = (request.args.get("tema") or "").strip()
    if tema and tema in TEMAS:
        q += f" AND tema={p}"
        params.append(tema)
    pub = (request.args.get("publico_tipo") or "").strip()
    if pub and pub in PUB_TIPOS:
        q += f" AND publico_tipo={p}"
        params.append(pub)
    cur = (request.args.get("curso") or "").strip()
    if cur:
        q += f" AND (publico_curso={p} OR publico_json LIKE {p})"
        params.append(cur)
        params.append(f'%\"curso\":\"{cur}\"%')
    creado_por = (request.args.get("creado_por_id") or "").strip()
    if creado_por.isdigit():
        q += f" AND creado_por_id={p}"
        params.append(int(creado_por))
    fd = (request.args.get("desde") or "").strip()
    if fd:
        q += f" AND fecha>={p}"
        params.append(fd)
    fh = (request.args.get("hasta") or "").strip()
    if fh:
        q += f" AND fecha<={p}"
        params.append(fh)
    qtext = (request.args.get("q") or "").strip()
    if qtext:
        like = f"%{qtext}%"
        q += f" AND (titulo LIKE {p} OR lugar LIKE {p} OR descripcion LIKE {p})"
        params.extend([like, like, like])
    q += " ORDER BY fecha DESC, id DESC LIMIT 200"
    rows = execute(conn, q, params, fetch="all") or []
    conn.close()
    return jsonify(rows)

@bp.route("/api/promocion/actividades/<int:aid>")
@login_required
def api_prom_get(aid):
    u = cu()
    if not _puede_ver(u):
        return jsonify({"error": "Sin permisos"}), 403
    cid, terr = resolve_colegio_id(u)
    if terr:
        return jsonify({"error": terr}), 400
    conn = get_db()
    p = ph()
    row = execute(conn, f"SELECT * FROM promocion_actividades WHERE id={p} AND colegio_id={p}", (aid, cid), fetch="one")
    conn.close()
    if not row:
        return jsonify({"error": "No encontrada"}), 404
    return jsonify(row)


_REP_CAT_LBL = {
    "mal": "Alerta ciudadana — Me siento mal / necesito ayuda",
    "molestan": "Alerta ciudadana — Me molestan",
    "mal_colegio": "Alerta ciudadana — Algo malo en el colegio",
    "peligro": "Alerta ciudadana — Peligro en el entorno",
}
_CR_TIPO_LBL = {
    "conv_i": "Conducta de riesgo — Tipo I (convivencia)",
    "conv_ii": "Conducta de riesgo — Tipo II (riesgo moderado)",
    "conv_iii": "Conducta de riesgo — Tipo III (grave/delito)",
}
_MAP_REP_TEMA = {
    "mal": "gestion_emocional",
    "molestan": "prevencion_conflictos",
    "mal_colegio": "normas_convivencia",
    "peligro": "ambiente_fisico_seguro",
}
_MAP_CONV_TEMA = {
    "conv_i": "relaciones_respetuosas",
    "conv_ii": "prevencion_conflictos",
    "conv_iii": "ambiente_fisico_seguro",
}


@bp.route("/api/promocion/focos-calor", methods=["GET"])
@login_required
def api_prom_focos_calor():
    """Agregados últimos N días: alertas ciudadanas + conductas de riesgo, para mapa de calor en Promoción."""
    u = cu()
    if not _puede_ver(u):
        return jsonify({"error": "Sin permisos"}), 403
    cid, terr = resolve_colegio_id(u)
    if terr:
        return jsonify({"error": terr}), 400
    try:
        dias = int(request.args.get("dias", 30))
    except (TypeError, ValueError):
        dias = 30
    dias = min(max(dias, 7), 90)
    hoy = date.today()
    desde_d = hoy - timedelta(days=dias - 1)
    desde = desde_d.isoformat()
    hasta = hoy.isoformat()

    conn = get_db()
    p = ph()

    rep_rows = []
    if u["rol"] in ("Coordinador", "Orientador", "Superadmin"):
        rep_rows = execute(
            conn,
            f"SELECT categoria_visual, urgencia, curso FROM reportes_convivencia WHERE colegio_id={p} "
            f"AND substr(creado_en,1,10)>={p} AND substr(creado_en,1,10)<={p}",
            (cid, desde, hasta),
            fetch="all",
        ) or []

    qsen = (
        f"SELECT tipo_conducta, urgencia, curso FROM senales_atencion WHERE colegio_id={p} "
        f"AND categoria={p} AND fecha_registro>={p} AND fecha_registro<={p}"
    )
    prm = [cid, "conducta_riesgo", desde, hasta]
    if u["rol"] == "Docente":
        qsen += f" AND registrado_por_id={p}"
        prm.append(u["id"])
    elif u["rol"] == "Director" and u.get("curso"):
        qsen += f" AND curso={p}"
        prm.append(u["curso"])
    sen_rows = execute(conn, qsen, prm, fetch="all") or []
    conn.close()

    # key -> {"u": int, "r": int, "cursos": Counter}
    agg = defaultdict(lambda: {"u": 0, "r": 0, "cursos": Counter()})

    for row in rep_rows:
        cat = (row.get("categoria_visual") or "").strip()
        if cat not in _MAP_REP_TEMA:
            continue
        key = ("ac", cat)
        urg = (row.get("urgencia") or "").strip() == "urgente"
        agg[key]["u" if urg else "r"] += 1
        c = (row.get("curso") or "").strip() or "—"
        agg[key]["cursos"][c] += 1

    for row in sen_rows:
        tipo = (row.get("tipo_conducta") or "").strip()
        if tipo not in _MAP_CONV_TEMA:
            continue
        key = ("cr", tipo)
        urg_s = (row.get("urgencia") or "").strip().lower()
        urg = urg_s in ("critica", "alta")
        agg[key]["u" if urg else "r"] += 1
        c = (row.get("curso") or "").strip() or "—"
        agg[key]["cursos"][c] += 1

    filas = []
    for (kind, code), v in agg.items():
        nu, nr = int(v["u"]), int(v["r"])
        tot = nu + nr
        if tot <= 0:
            continue
        if kind == "ac":
            label = _REP_CAT_LBL.get(code, code)
            tema = _MAP_REP_TEMA.get(code, "gestion_emocional")
            tid = f"ac:{code}"
            tit = f"Promoción — foco alertas: {label.split(' — ', 1)[-1] if ' — ' in label else label} ({dias} días)"
        else:
            label = _CR_TIPO_LBL.get(code, code)
            tema = _MAP_CONV_TEMA.get(code, "prevencion_conflictos")
            tid = f"cr:{code}"
            tit = f"Promoción — foco conductas: {label.split(' — ', 1)[-1] if ' — ' in label else label} ({dias} días)"
        top_c = v["cursos"].most_common(1)
        curso_sug = (top_c[0][0] if top_c and top_c[0][0] != "—" else "") or ""
        desc = (
            f"Planeación sugerida a partir del mapa de calor ({desde} a {hasta}). "
            f"Registros en ventana: {tot} (urgentes/alta: {nu}, resto: {nr}). "
            f"Revise convivencia y ajuste público objetivo según el colegio."
        )
        filas.append(
            {
                "id": tid,
                "label": label,
                "tema_promocion": tema,
                "titulo_sugerido": tit[:120],
                "descripcion_bosquejo": desc,
                "urgente": nu,
                "no_urgente": nr,
                "total": tot,
                "curso_sugerido": curso_sug[:80],
            }
        )

    filas.sort(key=lambda x: (-x["total"], x["label"]))
    max_u = max((x["urgente"] for x in filas), default=0)
    max_r = max((x["no_urgente"] for x in filas), default=0)
    max_t = max((x["total"] for x in filas), default=0)

    return jsonify(
        {
            "desde": desde,
            "hasta": hasta,
            "dias": dias,
            "filas": filas,
            "max_urgente": max_u,
            "max_no_urgente": max_r,
            "max_total": max_t,
        }
    )


def _save_evid(file_storage, colegio_id: int) -> str:
    if not file_storage or not file_storage.filename:
        return ""
    os.makedirs(UPLOAD_PROMO, exist_ok=True)
    orig = secure_filename(file_storage.filename) or "archivo"
    ext = os.path.splitext(orig)[1].lower()
    if ext not in ALLOWED:
        raise ValueError("Use PDF, imagen o Word (.pdf, .jpg, .jpeg, .png, .webp, .doc, .docx).")
    name = f"{colegio_id}_{secrets.token_hex(10)}{ext}"
    dest = os.path.join(UPLOAD_PROMO, name)
    file_storage.save(dest)
    return os.path.join("promocion", name).replace("\\", "/")

def _insert_evid(conn, actividad_id: int, colegio_id: int, rel: str, orig: str, mime: str, u: dict):
    p = ph()
    execute(
        conn,
        f"""INSERT INTO promocion_evidencias
        (actividad_id,colegio_id,stored_path,nombre_original,mime,subido_por_id,subido_por_nombre,creado_en)
        VALUES ({p},{p},{p},{p},{p},{p},{p},{p})""",
        (
            actividad_id,
            colegio_id,
            rel,
            orig[:220],
            (mime or "")[:120],
            u.get("id"),
            (u.get("nombre") or "")[:120],
            _now(),
        ),
    )


@bp.route("/api/promocion/actividades", methods=["POST"])
@roles("Superadmin", "Coordinador", "Director", "Orientador", "Docente")
def api_prom_crear():
    u = cu()
    cid, terr = resolve_colegio_id(u)
    if terr:
        return jsonify({"ok": False, "error": terr}), 400
    d = request.form.to_dict() if request.form else {}
    evid = request.files.get("evidencia")
    titulo = (d.get("titulo") or "").strip()[:120]
    tema = (d.get("tema") or "").strip()
    fecha = (d.get("fecha") or "").strip()[:10]
    lugar = (d.get("lugar") or "").strip()[:120]
    recursos = (d.get("recursos") or "").strip()[:240]
    descripcion = (d.get("descripcion") or "").strip()[:2000]
    pub = (d.get("publico_tipo") or "").strip()
    pub_curso = (d.get("publico_curso") or "").strip()[:80]
    pub_json = (d.get("publico_json") or "").strip()[:4000]
    if len(titulo) < 4:
        return jsonify({"ok": False, "error": "Título obligatorio (mín. 4 caracteres)."}), 400
    if tema not in TEMAS:
        return jsonify({"ok": False, "error": "Tema no válido."}), 400
    if not fecha:
        return jsonify({"ok": False, "error": "Fecha obligatoria."}), 400
    if pub not in PUB_TIPOS:
        return jsonify({"ok": False, "error": "Público objetivo no válido."}), 400
    if pub == "curso" and not pub_curso:
        return jsonify({"ok": False, "error": "Seleccione curso."}), 400
    if pub == "estudiantes" and len(pub_json) < 5:
        return jsonify({"ok": False, "error": "Seleccione estudiantes."}), 400
    try:
        ev_path = _save_evid(evid, int(cid))
        ev_orig = secure_filename(evid.filename) if evid and evid.filename else ""
        ev_mime = (evid.content_type or "").strip() if evid and evid.filename else ""
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400

    conn = get_db()
    p = ph()
    creado = _now()
    execute(
        conn,
        f"""INSERT INTO promocion_actividades
        (colegio_id,titulo,tema,fecha,lugar,recursos,descripcion,publico_tipo,publico_curso,publico_json,evidencia_path,creado_por_id,creado_por_nombre,creado_por_rol,creado_en)
        VALUES ({p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p})""",
        (
            cid,
            titulo,
            tema,
            fecha,
            lugar,
            recursos,
            descripcion,
            pub,
            pub_curso,
            pub_json,
            ev_path,
            u.get("id"),
            u.get("nombre", "")[:120],
            u.get("rol", "")[:40],
            creado,
        ),
    )
    if USE_PG:
        aid = int(execute(conn, "SELECT lastval() as lid", fetch="one")["lid"])
    else:
        aid = int(execute(conn, "SELECT last_insert_rowid() as lid", fetch="one")["lid"])
    if ev_path:
        _insert_evid(conn, aid, int(cid), ev_path, ev_orig or "", ev_mime or "", u)
    commit(conn)
    conn.close()
    return jsonify({"ok": True, "id": aid})

@bp.route("/api/promocion/actividades/<int:aid>", methods=["PATCH"])
@login_required
def api_prom_patch(aid):
    u = cu()
    if not _puede_editar(u):
        return jsonify({"ok": False, "error": "Sin permisos"}), 403
    cid, terr = resolve_colegio_id(u)
    if terr:
        return jsonify({"ok": False, "error": terr}), 400
    d = request.get_json(silent=True) or {}
    titulo = (d.get("titulo") or "").strip()[:120]
    tema = (d.get("tema") or "").strip()
    fecha = (d.get("fecha") or "").strip()[:10]
    lugar = (d.get("lugar") or "").strip()[:120]
    recursos = (d.get("recursos") or "").strip()[:240]
    descripcion = (d.get("descripcion") or "").strip()[:2000]
    pub = (d.get("publico_tipo") or "").strip()
    pub_curso = (d.get("publico_curso") or "").strip()[:80]
    pub_json = (d.get("publico_json") or "").strip()[:4000]
    if len(titulo) < 4:
        return jsonify({"ok": False, "error": "Título obligatorio (mín. 4 caracteres)."}), 400
    if tema not in TEMAS:
        return jsonify({"ok": False, "error": "Tema no válido."}), 400
    if not fecha:
        return jsonify({"ok": False, "error": "Fecha obligatoria."}), 400
    if pub not in PUB_TIPOS:
        return jsonify({"ok": False, "error": "Público objetivo no válido."}), 400
    if pub == "curso" and not pub_curso:
        return jsonify({"ok": False, "error": "Seleccione curso."}), 400
    if pub == "estudiantes" and len(pub_json) < 5:
        return jsonify({"ok": False, "error": "Seleccione estudiantes."}), 400

    conn = get_db()
    p = ph()
    ex = execute(conn, f"SELECT id FROM promocion_actividades WHERE id={p} AND colegio_id={p}", (aid, cid), fetch="one")
    if not ex:
        conn.close()
        return jsonify({"ok": False, "error": "No encontrada"}), 404
    execute(
        conn,
        f"""UPDATE promocion_actividades
        SET titulo={p},tema={p},fecha={p},lugar={p},recursos={p},descripcion={p},publico_tipo={p},publico_curso={p},publico_json={p}
        WHERE id={p} AND colegio_id={p}""",
        (titulo, tema, fecha, lugar, recursos, descripcion, pub, pub_curso, pub_json, aid, cid),
    )
    commit(conn)
    conn.close()
    return jsonify({"ok": True})

@bp.route("/api/promocion/actividades/<int:aid>", methods=["DELETE"])
@login_required
def api_prom_delete(aid):
    u = cu()
    if u.get("rol") not in ("Superadmin", "Coordinador"):
        return jsonify({"ok": False, "error": "Sin permisos"}), 403
    cid, terr = resolve_colegio_id(u)
    if terr:
        return jsonify({"ok": False, "error": terr}), 400
    conn = get_db()
    p = ph()
    ex = execute(conn, f"SELECT id FROM promocion_actividades WHERE id={p} AND colegio_id={p}", (aid, cid), fetch="one")
    if not ex:
        conn.close()
        return jsonify({"ok": False, "error": "No encontrada"}), 404
    execute(conn, f"DELETE FROM promocion_actividades WHERE id={p} AND colegio_id={p}", (aid, cid))
    commit(conn)
    conn.close()
    return jsonify({"ok": True})

@bp.route("/api/promocion/actividades/<int:aid>/evidencias")
@login_required
def api_prom_evid_list(aid):
    u = cu()
    if not _puede_ver(u):
        return jsonify({"error": "Sin permisos"}), 403
    cid, terr = resolve_colegio_id(u)
    if terr:
        return jsonify({"error": terr}), 400
    conn = get_db()
    p = ph()
    ex = execute(conn, f"SELECT id FROM promocion_actividades WHERE id={p} AND colegio_id={p}", (aid, cid), fetch="one")
    if not ex:
        conn.close()
        return jsonify({"error": "No encontrada"}), 404
    rows = execute(
        conn,
        f"SELECT id,nombre_original,mime,subido_por_nombre,creado_en FROM promocion_evidencias WHERE actividad_id={p} ORDER BY id DESC",
        (aid,),
        fetch="all",
    ) or []
    conn.close()
    return jsonify(rows)

@bp.route("/api/promocion/actividades/<int:aid>/evidencias", methods=["POST"])
@login_required
def api_prom_evid_add(aid):
    u = cu()
    if not _puede_editar(u):
        return jsonify({"ok": False, "error": "Sin permisos"}), 403
    cid, terr = resolve_colegio_id(u)
    if terr:
        return jsonify({"ok": False, "error": terr}), 400
    f = request.files.get("evidencia")
    if not f or not f.filename:
        return jsonify({"ok": False, "error": "Archivo requerido"}), 400
    conn = get_db()
    p = ph()
    ex = execute(conn, f"SELECT id FROM promocion_actividades WHERE id={p} AND colegio_id={p}", (aid, cid), fetch="one")
    if not ex:
        conn.close()
        return jsonify({"ok": False, "error": "No encontrada"}), 404
    try:
        rel = _save_evid(f, int(cid))
    except ValueError as e:
        conn.close()
        return jsonify({"ok": False, "error": str(e)}), 400
    _insert_evid(conn, aid, int(cid), rel, secure_filename(f.filename) or "", (f.content_type or "").strip(), u)
    if request.form.get("set_como_principal") in ("1", "true", "yes", "on"):
        execute(conn, f"UPDATE promocion_actividades SET evidencia_path={p} WHERE id={p} AND colegio_id={p}", (rel, aid, cid))
    commit(conn)
    conn.close()
    return jsonify({"ok": True})

@bp.route("/api/promocion/evidencias/<int:eid>/file")
@login_required
def api_prom_evid_file(eid):
    u = cu()
    if not _puede_ver(u):
        return jsonify({"error": "Sin permisos"}), 403
    cid, terr = resolve_colegio_id(u)
    if terr:
        return jsonify({"error": terr}), 400
    conn = get_db()
    p = ph()
    row = execute(
        conn,
        f"SELECT stored_path, colegio_id FROM promocion_evidencias WHERE id={p}",
        (eid,),
        fetch="one",
    )
    conn.close()
    if not row or int(row.get("colegio_id") or 0) != int(cid):
        return jsonify({"error": "No encontrada"}), 404
    rel = (row.get("stored_path") or "").strip()
    abs_path = os.path.join(_PKG_ROOT, "static", "uploads", rel)
    if not rel or not os.path.exists(abs_path):
        return jsonify({"error": "Archivo no encontrado"}), 404
    return send_file(abs_path, as_attachment=False)

@bp.route("/api/promocion/evidencias/<int:eid>", methods=["DELETE"])
@login_required
def api_prom_evid_delete(eid):
    u = cu()
    if u.get("rol") not in ("Superadmin", "Coordinador", "Director", "Orientador", "Docente"):
        return jsonify({"ok": False, "error": "Sin permisos"}), 403
    cid, terr = resolve_colegio_id(u)
    if terr:
        return jsonify({"ok": False, "error": terr}), 400
    conn = get_db()
    p = ph()
    row = execute(
        conn,
        f"SELECT id, stored_path, colegio_id FROM promocion_evidencias WHERE id={p}",
        (eid,),
        fetch="one",
    )
    if not row or int(row.get("colegio_id") or 0) != int(cid):
        conn.close()
        return jsonify({"ok": False, "error": "No encontrada"}), 404
    execute(conn, f"DELETE FROM promocion_evidencias WHERE id={p}", (eid,))
    commit(conn)
    conn.close()
    return jsonify({"ok": True})

@bp.route("/api/promocion/actividades/<int:aid>/evidencia")
@login_required
def api_prom_evidencia(aid):
    u = cu()
    if not _puede_ver(u):
        return jsonify({"error": "Sin permisos"}), 403
    cid, terr = resolve_colegio_id(u)
    if terr:
        return jsonify({"error": terr}), 400
    # Compatibilidad: primera evidencia/archivo principal
    conn = get_db()
    p = ph()
    row = execute(conn, f"SELECT evidencia_path, colegio_id FROM promocion_actividades WHERE id={p}", (aid,), fetch="one")
    conn.close()
    if not row or int(row.get("colegio_id") or 0) != int(cid):
        return jsonify({"error": "No encontrada"}), 404
    rel = (row.get("evidencia_path") or "").strip()
    if not rel:
        return jsonify({"error": "Sin evidencia"}), 404
    abs_path = os.path.join(_PKG_ROOT, "static", "uploads", rel)
    if not os.path.exists(abs_path):
        return jsonify({"error": "Archivo no encontrado"}), 404
    return send_file(abs_path, as_attachment=False)

