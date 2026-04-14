"""Tomas de asistencia y asignatura del docente en perfil."""
from datetime import datetime

from flask import Blueprint, jsonify, request, session

from ce_db import USE_PG, commit, execute, get_db, ph
from routes.authz import cu, login_required, resolve_colegio_id, roles

bp = Blueprint("asistencia", __name__)


@bp.route("/api/asistencia/tomas")
@login_required
def api_asistencia_tomas():
    u = cu()
    if u["rol"] == "Acudiente":
        return jsonify({"error": "Sin permisos"}), 403
    cid, terr = resolve_colegio_id(u)
    if terr:
        return jsonify({"error": terr}), 400
    conn = get_db()
    p = ph()
    q = f"SELECT t.* FROM asistencia_toma t WHERE t.colegio_id={p}"
    prm = [cid]
    if u["rol"] == "Director" and u.get("curso"):
        q += f" AND t.curso={p}"
        prm.append(u["curso"])
    if u["rol"] == "Docente":
        q += f" AND t.docente_id={p}"
        prm.append(u["id"])
    cur = request.args.get("curso", "")
    if cur:
        q += f" AND t.curso={p}"
        prm.append(cur)
    fd = request.args.get("desde", "")
    if fd:
        q += f" AND t.fecha>={p}"
        prm.append(fd)
    fh = request.args.get("hasta", "")
    if fh:
        q += f" AND t.fecha<={p}"
        prm.append(fh)
    q += " ORDER BY t.fecha DESC, t.id DESC LIMIT 100"
    tomas = execute(conn, q, prm, fetch="all")
    for t in tomas:
        t["detalles"] = execute(
            conn,
            f"SELECT * FROM asistencia_detalle WHERE toma_id={p} ORDER BY estudiante_nombre",
            (t["id"],),
            fetch="all",
        )
    conn.close()
    return jsonify(tomas)


@bp.route("/api/asistencia/toma", methods=["POST"])
@roles("Superadmin", "Coordinador", "Director", "Docente")
def api_asistencia_crear_toma():
    d = request.json or {}
    u = cu()
    cid, terr = resolve_colegio_id(u)
    if terr:
        return jsonify({"ok": False, "error": terr}), 400
    fecha = (d.get("fecha") or "").strip()
    curso = (d.get("curso") or "").strip()
    asignatura = (d.get("asignatura") or "").strip() or (u.get("asignatura") or "")
    lineas = d.get("lineas") or []
    if not fecha or not curso:
        return jsonify({"ok": False, "error": "Fecha y curso obligatorios"}), 400
    if u["rol"] == "Director" and u.get("curso") and curso != u["curso"]:
        return jsonify({"ok": False, "error": "Solo su curso asignado"}), 403
    conn = get_db()
    p = ph()
    creado = datetime.now().strftime("%Y-%m-%d %H:%M")
    execute(
        conn,
        f"INSERT INTO asistencia_toma (colegio_id,fecha,curso,asignatura,docente_id,docente_nombre,creado_en) VALUES ({p},{p},{p},{p},{p},{p},{p})",
        (cid, fecha, curso, asignatura, u["id"], u["nombre"], creado),
    )
    if USE_PG:
        tid = execute(conn, "SELECT lastval() as lid", fetch="one")["lid"]
    else:
        tid = execute(conn, "SELECT last_insert_rowid() as lid", fetch="one")["lid"]
    for ln in lineas:
        eid = ln.get("estudiante_id")
        if not eid:
            continue
        est = execute(conn, f"SELECT nombre,curso FROM estudiantes WHERE id={p} AND colegio_id={p}", (eid, cid), fetch="one")
        if not est or est["curso"] != curso:
            continue
        jus = ln.get("justificada")
        ji = 1 if jus is True else (0 if jus is False else None)
        execute(
            conn,
            f"INSERT INTO asistencia_detalle (toma_id,estudiante_id,estudiante_nombre,ausente,justificada) VALUES ({p},{p},{p},{p},{p})",
            (tid, eid, est["nombre"], 1, ji),
        )
    commit(conn)
    conn.close()
    return jsonify({"ok": True, "toma_id": tid})


@bp.route("/api/asistencia/linea/<int:lid>", methods=["PATCH"])
@roles("Superadmin", "Coordinador", "Director")
def api_asistencia_linea_justificar(lid):
    d = request.json or {}
    u = cu()
    tenant_id, terr = resolve_colegio_id(u)
    if terr:
        return jsonify({"error": terr}), 400
    jus = d.get("justificada")
    if jus not in (True, False):
        return jsonify({"error": "justificada debe ser true o false"}), 400
    conn = get_db()
    p = ph()
    row = execute(
        conn,
        f"SELECT d.*,t.curso,t.colegio_id FROM asistencia_detalle d JOIN asistencia_toma t ON t.id=d.toma_id WHERE d.id={p}",
        (lid,),
        fetch="one",
    )
    if not row or int(row["colegio_id"] or 0) != int(tenant_id):
        conn.close()
        return jsonify({"error": "No encontrada"}), 404
    if u["rol"] == "Director" and u.get("curso") and row["curso"] != u["curso"]:
        conn.close()
        return jsonify({"error": "Sin permisos"}), 403
    ji = 1 if jus else 0
    execute(conn, f"UPDATE asistencia_detalle SET justificada={p} WHERE id={p}", (ji, lid))
    commit(conn)
    conn.close()
    return jsonify({"ok": True})


@bp.route("/api/me/asignatura", methods=["PATCH"])
@login_required
def api_me_asignatura():
    u = cu()
    if u["rol"] != "Docente":
        return jsonify({"error": "Solo docentes"}), 403
    asig = (request.json or {}).get("asignatura", "")
    asig = str(asig).strip()[:120]
    conn = get_db()
    p = ph()
    execute(conn, f"UPDATE usuarios SET asignatura={p} WHERE id={p}", (asig, u["id"]))
    commit(conn)
    conn.close()
    session["usuario"]["asignatura"] = asig
    return jsonify({"ok": True})
