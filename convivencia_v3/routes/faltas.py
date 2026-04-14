"""Rutas HTTP: faltas disciplinarias y citas con acudientes."""
import os
import secrets
from datetime import datetime

from flask import Blueprint, jsonify, request, send_file
from werkzeug.utils import secure_filename

from ce_citas import CITA_ROLES_DESTINO, cancelar_citas_abiertas_por_falta, insert_cita_escuela
from ce_db import USE_PG, commit, execute, get_db, ph
from ce_faltas_service import attach_cita_falta, listar_faltas_enriquecidas, parse_filtros_faltas_args
from ce_gestion import enriquecer_falta_gestion
from routes.authz import cu, login_required, resolve_colegio_id, roles

bp = Blueprint("faltas_citas", __name__)

_PKG_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
UPLOAD_FALTAS = os.path.join(_PKG_ROOT, "static", "uploads", "faltas_actas")
_ALLOWED_ADJ = frozenset({".pdf", ".jpg", ".jpeg", ".png", ".webp", ".doc", ".docx"})
CAT_DESCARGOS = "descargos_inicial"
CAT_SESION = "sesion_instancias"
_VALID_CAT = frozenset({CAT_DESCARGOS, CAT_SESION})


def _puede_subir_adjunto_descargos(u, f):
    if int(f.get("colegio_id") or 0) != int(u.get("colegio_id") or 0):
        return False
    return u["rol"] == "Docente" and f.get("docente") == u["nombre"]


def _puede_subir_adjunto_sesion(u, f):
    if u["rol"] == "Superadmin":
        return True
    if int(f.get("colegio_id") or 0) != int(u.get("colegio_id") or 0):
        return False
    if u["rol"] == "Coordinador":
        return True
    if u["rol"] == "Director":
        return (u.get("curso") or "") == (f.get("curso") or "") or f.get("docente") == u.get("nombre")
    return False


def _puede_ver_adjuntos(u, f):
    if u["rol"] == "Superadmin":
        return True
    if int(f.get("colegio_id") or 0) != int(u.get("colegio_id") or 0):
        return False
    if u["rol"] == "Acudiente":
        return f.get("estudiante_id") == u.get("estudiante_id")
    if u["rol"] == "Docente":
        return f.get("docente") == u["nombre"]
    if u["rol"] == "Director":
        return f.get("curso") == u.get("curso") or f.get("docente") == u.get("nombre")
    return u["rol"] in ("Coordinador", "Orientador")


def _save_falta_adjunto_file(file_storage, colegio_id: int) -> tuple[str, str, str]:
    if not file_storage or not file_storage.filename:
        raise ValueError("Archivo requerido")
    os.makedirs(UPLOAD_FALTAS, exist_ok=True)
    orig = secure_filename(file_storage.filename) or "archivo"
    ext = os.path.splitext(orig)[1].lower()
    if ext not in _ALLOWED_ADJ:
        raise ValueError("Use PDF, imagen o Word (.pdf, .jpg, .jpeg, .png, .webp, .doc, .docx).")
    name = f"{colegio_id}_{secrets.token_hex(12)}{ext}"
    dest = os.path.join(UPLOAD_FALTAS, name)
    file_storage.save(dest)
    rel = os.path.join("faltas_actas", name).replace("\\", "/")
    mime = (file_storage.content_type or "").strip()
    return rel, orig, mime


def _lista_adjuntos(conn, fid):
    p = ph()
    rows = execute(
        conn,
        f"SELECT id, categoria, nombre_original, subido_por_nombre, subido_por_id, creado_en FROM falta_adjuntos "
        f"WHERE falta_id={p} ORDER BY id",
        (fid,),
        fetch="all",
    )
    return rows or []


@bp.route("/api/faltas")
@login_required
def api_faltas():
    u = cu()
    tenant_id, terr = resolve_colegio_id(u)
    if terr:
        return jsonify({"error": terr}), 400
    u_sc = {**u, "colegio_id": tenant_id}
    anio = request.args.get("anio", str(datetime.now().year))
    filt_sql = parse_filtros_faltas_args(request.args)
    estado_g = (request.args.get("estado_gestion") or "").strip()
    if estado_g not in ("pendiente", "en_revision", "cerrada"):
        estado_g = None
    conn = get_db()
    try:
        faltas = listar_faltas_enriquecidas(conn, u_sc, anio, filt_sql, estado_g)
        return jsonify(faltas)
    finally:
        conn.close()


