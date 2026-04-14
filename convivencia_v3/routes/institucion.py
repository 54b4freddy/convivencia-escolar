"""Colegios y usuarios del sistema (no acudientes en listados de gestión)."""
from flask import Blueprint, jsonify, request

from ce_db import commit, execute, get_db, ph
from ce_utils import hpwd, nombre_desde_partes, solo_letras, solo_numeros
from routes.authz import cu, login_required, resolve_colegio_id, roles

bp = Blueprint("institucion", __name__)


@bp.route("/api/colegios")
@login_required
def api_colegios():
    u = cu()
    conn = get_db()
    p = ph()
    if u["rol"] == "Superadmin":
        rows = execute(conn, "SELECT * FROM colegios ORDER BY nombre", fetch="all")
    else:
        cid = u.get("colegio_id")
        if not cid:
            conn.close()
            return jsonify({"error": "Sin colegio asignado"}), 403
        rows = execute(conn, f"SELECT * FROM colegios WHERE id={p}", (cid,), fetch="all") or []
    result = []
    for c in rows:
        c["num_usuarios"] = execute(
            conn,
            f"SELECT COUNT(*) as n FROM usuarios WHERE colegio_id={p} AND rol!='Acudiente'",
            (c["id"],),
            fetch="one",
        ).get("n", 0)
        c["num_estudiantes"] = execute(
            conn, f"SELECT COUNT(*) as n FROM estudiantes WHERE colegio_id={p}", (c["id"],), fetch="one"
        ).get("n", 0)
        c["usuarios"] = execute(
            conn,
            f"SELECT id,usuario,rol,nombre,curso FROM usuarios WHERE colegio_id={p} AND rol!='Acudiente' ORDER BY rol,nombre",
            (c["id"],),
            fetch="all",
        )
        result.append(c)
    conn.close()
    return jsonify(result)


@bp.route("/api/colegios", methods=["POST"])
@roles("Superadmin")
def api_colegio_crear():
    d = request.json or {}
    conn = get_db()
    p = ph()
    execute(
        conn,
        f"INSERT INTO colegios (nombre,nit,municipio,rector,direccion,telefono,email) VALUES ({p},{p},{p},{p},{p},{p},{p})",
        (
            d["nombre"],
            d.get("nit", ""),
            d.get("municipio", ""),
            d.get("rector", ""),
            d.get("direccion", ""),
            d.get("telefono", ""),
            d.get("email", ""),
        ),
    )
    commit(conn)
    conn.close()
    return jsonify({"ok": True})


@bp.route("/api/colegios/<int:cid>", methods=["PATCH"])
@roles("Superadmin")
def api_colegio_editar(cid):
    d = request.json or {}
    conn = get_db()
    p = ph()
    execute(
        conn,
        f"UPDATE colegios SET nombre={p},nit={p},municipio={p},rector={p},direccion={p},telefono={p},email={p} WHERE id={p}",
        (
            d["nombre"],
            d.get("nit", ""),
            d.get("municipio", ""),
            d.get("rector", ""),
            d.get("direccion", ""),
            d.get("telefono", ""),
            d.get("email", ""),
            cid,
        ),
    )
    commit(conn)
    conn.close()
    return jsonify({"ok": True})


@bp.route("/api/usuarios")
@login_required
def api_usuarios():
    u = cu()
    conn = get_db()
    p = ph()
    if u["rol"] == "Superadmin":
        rows = execute(
            conn,
            "SELECT u.*,c.nombre as col_nom FROM usuarios u LEFT JOIN colegios c ON c.id=u.colegio_id WHERE u.rol!='Acudiente' ORDER BY u.rol,u.nombre",
            fetch="all",
        )
    else:
        tenant_id, terr = resolve_colegio_id(u)
        if terr:
            conn.close()
            return jsonify({"error": terr}), 400
        rows = execute(
            conn,
            f"SELECT u.*,c.nombre as col_nom FROM usuarios u LEFT JOIN colegios c ON c.id=u.colegio_id WHERE u.colegio_id={p} AND u.rol NOT IN ('Acudiente') ORDER BY u.rol,u.nombre",
            (tenant_id,),
            fetch="all",
        )
    conn.close()
    return jsonify([{k: v for k, v in r.items() if k != "contrasena"} for r in rows])


