"""Reportes, exportación y PDFs. Datos siempre acotados por colegio_id y rol (multi-institución)."""
import json
import re
from collections import Counter
from datetime import datetime

from flask import Blueprint, jsonify, request, Response

from ce_db import commit, execute, get_db, ph
from ce_export import csv_response
from ce_pdf import generar_pdf_acta_descargos, generar_pdf_acta_proceso, generar_pdf_curso, generar_pdf_estudiante
from ce_queries import col_nom, fq, faltas_con_notas
from ce_sugerencias import generar_sugerencias
from routes.authz import cu, login_required, resolve_colegio_id, roles

bp = Blueprint("reportes", __name__)


def _puede_descargar_acta(u, f):
    if u["rol"] == "Superadmin":
        return True
    if (u.get("colegio_id") or 1) != (f.get("colegio_id") or 1):
        return False
    if u["rol"] == "Acudiente":
        return f.get("estudiante_id") == u.get("estudiante_id")
    if u["rol"] == "Docente":
        return f.get("docente") == u["nombre"]
    if u["rol"] == "Director":
        return f.get("curso") == u.get("curso") or f.get("docente") == u.get("nombre")
    return True


@bp.route("/api/reportes")
@login_required
def api_reportes():
    u = cu()
    anio = request.args.get("anio", str(datetime.now().year))
    tenant_id, terr = resolve_colegio_id(u)
    if terr:
        return jsonify({"error": terr}), 400
    u_sc = {**u, "colegio_id": tenant_id}
    conn = get_db()
    q, p = fq(u_sc, anio)
    faltas = execute(conn, q, p, fetch="all")
    conn.close()
    ests_t1 = Counter(f["estudiante"] for f in faltas if f["tipo_falta"] == "Tipo I")
    reincidencias_t1 = [
        {"estudiante": e, "count": n, "sugerencia": "Activar proceso Tipo II: citación de acudiente y compromiso formal."}
        for e, n in ests_t1.items()
        if n >= 3
    ]
    ests_all = Counter(f["estudiante"] for f in faltas)
    tipos = Counter(f["tipo_falta"] for f in faltas)
    cursos = Counter(f["curso"] for f in faltas)
    docs = Counter(f["docente"] for f in faltas)
    meses = Counter(f["fecha"][5:7] for f in faltas if f["fecha"])
    sugerencias = generar_sugerencias(faltas)
    return jsonify(
        {
            "total": len(faltas),
            "por_tipo": dict(tipos),
            "por_curso": dict(cursos),
            "top_estudiantes": ests_all.most_common(10),
            "por_docente": dict(docs),
            "por_mes": dict(meses),
            "reincidentes": [e for e, n in ests_all.items() if n >= 4],
            "reincidencias_tipo_i": reincidencias_t1,
            "sugerencias": sugerencias,
        }
    )


@bp.route("/api/exportar-csv")
@login_required
def api_exportar_csv():
    u = cu()
    anio = request.args.get("anio", str(datetime.now().year))
    tenant_id, terr = resolve_colegio_id(u)
    if terr:
        return jsonify({"error": terr}), 400
    u_sc = {**u, "colegio_id": tenant_id}
    conn = get_db()
    q, params = fq(u_sc, anio)
    faltas = execute(conn, q, params, fetch="all")
    conn.close()
    header = [
        "id",
        "anio",
        "fecha",
        "curso",
        "estudiante",
        "tipo_falta",
        "falta_especifica",
        "descripcion",
        "proceso_inicial",
        "protocolo_aplicado",
        "sancion_aplicada",
        "docente",
        "colegio_id",
    ]
    rows = (
        [
            f.get("id"),
            f.get("anio"),
            f.get("fecha"),
            f.get("curso"),
            f.get("estudiante"),
            f.get("tipo_falta"),
            f.get("falta_especifica"),
            f.get("descripcion"),
            f.get("proceso_inicial"),
            f.get("protocolo_aplicado", ""),
            f.get("sancion_aplicada", ""),
            f.get("docente"),
            f.get("colegio_id"),
        ]
        for f in faltas
    )
    return csv_response(f"faltas_{anio}.csv", header, rows)