@bp.route("/api/faltas/<int:fid>")
@login_required
def api_falta_detalle(fid):
    u = cu()
    tenant_id, terr = resolve_colegio_id(u)
    if terr:
        return jsonify({"error": terr}), 400
    conn = get_db()
    p = ph()
    f = execute(
        conn,
        f"SELECT f.*,e.acudiente,e.cedula_acudiente,e.telefono as tel_acudiente,e.discapacidad,e.documento_identidad "
        f"FROM faltas f LEFT JOIN estudiantes e ON e.id=f.estudiante_id WHERE f.id={p}",
        (fid,),
        fetch="one",
    )
    if not f:
        conn.close()
        return jsonify({"error": "No encontrada"}), 404
    if int(f.get("colegio_id") or 0) != int(tenant_id):
        conn.close()
        return jsonify({"error": "Sin permisos"}), 403
    if u["rol"] == "Acudiente" and f.get("estudiante_id") != u.get("estudiante_id"):
        conn.close()
        return jsonify({"error": "Sin permisos"}), 403
    f["anotaciones"] = execute(conn, f"SELECT * FROM anotaciones WHERE falta_id={p} ORDER BY id", (fid,), fetch="all")
    attach_cita_falta(conn, f)
    enriquecer_falta_gestion(f)
    f["adjuntos"] = _lista_adjuntos(conn, fid)
    conn.close()
    return jsonify(f)


@bp.route("/api/faltas/<int:fid>/gestion", methods=["PATCH"])
@roles("Coordinador", "Superadmin")
def api_falta_gestion(fid):
    d = request.json or {}
    if "decision" not in d:
        return jsonify({"ok": False, "error": "Indique decision: cerrada, en_revision o null (automático)"}), 400
    dec = d.get("decision")
    if dec in (None, "", "null", "automatico"):
        val = None
    elif dec in ("cerrada", "en_revision"):
        val = dec
    else:
        return jsonify({"ok": False, "error": "decision debe ser cerrada, en_revision o null"}), 400
    u = cu()
    tenant_id, terr = resolve_colegio_id(u)
    if terr:
        return jsonify({"ok": False, "error": terr}), 400
    conn = get_db()
    p = ph()
    f = execute(conn, f"SELECT * FROM faltas WHERE id={p}", (fid,), fetch="one")
    if not f:
        conn.close()
        return jsonify({"ok": False, "error": "No encontrada"}), 404
    if int(f.get("colegio_id") or 0) != int(tenant_id):
        conn.close()
        return jsonify({"ok": False, "error": "Sin permisos"}), 403
    execute(conn, f"UPDATE faltas SET gestion_coordinador={p} WHERE id={p}", (val, fid))
    commit(conn)
    conn.close()
    return jsonify({"ok": True})


@bp.route("/api/faltas", methods=["POST"])
@roles("Superadmin", "Coordinador", "Director", "Docente")
def api_falta_crear():
    d = request.json or {}
    u = cu()
    cid, terr = resolve_colegio_id(u)
    if terr:
        return jsonify({"ok": False, "error": terr}), 400
    conn = get_db()
    p = ph()
    try:
        anio = int(d.get("anio", datetime.now().year))
    except (TypeError, ValueError):
        anio = datetime.now().year
    est_id = d.get("estudiante_id")
    est_nom = (d.get("estudiante") or "").strip()
    if est_id:
        row = execute(
            conn,
            f"SELECT id,nombre FROM estudiantes WHERE id={p} AND colegio_id={p}",
            (int(est_id), cid),
            fetch="one",
        )
        if row:
            est_id = row["id"]
            est_nom = row.get("nombre") or est_nom
    if not est_nom:
        est = execute(
            conn,
            f"SELECT id,nombre FROM estudiantes WHERE nombre={p} AND colegio_id={p}",
            (d.get("estudiante", ""), cid),
            fetch="one",
        )
        if est:
            est_id = est["id"]
            est_nom = est["nombre"]
    if not est_nom:
        conn.close()
        return jsonify({"ok": False, "error": "Estudiante no válido"}), 400
    cat = execute(
        conn,
        f"SELECT protocolo,sancion FROM catalogo_faltas WHERE descripcion={p} AND colegio_id={p}",
        (d["falta_especifica"], cid),
        fetch="one",
    )
    execute(
        conn,
        f"INSERT INTO faltas (anio,fecha,curso,estudiante,estudiante_id,tipo_falta,falta_especifica,"
        f"descripcion,proceso_inicial,protocolo_aplicado,sancion_aplicada,docente,colegio_id) "
        f"VALUES ({p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p})",
        (
            anio,
            datetime.now().strftime("%Y-%m-%d"),
            d["curso"],
            est_nom,
            est_id,
            d["tipo_falta"],
            d["falta_especifica"],
            d["descripcion"],
            d["proceso_inicial"],
            cat.get("protocolo", "") if cat else "",
            cat.get("sancion", "") if cat else "",
            u["nombre"],
            cid,
        ),
    )
    if USE_PG:
        fid = execute(conn, "SELECT lastval() as lid", fetch="one")["lid"]
    else:
        fid = execute(conn, "SELECT last_insert_rowid() as lid", fetch="one")["lid"]
    cc = d.get("cita_acudiente") or {}
    if isinstance(cc, dict) and cc.get("activar"):
        fh = (cc.get("fecha_hora") or "").strip()
        if fh:
            try:
                cancelar_citas_abiertas_por_falta(conn, fid)
                insert_cita_escuela(conn, fid, cid, fh, u)
            except Exception:
                pass
    commit(conn)
    conn.close()
    return jsonify({"ok": True, "id": fid})


