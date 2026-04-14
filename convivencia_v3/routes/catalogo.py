"""Catálogo de faltas por colegio (tipos I / II / III)."""
from flask import Blueprint, jsonify, request

from ce_db import commit, execute, get_db, ph
from routes.authz import cu, login_required, resolve_colegio_id, roles

bp = Blueprint("catalogo", __name__)


@bp.route("/api/catalogo")
@login_required
def api_catalogo():
    u = cu()
    tenant_id, terr = resolve_colegio_id(u)
    if terr:
        return jsonify({"error": terr}), 400
    conn = get_db()
    p = ph()
    tipo = request.args.get("tipo", "")
    q = f"SELECT * FROM catalogo_faltas WHERE colegio_id={p}"
    params = [tenant_id]
    if tipo:
        q += f" AND tipo={p}"
        params.append(tipo)
    rows = execute(conn, q + " ORDER BY tipo,descripcion", params, fetch="all")
    conn.close()
    return jsonify(rows)


@bp.route("/api/catalogo", methods=["POST"])
@roles("Superadmin", "Coordinador")
def api_catalogo_crear():
    d = request.json or {}
    u = cu()
    tenant_id, terr = resolve_colegio_id(u)
    if terr:
        return jsonify({"error": terr}), 400
    conn = get_db()
    p = ph()
    execute(
        conn,
        f"INSERT INTO catalogo_faltas (tipo,descripcion,protocolo,sancion,colegio_id) VALUES ({p},{p},{p},{p},{p})",
        (d["tipo"], d["descripcion"], d.get("protocolo", ""), d.get("sancion", ""), tenant_id),
    )
    commit(conn)
    conn.close()
    return jsonify({"ok": True})


@bp.route("/api/catalogo/<int:cid>", methods=["PATCH"])
@roles("Superadmin", "Coordinador")
def api_catalogo_editar(cid):
    d = request.json or {}
    u = cu()
    tenant_id, terr = resolve_colegio_id(u)
    if terr:
        return jsonify({"error": terr}), 400
    conn = get_db()
    p = ph()
    row = execute(conn, f"SELECT id, colegio_id FROM catalogo_faltas WHERE id={p}", (cid,), fetch="one")
    if not row or int(row.get("colegio_id") or 0) != int(tenant_id):
        conn.close()
        return jsonify({"error": "No encontrada"}), 404
    execute(
        conn,
        f"UPDATE catalogo_faltas SET protocolo={p},sancion={p} WHERE id={p}",
        (d.get("protocolo", ""), d.get("sancion", ""), cid),
    )
    commit(conn)
    conn.close()
    return jsonify({"ok": True})


@bp.route("/api/catalogo/<int:cid>", methods=["DELETE"])
@roles("Superadmin", "Coordinador")
def api_catalogo_borrar(cid):
    u = cu()
    tenant_id, terr = resolve_colegio_id(u)
    if terr:
        return jsonify({"error": terr}), 400
    conn = get_db()
    p = ph()
    row = execute(conn, f"SELECT id, colegio_id FROM catalogo_faltas WHERE id={p}", (cid,), fetch="one")
    if not row or int(row.get("colegio_id") or 0) != int(tenant_id):
        conn.close()
        return jsonify({"error": "No encontrada"}), 404
    execute(conn, f"DELETE FROM catalogo_faltas WHERE id={p}", (cid,))
    commit(conn)
    conn.close()
    return jsonify({"ok": True})


@bp.route("/api/catalogo/importar", methods=["POST"])
@roles("Superadmin", "Coordinador")
def api_catalogo_importar():
    d = request.json or {}
    u = cu()
    cid, terr = resolve_colegio_id(u)
    if terr:
        return jsonify({"ok": False, "error": terr}), 400
    items = d.get("items")
    if not items and d.get("texto"):
        items = []
        for linea in d.get("texto", "").split("\n"):
            linea = linea.strip()
            if not linea or linea.startswith("#"):
                continue
            parts = [x.strip() for x in linea.split(",")]
            if len(parts) < 2:
                continue
            items.append({"tipo": parts[0], "descripcion": parts[1]})
    if not items:
        return jsonify({"ok": False, "error": "Envíe items[] o texto con líneas: Tipo I,Descripción"}), 400
    conn = get_db()
    p = ph()
    n = 0
    for it in items:
        tipo = (it.get("tipo") or "").strip()
        desc = (it.get("descripcion") or "").strip()
        if tipo not in ("Tipo I", "Tipo II", "Tipo III") or not desc:
            continue
        execute(
            conn,
            f"INSERT INTO catalogo_faltas (tipo,descripcion,protocolo,sancion,colegio_id) VALUES ({p},{p},{p},{p},{p})",
            (tipo, desc[:500], "", "", cid),
        )
        n += 1
    commit(conn)
    conn.close()
    return jsonify({"ok": True, "insertados": n})