@bp.route("/api/usuarios", methods=["POST"])
@roles("Superadmin", "Coordinador")
def api_usuario_crear():
    d = request.json or {}
    u = cu()
    conn = get_db()
    p = ph()
    if u["rol"] == "Superadmin":
        try:
            cid = int(d.get("colegio_id"))
        except (TypeError, ValueError):
            conn.close()
            return jsonify({"ok": False, "error": "Indique colegio_id (entero) para el nuevo usuario."}), 400
        if cid <= 0:
            conn.close()
            return jsonify({"ok": False, "error": "colegio_id no válido."}), 400
    else:
        cid, cerr = resolve_colegio_id(u)
        if cerr:
            conn.close()
            return jsonify({"ok": False, "error": cerr}), 400
    try:
        nom = (d.get("nombre") or "").strip() or nombre_desde_partes(
            d.get("apellido1", ""), d.get("apellido2", ""), d.get("nombre1", ""), d.get("nombre2", "")
        )
        if not nom:
            conn.close()
            return jsonify({"ok": False, "error": "Indique nombre o apellidos y nombres."}), 400
        execute(
            conn,
            f"INSERT INTO usuarios (usuario,contrasena,rol,nombre,curso,colegio_id,asignatura,tipo_doc,documento_personal,apellido1,apellido2,nombre1,nombre2,telefono) VALUES ({p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p})",
            (
                d["usuario"],
                hpwd(d["contrasena"]),
                d["rol"],
                nom,
                d.get("curso", ""),
                cid,
                d.get("asignatura", "").strip(),
                (d.get("tipo_doc") or "").strip()[:80],
                solo_numeros(d.get("documento_personal", "")),
                solo_letras(d.get("apellido1", "")),
                solo_letras(d.get("apellido2", "")),
                solo_letras(d.get("nombre1", "")),
                solo_letras(d.get("nombre2", "")),
                solo_numeros(d.get("telefono", "")),
            ),
        )
        commit(conn)
        conn.close()
        return jsonify({"ok": True})
    except Exception:
        conn.close()
        return jsonify({"ok": False, "error": "El usuario ya existe"}), 409


@bp.route("/api/usuarios/<int:uid>", methods=["PATCH"])
@roles("Superadmin", "Coordinador")
def api_usuario_editar(uid):
    d = request.json or {}
    u = cu()
    conn = get_db()
    p = ph()
    target = execute(conn, f"SELECT id, colegio_id, rol FROM usuarios WHERE id={p}", (uid,), fetch="one")
    if not target:
        conn.close()
        return jsonify({"ok": False, "error": "No encontrado"}), 404
    if u["rol"] == "Coordinador":
        tenant_id, terr = resolve_colegio_id(u)
        if terr:
            conn.close()
            return jsonify({"ok": False, "error": terr}), 400
        if int(target.get("colegio_id") or 0) != int(tenant_id):
            conn.close()
            return jsonify({"ok": False, "error": "Sin permisos"}), 403
        if target.get("rol") == "Superadmin" or d.get("rol") == "Superadmin":
            conn.close()
            return jsonify({"ok": False, "error": "Sin permisos"}), 403
    asig = d.get("asignatura", "")
    nom = (d.get("nombre") or "").strip() or nombre_desde_partes(
        d.get("apellido1", ""), d.get("apellido2", ""), d.get("nombre1", ""), d.get("nombre2", "")
    )
    if not nom:
        conn.close()
        return jsonify({"ok": False, "error": "Indique nombre o apellidos y nombres."}), 400
    td = (d.get("tipo_doc") or "").strip()[:80]
    dp = solo_numeros(d.get("documento_personal", ""))
    a1, a2, n1, n2 = (
        solo_letras(d.get("apellido1", "")),
        solo_letras(d.get("apellido2", "")),
        solo_letras(d.get("nombre1", "")),
        solo_letras(d.get("nombre2", "")),
    )
    tel = solo_numeros(d.get("telefono", ""))
    if d.get("contrasena"):
        execute(
            conn,
            f"UPDATE usuarios SET nombre={p},rol={p},curso={p},asignatura={p},tipo_doc={p},documento_personal={p},apellido1={p},apellido2={p},nombre1={p},nombre2={p},telefono={p},contrasena={p} WHERE id={p}",
            (nom, d["rol"], d.get("curso", ""), asig.strip(), td, dp, a1, a2, n1, n2, tel, hpwd(d["contrasena"]), uid),
        )
    else:
        execute(
            conn,
            f"UPDATE usuarios SET nombre={p},rol={p},curso={p},asignatura={p},tipo_doc={p},documento_personal={p},apellido1={p},apellido2={p},nombre1={p},nombre2={p},telefono={p} WHERE id={p}",
            (nom, d["rol"], d.get("curso", ""), asig.strip(), td, dp, a1, a2, n1, n2, tel, uid),
        )
    commit(conn)
    conn.close()
    return jsonify({"ok": True})


@bp.route("/api/usuarios/<int:uid>", methods=["DELETE"])
@roles("Superadmin", "Coordinador")
def api_usuario_borrar(uid):
    u = cu()
    if uid == u["id"]:
        return jsonify({"ok": False, "error": "No puedes eliminarte"}), 400
    conn = get_db()
    p = ph()
    target = execute(conn, f"SELECT id, colegio_id, rol FROM usuarios WHERE id={p}", (uid,), fetch="one")
    if not target:
        conn.close()
        return jsonify({"ok": False, "error": "No encontrado"}), 404
    if u["rol"] == "Coordinador":
        tenant_id, terr = resolve_colegio_id(u)
        if terr:
            conn.close()
            return jsonify({"ok": False, "error": terr}), 400
        if int(target.get("colegio_id") or 0) != int(tenant_id):
            conn.close()
            return jsonify({"ok": False, "error": "Sin permisos"}), 403
        if target.get("rol") == "Superadmin":
            conn.close()
            return jsonify({"ok": False, "error": "Sin permisos"}), 403
    execute(conn, f"DELETE FROM usuarios WHERE id={p}", (uid,))
    commit(conn)
    conn.close()
    return jsonify({"ok": True})