@bp.route("/api/faltas/<int:fid>/adjuntos", methods=["POST"])
@login_required
def api_falta_adjunto_subir(fid):
    u = cu()
    tenant_id, terr = resolve_colegio_id(u)
    if terr:
        return jsonify({"ok": False, "error": terr}), 400
    if u["rol"] == "Acudiente":
        return jsonify({"ok": False, "error": "Sin permisos"}), 403
    cat = (request.form.get("categoria") or "").strip()
    if cat not in _VALID_CAT:
        return jsonify({"ok": False, "error": "categoria debe ser descargos_inicial o sesion_instancias"}), 400
    fs = request.files.get("archivo")
    conn = get_db()
    p = ph()
    f = execute(conn, f"SELECT * FROM faltas WHERE id={p} AND colegio_id={p}", (fid, tenant_id), fetch="one")
    if not f:
        conn.close()
        return jsonify({"ok": False, "error": "No encontrada"}), 404
    if cat == CAT_DESCARGOS and not _puede_subir_adjunto_descargos(u, f):
        conn.close()
        return jsonify({"ok": False, "error": "Sin permisos"}), 403
    if cat == CAT_SESION and not _puede_subir_adjunto_sesion(u, f):
        conn.close()
        return jsonify({"ok": False, "error": "Sin permisos"}), 403
    try:
        rel, orig, mime = _save_falta_adjunto_file(fs, tenant_id)
    except ValueError as e:
        conn.close()
        return jsonify({"ok": False, "error": str(e)}), 400
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    execute(
        conn,
        f"INSERT INTO falta_adjuntos (falta_id,colegio_id,categoria,stored_path,nombre_original,mime,"
        f"subido_por_id,subido_por_nombre,creado_en) VALUES ({p},{p},{p},{p},{p},{p},{p},{p},{p})",
        (
            fid,
            tenant_id,
            cat,
            rel,
            orig[:240],
            (mime or "")[:120],
            u.get("id"),
            (u.get("nombre") or "")[:200],
            now,
        ),
    )
    commit(conn)
    adj = _lista_adjuntos(conn, fid)
    conn.close()
    return jsonify({"ok": True, "adjuntos": adj})


@bp.route("/api/faltas/<int:fid>/adjuntos/<int:aid>", methods=["DELETE"])
@login_required
def api_falta_adjunto_borrar(fid, aid):
    u = cu()
    tenant_id, terr = resolve_colegio_id(u)
    if terr:
        return jsonify({"ok": False, "error": terr}), 400
    conn = get_db()
    p = ph()
    row = execute(
        conn,
        f"SELECT * FROM falta_adjuntos WHERE id={p} AND falta_id={p} AND colegio_id={p}",
        (aid, fid, tenant_id),
        fetch="one",
    )
    if not row:
        conn.close()
        return jsonify({"ok": False, "error": "No encontrado"}), 404
    puede = u["rol"] in ("Superadmin", "Coordinador") or (
        row.get("subido_por_id") is not None and int(row.get("subido_por_id") or 0) == int(u.get("id") or 0)
    )
    if not puede:
        conn.close()
        return jsonify({"ok": False, "error": "Sin permisos"}), 403
    abs_path = os.path.join(_PKG_ROOT, "static", "uploads", row["stored_path"])
    execute(conn, f"DELETE FROM falta_adjuntos WHERE id={p}", (aid,))
    commit(conn)
    conn.close()
    try:
        if os.path.isfile(abs_path):
            os.remove(abs_path)
    except OSError:
        pass
    return jsonify({"ok": True})


