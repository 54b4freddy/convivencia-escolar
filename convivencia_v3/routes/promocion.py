"""Promoción: actividades institucionales (planeación, público objetivo, evidencias)."""
import os
import secrets
from datetime import datetime

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