@bp.route("/api/reporte-estudiante")
@login_required
def api_reporte_estudiante():
    u = cu()
    estudiante = (request.args.get("estudiante") or "").strip()
    anio = request.args.get("anio", "todos")
    if not estudiante:
        return jsonify({"error": "Estudiante requerido"}), 400

    conn = get_db()
    p = ph()
    if u["rol"] == "Acudiente":
        est = execute(conn, f"SELECT nombre FROM estudiantes WHERE id={p}", (u.get("estudiante_id"),), fetch="one")
        if not est:
            conn.close()
            return jsonify({"error": "Sin estudiante asociado"}), 400
        estudiante = est["nombre"]

    tenant_id, terr = resolve_colegio_id(u)
    if terr:
        conn.close()
        return jsonify({"error": terr}), 400

    where = f"f.colegio_id={p} AND f.estudiante={p}"
    params = [tenant_id, estudiante]
    if anio != "todos":
        where += f" AND f.anio={p}"
        params.append(anio)

    if u["rol"] == "Director":
        where += f" AND (f.curso={p} OR f.docente={p})"
        params += [u.get("curso", ""), u.get("nombre", "")]
    elif u["rol"] == "Docente":
        where += f" AND f.docente={p}"
        params.append(u.get("nombre", ""))

    faltas = faltas_con_notas(conn, where, params)
    conn.close()

    header = [
        "id",
        "anio",
        "fecha",
        "curso",
        "estudiante",
        "tipo_falta",
        "falta_especifica",
        "descripcion",
        "proceso_inicial",
        "docente",
        "notas",
    ]
    rows = (
        [
            f.get("id"),
            f.get("anio"),
            f.get("fecha"),
            f.get("curso"),
            f.get("estudiante"),
            f.get("tipo_falta"),
            f.get("falta_especifica"),
            f.get("descripcion"),
            f.get("proceso_inicial"),
            f.get("docente"),
            f.get("notas") or "",
        ]
        for f in faltas
    )
    safe_name = re.sub(r"[^a-zA-Z0-9_-]+", "_", estudiante).strip("_") or "estudiante"
    return csv_response(f"historial_{safe_name}.csv", header, rows)


@bp.route("/api/mejoramiento")
@login_required
def api_mejoramiento():
    u = cu()
    if u["rol"] not in ("Director", "Coordinador", "Orientador", "Superadmin"):
        return jsonify({"error": "Sin permisos"}), 403
    anio = request.args.get("anio", str(datetime.now().year))
    tenant_id, terr = resolve_colegio_id(u)
    if terr:
        return jsonify({"error": terr}), 400
    u_sc = {**u, "colegio_id": tenant_id}
    conn = get_db()
    q, p = fq(u_sc, anio)
    faltas = execute(conn, q, p, fetch="all")
    conn.close()
    por_curso = {}
    for f in faltas:
        c = f["curso"]
        if c not in por_curso:
            por_curso[c] = {"total": 0, "t1": 0, "t2": 0, "t3": 0, "faltas": [], "reincidentes_t1": []}
        por_curso[c]["total"] += 1
        por_curso[c]["faltas"].append(f)
        if f["tipo_falta"] == "Tipo I":
            por_curso[c]["t1"] += 1
        elif f["tipo_falta"] == "Tipo II":
            por_curso[c]["t2"] += 1
        elif f["tipo_falta"] == "Tipo III":
            por_curso[c]["t3"] += 1
    result = {}
    for curso, data in por_curso.items():
        t1_est = Counter(f["estudiante"] for f in data["faltas"] if f["tipo_falta"] == "Tipo I")
        data["reincidentes_t1"] = [{"estudiante": e, "count": n} for e, n in t1_est.items() if n >= 3]
        data["sugerencias"] = generar_sugerencias(data["faltas"])
        del data["faltas"]
        result[curso] = data
    return jsonify(result)