@bp.route("/api/faltas/<int:fid>/adjuntos/<int:aid>")
@login_required
def api_falta_adjunto_archivo(fid, aid):
    u = cu()
    tenant_id, terr = resolve_colegio_id(u)
    if terr:
        return jsonify({"error": terr}), 400
    conn = get_db()
    p = ph()
    f = execute(conn, f"SELECT * FROM faltas WHERE id={p} AND colegio_id={p}", (fid, tenant_id), fetch="one")
    if not f:
        conn.close()
        return jsonify({"error": "No encontrada"}), 404
    if not _puede_ver_adjuntos(u, f):
        conn.close()
        return jsonify({"error": "Sin permisos"}), 403
    row = execute(
        conn,
        f"SELECT * FROM falta_adjuntos WHERE id={p} AND falta_id={p}",
        (aid, fid),
        fetch="one",
    )
    conn.close()
    if not row:
        return jsonify({"error": "No encontrado"}), 404
    abs_path = os.path.join(_PKG_ROOT, "static", "uploads", row["stored_path"])
    if not os.path.isfile(abs_path):
        return jsonify({"error": "Archivo no disponible"}), 404
    down_name = secure_filename(row.get("nombre_original") or "adjunto") or "adjunto"
    return send_file(abs_path, as_attachment=True, download_name=down_name)


@bp.route("/api/faltas/<int:fid>/anotaciones", methods=["POST"])
@roles("Superadmin", "Coordinador", "Director", "Orientador", "Docente")
def api_anotacion(fid):
    d = request.json or {}
    u = cu()
    tenant_id, terr = resolve_colegio_id(u)
    if terr:
        return jsonify({"error": terr}), 400
    txt = d.get("texto", "").strip()
    if not txt:
        return jsonify({"error": "Texto vacío"}), 400
    conn = get_db()
    p = ph()
    f = execute(conn, f"SELECT * FROM faltas WHERE id={p}", (fid,), fetch="one")
    if not f:
        conn.close()
        return jsonify({"error": "No encontrada"}), 404
    if int(f.get("colegio_id") or 0) != int(tenant_id):
        conn.close()
        return jsonify({"error": "Sin permisos"}), 403
    if u["rol"] == "Docente" and f.get("docente") != u["nombre"]:
        conn.close()
        return jsonify({"error": "Sin permisos"}), 403
    execute(
        conn,
        f"INSERT INTO anotaciones (falta_id,rol,autor,fecha,texto) VALUES ({p},{p},{p},{p},{p})",
        (fid, u["rol"], u["nombre"], datetime.now().strftime("%Y-%m-%d"), txt),
    )
    commit(conn)
    conn.close()
    return jsonify({"ok": True})


@bp.route("/api/me/citas-pendientes")
@login_required
def api_me_citas_pendientes():
    u = cu()
    cid, terr = resolve_colegio_id(u)
    if terr:
        return jsonify({"error": terr}), 400
    conn = get_db()
    p = ph()
    por_confirmar = []
    por_agendar = []
    if u["rol"] == "Acudiente":
        eid = u.get("estudiante_id")
        if eid:
            por_confirmar = (
                execute(
                    conn,
                    f"SELECT c.*, f.estudiante, f.falta_especifica, f.fecha as falta_fecha, f.curso "
                    f"FROM citas_acudiente c JOIN faltas f ON f.id=c.falta_id "
                    f"WHERE f.estudiante_id={p} AND f.colegio_id={p} AND c.estado='pendiente_confirmacion_acudiente'",
                    (eid, cid),
                    fetch="all",
                )
                or []
            )
    elif u["rol"] in CITA_ROLES_DESTINO:
        por_agendar = (
            execute(
                conn,
                f"SELECT c.*, f.estudiante, f.falta_especifica, f.fecha as falta_fecha, f.curso "
                f"FROM citas_acudiente c JOIN faltas f ON f.id=c.falta_id "
                f"WHERE c.colegio_id={p} AND c.estado='pendiente_agenda' AND c.rol_destino={p}",
                (cid, u["rol"]),
                fetch="all",
            )
            or []
        )
    conn.close()
    return jsonify({"por_confirmar": por_confirmar, "por_agendar": por_agendar})


