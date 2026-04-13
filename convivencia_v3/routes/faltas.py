"""Rutas HTTP: faltas disciplinarias y citas con acudientes."""
from datetime import datetime

from flask import Blueprint, jsonify, request

from ce_citas import CITA_ROLES_DESTINO, cancelar_citas_abiertas_por_falta, insert_cita_escuela
from ce_db import USE_PG, commit, execute, get_db, ph
from ce_faltas_service import attach_cita_falta, listar_faltas_enriquecidas, parse_filtros_faltas_args
from ce_gestion import enriquecer_falta_gestion
from routes.authz import cu, login_required, roles

bp = Blueprint("faltas_citas", __name__)


@bp.route("/api/faltas")
@login_required
def api_faltas():
    u = cu()
    anio = request.args.get("anio", str(datetime.now().year))
    filt_sql = parse_filtros_faltas_args(request.args)
    estado_g = (request.args.get("estado_gestion") or "").strip()
    if estado_g not in ("pendiente", "en_revision", "cerrada"):
        estado_g = None
    conn = get_db()
    try:
        faltas = listar_faltas_enriquecidas(conn, u, anio, filt_sql, estado_g)
        return jsonify(faltas)
    finally:
        conn.close()


@bp.route("/api/faltas/<int:fid>")
@login_required
def api_falta_detalle(fid):
    u = cu()
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
    if u["rol"] == "Acudiente" and f.get("estudiante_id") != u.get("estudiante_id"):
        conn.close()
        return jsonify({"error": "Sin permisos"}), 403
    f["anotaciones"] = execute(conn, f"SELECT * FROM anotaciones WHERE falta_id={p} ORDER BY id", (fid,), fetch="all")
    attach_cita_falta(conn, f)
    enriquecer_falta_gestion(f)
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
    conn = get_db()
    p = ph()
    f = execute(conn, f"SELECT * FROM faltas WHERE id={p}", (fid,), fetch="one")
    if not f:
        conn.close()
        return jsonify({"ok": False, "error": "No encontrada"}), 404
    if u["rol"] != "Superadmin" and f.get("colegio_id") != (u.get("colegio_id") or 1):
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
    conn = get_db()
    p = ph()
    cid = u["colegio_id"] or 1
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


@bp.route("/api/faltas/<int:fid>/anotaciones", methods=["POST"])
@roles("Superadmin", "Coordinador", "Director", "Orientador", "Docente")
def api_anotacion(fid):
    d = request.json or {}
    u = cu()
    txt = d.get("texto", "").strip()
    if not txt:
        return jsonify({"error": "Texto vacío"}), 400
    conn = get_db()
    p = ph()
    f = execute(conn, f"SELECT * FROM faltas WHERE id={p}", (fid,), fetch="one")
    if not f:
        conn.close()
        return jsonify({"error": "No encontrada"}), 404
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
    cid = u.get("colegio_id") or 1
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
    conn = get_db()
    p = ph()
    cid = u.get("colegio_id") or 1
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


@bp.route("/api/citas/<int:cid>", methods=["PATCH"])
@login_required
def api_cita_patch(cid):
    d = request.json or {}
    u = cu()
    conn = get_db()
    p = ph()
    c = execute(conn, f"SELECT * FROM citas_acudiente WHERE id={p}", (cid,), fetch="one")
    if not c:
        conn.close()
        return jsonify({"ok": False, "error": "No encontrada"}), 404
    if c.get("colegio_id") != (u.get("colegio_id") or 1) and u["rol"] != "Superadmin":
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
            execute(conn, f"UPDATE citas_acudiente SET estado='confirmada', actualizado_en={p} WHERE id={p}", (now, cid))
        elif acc == "rechazar":
            execute(conn, f"UPDATE citas_acudiente SET estado='rechazada', actualizado_en={p} WHERE id={p}", (now, cid))
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
            (fh, u.get("id"), (u.get("nombre") or "")[:200], now, cid),
        )
        commit(conn)
        conn.close()
        return jsonify({"ok": True})

    conn.close()
    return jsonify({"ok": False, "error": "No puede actualizar esta cita en su estado actual"}), 400