@bp.route("/api/pdf/curso")
@login_required
def api_pdf_curso():
    u = cu()
    if u["rol"] == "Acudiente":
        return jsonify({"error": "Sin permisos"}), 403
    curso = request.args.get("curso", "")
    anio = request.args.get("anio", str(datetime.now().year))
    cid, terr = resolve_colegio_id(u)
    if terr:
        return jsonify({"error": terr}), 400
    if not curso:
        return jsonify({"error": "Curso requerido"}), 400
    if u["rol"] == "Director" and u.get("curso") and curso != u["curso"]:
        return jsonify({"error": "Solo su curso asignado"}), 403

    conn = get_db()
    p = ph()
    where = f"f.colegio_id={p} AND f.anio={p} AND f.curso={p}"
    params = [cid, anio, curso]
    if u["rol"] == "Docente":
        where += f" AND f.docente={p}"
        params.append(u["nombre"])

    faltas = faltas_con_notas(conn, where, params)
    conn.close()
    buf = generar_pdf_curso(col_nom(cid), curso, anio, faltas)
    return Response(
        buf.read(),
        mimetype="application/pdf",
        headers={"Content-Disposition": f'attachment;filename=faltas_{curso.replace(" ", "_")}_{anio}.pdf'},
    )


@bp.route("/api/pdf/estudiante")
@login_required
def api_pdf_estudiante():
    u = cu()
    est_id = request.args.get("est_id")
    nombre_est = request.args.get("estudiante", "")
    anio = request.args.get("anio", "todos")
    cid, terr = resolve_colegio_id(u)
    if terr:
        return jsonify({"error": terr}), 400
    conn = get_db()
    p = ph()
    est_info = None

    if u["rol"] == "Acudiente":
        est = execute(conn, f"SELECT * FROM estudiantes WHERE id={p}", (u.get("estudiante_id"),), fetch="one")
        if not est:
            conn.close()
            return jsonify({"error": "Sin estudiante asociado"}), 400
        nombre_est = est["nombre"]
        est_info = est
    elif est_id:
        est_info = execute(
            conn,
            f"SELECT * FROM estudiantes WHERE id={p} AND colegio_id={p}",
            (est_id, cid),
            fetch="one",
        )
        if est_info:
            nombre_est = est_info["nombre"]
    elif nombre_est:
        est_info = execute(
            conn,
            f"SELECT * FROM estudiantes WHERE nombre={p} AND colegio_id={p}",
            (nombre_est, cid),
            fetch="one",
        )

    if not nombre_est:
        conn.close()
        return jsonify({"error": "Estudiante requerido"}), 400

    where = f"f.colegio_id={p} AND f.estudiante={p}"
    params = [cid, nombre_est]
    if u["rol"] == "Acudiente" and u.get("estudiante_id") is not None:
        where += f" AND f.estudiante_id={p}"
        params.append(u["estudiante_id"])
    if anio != "todos":
        where += f" AND f.anio={p}"
        params.append(anio)

    if u["rol"] == "Director":
        where += f" AND (f.curso={p} OR f.docente={p})"
        params += [u.get("curso", ""), u.get("nombre", "")]
    elif u["rol"] == "Docente":
        where += f" AND f.docente={p}"
        params.append(u.get("nombre", ""))

    faltas = faltas_con_notas(conn, where, params)
    conn.close()
    buf = generar_pdf_estudiante(col_nom(cid), nombre_est, faltas, est_info)
    return Response(
        buf.read(),
        mimetype="application/pdf",
        headers={"Content-Disposition": f'attachment;filename=historial_{nombre_est.replace(" ", "_")}.pdf'},
    )


@bp.route("/api/pdf/general")
@login_required
def api_pdf_general():
    u = cu()
    if u["rol"] == "Acudiente":
        return jsonify({"error": "Sin permisos"}), 403
    anio = request.args.get("anio", str(datetime.now().year))
    cid, terr = resolve_colegio_id(u)
    if terr:
        return jsonify({"error": terr}), 400
    conn = get_db()
    ph_ = ph()
    where = f"f.colegio_id={ph_} AND f.anio={ph_}"
    params = [cid, anio]
    if u["rol"] == "Director":
        where += f" AND (f.curso={ph_} OR f.docente={ph_})"
        params += [u["curso"], u["nombre"]]
    elif u["rol"] == "Docente":
        where += f" AND f.docente={ph_}"
        params.append(u["nombre"])

    faltas = faltas_con_notas(conn, where, params)
    conn.close()
    buf = generar_pdf_curso(col_nom(cid), "Todos los cursos", anio, faltas)
    return Response(
        buf.read(),
        mimetype="application/pdf",
        headers={"Content-Disposition": f"attachment;filename=reporte_general_{anio}.pdf"},
    )