@bp.route("/api/faltas/<int:fid>/cita/solicitud", methods=["POST"])
@roles("Acudiente")
def api_cita_solicitud(fid):
    d = request.json or {}
    rol_dest = (d.get("rol_destino") or "").strip()
    if rol_dest not in CITA_ROLES_DESTINO:
        return jsonify({"ok": False, "error": "Rol no válido"}), 400
    u = cu()
    eid = u.get("estudiante_id")
    if not eid:
        return jsonify({"ok": False, "error": "Sin estudiante asociado"}), 400
    cid, cerr = resolve_colegio_id(u)
    if cerr:
        return jsonify({"ok": False, "error": cerr}), 400
    conn = get_db()
    p = ph()
    f = execute(conn, f"SELECT * FROM faltas WHERE id={p} AND colegio_id={p}", (fid, cid), fetch="one")
    if not f or int(f.get("estudiante_id") or 0) != int(eid):
        conn.close()
        return jsonify({"ok": False, "error": "Falta no encontrada"}), 404
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    cancelar_citas_abiertas_por_falta(conn, fid)
    execute(
        conn,
        f"INSERT INTO citas_acudiente (falta_id,colegio_id,origen,estado,rol_destino,fecha_hora,"
        f"creado_por_id,creado_por_nombre,creado_por_rol,agenda_por_id,agenda_por_nombre,creado_en,actualizado_en) "
        f"VALUES ({p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p})",
        (
            fid,
            cid,
            "acudiente",
            "pendiente_agenda",
            rol_dest,
            "",
            u.get("id"),
            (u.get("nombre") or "")[:200],
            "Acudiente",
            None,
            "",
            now,
            now,
        ),
    )
    commit(conn)
    conn.close()
    return jsonify({"ok": True})


@bp.route("/api/citas/<int:cita_id>", methods=["PATCH"])
@login_required
def api_cita_patch(cita_id):
    d = request.json or {}
    u = cu()
    tenant_id, terr = resolve_colegio_id(u)
    if terr:
        return jsonify({"ok": False, "error": terr}), 400
    conn = get_db()
    p = ph()
    c = execute(conn, f"SELECT * FROM citas_acudiente WHERE id={p}", (cita_id,), fetch="one")
    if not c:
        conn.close()
        return jsonify({"ok": False, "error": "No encontrada"}), 404
    if int(c.get("colegio_id") or 0) != int(tenant_id):
        conn.close()
        return jsonify({"ok": False, "error": "Sin permisos"}), 403

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    estado = c.get("estado") or ""

    if u["rol"] == "Acudiente":
        frow = execute(conn, f"SELECT * FROM faltas WHERE id={p}", (c["falta_id"],), fetch="one")
        if not frow or int(frow.get("estudiante_id") or 0) != int(u.get("estudiante_id") or 0):
            conn.close()
            return jsonify({"ok": False, "error": "Sin permisos"}), 403
        acc = (d.get("accion") or "").strip().lower()
        if estado != "pendiente_confirmacion_acudiente":
            conn.close()
            return jsonify({"ok": False, "error": "Estado de cita no permite esta acción"}), 400
        if acc == "confirmar":
            execute(
                conn,
                f"UPDATE citas_acudiente SET estado='confirmada', actualizado_en={p} WHERE id={p}",
                (now, cita_id),
            )
        elif acc == "rechazar":
            execute(
                conn,
                f"UPDATE citas_acudiente SET estado='rechazada', actualizado_en={p} WHERE id={p}",
                (now, cita_id),
            )
        else:
            conn.close()
            return jsonify({"ok": False, "error": "Use accion: confirmar o rechazar"}), 400
        commit(conn)
        conn.close()
        return jsonify({"ok": True})

    if u["rol"] not in CITA_ROLES_DESTINO and u["rol"] != "Superadmin":
        conn.close()
        return jsonify({"ok": False, "error": "Sin permisos"}), 403

    if estado == "pendiente_agenda" and (u["rol"] == c.get("rol_destino") or u["rol"] == "Superadmin"):
        fh = (d.get("fecha_hora") or "").strip()
        if not fh:
            conn.close()
            return jsonify({"ok": False, "error": "Indique fecha_hora (formato fecha y hora local)"}), 400
        execute(
            conn,
            f"UPDATE citas_acudiente SET fecha_hora={p}, estado='pendiente_confirmacion_acudiente', "
            f"agenda_por_id={p}, agenda_por_nombre={p}, actualizado_en={p} WHERE id={p}",
            (fh, u.get("id"), (u.get("nombre") or "")[:200], now, cita_id),
        )
        commit(conn)
        conn.close()
        return jsonify({"ok": True})

    conn.close()
    return jsonify({"ok": False, "error": "No puede actualizar esta cita en su estado actual"}), 400