@bp.route("/api/pdf/acta-descargos/<int:fid>")
@login_required
def api_pdf_acta_descargos(fid):
    u = cu()
    cid, terr = resolve_colegio_id(u)
    if terr:
        return jsonify({"error": terr}), 400
    conn = get_db()
    p = ph()
    f = execute(
        conn,
        f"SELECT f.*, e.documento_identidad FROM faltas f "
        f"LEFT JOIN estudiantes e ON e.id=f.estudiante_id WHERE f.id={p}",
        (fid,),
        fetch="one",
    )
    if not f:
        conn.close()
        return jsonify({"error": "No encontrada"}), 404
    if int(f.get("colegio_id") or 0) != int(cid):
        conn.close()
        return jsonify({"error": "Sin permisos"}), 403
    if not _puede_descargar_acta(u, f):
        conn.close()
        return jsonify({"error": "Sin permisos"}), 403
    acta = execute(conn, f"SELECT * FROM acta_descargos WHERE falta_id={p}", (fid,), fetch="one")
    if not acta:
        conn.close()
        return jsonify({"error": "No hay acta de descargos registrada para esta falta"}), 404
    try:
        datos = json.loads(acta.get("datos_json") or "{}")
    except json.JSONDecodeError:
        datos = {}
    col = execute(conn, f"SELECT nombre,nit,municipio FROM colegios WHERE id={p}", (cid,), fetch="one") or {}
    tok = acta.get("verificacion_token") or ""
    base = request.url_root.rstrip("/")
    vurl = f"{base}/api/verificar-descargos/{tok}" if tok else ""
    conn.close()
    buf = generar_pdf_acta_descargos(col, f, datos, vurl)
    safe = re.sub(r"[^a-zA-Z0-9_-]+", "_", str(f.get("estudiante", "descargos"))).strip("_") or "descargos"
    return Response(
        buf.read(),
        mimetype="application/pdf",
        headers={"Content-Disposition": f"attachment;filename=acta_descargos_{fid}_{safe}.pdf"},
    )


@bp.route("/api/pdf/acta/<int:fid>")
@login_required
def api_pdf_acta(fid):
    u = cu()
    cid, terr = resolve_colegio_id(u)
    if terr:
        return jsonify({"error": terr}), 400
    conn = get_db()
    p = ph()
    f = execute(conn, f"SELECT * FROM faltas WHERE id={p}", (fid,), fetch="one")
    if not f:
        conn.close()
        return jsonify({"error": "No encontrada"}), 404
    if int(f.get("colegio_id") or 0) != int(cid):
        conn.close()
        return jsonify({"error": "Sin permisos"}), 403
    if not _puede_descargar_acta(u, f):
        conn.close()
        return jsonify({"error": "Sin permisos"}), 403
    anots = execute(conn, f"SELECT * FROM anotaciones WHERE falta_id={p} ORDER BY id", (fid,), fetch="all")
    conn.close()
    buf = generar_pdf_acta_proceso(col_nom(cid), f, anots or [])
    safe = re.sub(r"[^a-zA-Z0-9_-]+", "_", str(f.get("estudiante", "acta"))).strip("_") or "acta"
    return Response(
        buf.read(),
        mimetype="application/pdf",
        headers={"Content-Disposition": f"attachment;filename=acta_falta_{fid}_{safe}.pdf"},
    )


@bp.route("/api/cerrar-anio", methods=["POST"])
@roles("Superadmin", "Coordinador")
def api_cerrar_anio():
    d = request.json or {}
    u = cu()
    conn = get_db()
    p = ph()
    if d.get("limpiar_estudiantes"):
        cid, cerr = resolve_colegio_id(u)
        if cerr:
            conn.close()
            return jsonify({"ok": False, "error": cerr}), 400
        execute(conn, f"DELETE FROM estudiantes WHERE colegio_id={p}", (cid,))
    commit(conn)
    conn.close()
    return jsonify({"ok": True})
