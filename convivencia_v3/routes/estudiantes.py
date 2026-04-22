"""CRUD e importación masiva de estudiantes."""
import csv
from io import StringIO
from typing import Optional

from flask import Blueprint, Response, jsonify, request

from ce_db import USE_PG, commit, execute, get_db, ph
from ce_utils import clave_portal_estudiante_por_defecto, hpwd, nombre_desde_partes, solo_letras, solo_numeros
from routes.authz import cu, login_required, resolve_colegio_id, roles

bp = Blueprint("estudiantes", __name__)


def _usuario_interno_estudiante(est_id: int) -> str:
    """Login por documento usa JOIN; este valor solo cumple UNIQUE en usuarios."""
    return f"est_{int(est_id)}"


def _sync_usuario_estudiante(conn, est_id: int, col_id: int, nombre: str, curso: str, documento_identidad: str, clave: Optional[str] = None):
    """Crea o actualiza usuario con rol Estudiante (documento + contraseña en /api/login y /reporte).

    Si `clave` está vacío, usa los 4 últimos dígitos del documento. Si se indica clave, mínimo 4 caracteres.
    """
    doc = solo_numeros(str(documento_identidad or ""))
    raw = (clave or "").strip()
    effective = raw if raw else clave_portal_estudiante_por_defecto(doc)
    if not solo_numeros(doc):
        return False, "El documento del estudiante debe incluir dígitos para generar la contraseña inicial."
    if len(effective) < 4:
        return False, "La contraseña del portal estudiante debe tener al menos 4 caracteres."
    if len(effective) > 80:
        return False, "La contraseña del portal estudiante es demasiado larga."
    p = ph()
    uinterno = _usuario_interno_estudiante(est_id)
    ex = execute(conn, f"SELECT id FROM usuarios WHERE estudiante_id={p} AND rol='Estudiante'", (est_id,), fetch="one")
    h = hpwd(effective)
    if ex:
        execute(
            conn,
            f"UPDATE usuarios SET contrasena={p}, nombre={p}, curso={p}, colegio_id={p} WHERE id={p}",
            (h, nombre[:120], (curso or "")[:80], col_id, ex["id"]),
        )
    else:
        execute(
            conn,
            f"INSERT INTO usuarios (usuario,contrasena,rol,nombre,curso,colegio_id,estudiante_id) VALUES ({p},{p},{p},{p},{p},{p},{p})",
            (uinterno, h, "Estudiante", nombre[:120], (curso or "")[:80], col_id, est_id),
        )
    return True, None


def _crear_acudiente(conn, cedula, nombre_acu, curso, col_id, est_id):
    cedula = solo_numeros(cedula)
    if not cedula:
        return
    p = ph()
    ex = execute(conn, f"SELECT id FROM usuarios WHERE usuario={p}", (cedula,), fetch="one")
    if not ex:
        execute(
            conn,
            f"INSERT INTO usuarios (usuario,contrasena,rol,nombre,curso,colegio_id,estudiante_id) VALUES ({p},{p},{p},{p},{p},{p},{p})",
            (cedula, hpwd(cedula), "Acudiente", nombre_acu or "Acudiente", curso, col_id, est_id),
        )


def _nombre_estudiante_payload(d):
    n = nombre_desde_partes(
        d.get("apellido1_est", ""), d.get("apellido2_est", ""), d.get("nombre1_est", ""), d.get("nombre2_est", "")
    )
    if n:
        return n
    return solo_letras(d.get("nombre", ""))


def _nombre_acudiente_payload(d):
    n = nombre_desde_partes(
        d.get("apellido1_acu", ""), d.get("apellido2_acu", ""), d.get("nombre1_acu", ""), d.get("nombre2_acu", "")
    )
    if n:
        return n
    return solo_letras(d.get("acudiente", ""))


def _row_csv(linea):
    linea = linea.strip()
    if not linea:
        return []
    try:
        return next(csv.reader(StringIO(linea)))
    except Exception:
        return [x.strip() for x in linea.split(",")]


def _strip_utf8_bom(s: str) -> str:
    if s.startswith("\ufeff"):
        return s[1:]
    return s


def _import_csv_rows(texto: str) -> list[list[str]]:
    """Parsea todo el texto como CSV (respeta comillas y separadores).

    Acepta delimitadores típicos de exportación: coma `,` y punto y coma `;` (Excel LATAM).
    """
    texto = _strip_utf8_bom((texto or "").strip())
    if not texto:
        return []
    sample = texto[:8192]
    delim = ","
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=";,\t|")
        delim = getattr(dialect, "delimiter", ",") or ","
    except Exception:
        # Heurística simple si el sniff falla
        if sample.count(";") > sample.count(","):
            delim = ";"
        elif sample.count("\t") > sample.count(","):
            delim = "\t"
        else:
            delim = ","
    return list(csv.reader(StringIO(texto), delimiter=delim))


def _is_extended_header_row(pts: list[str]) -> bool:
    """Primera fila típica de Excel: encabezados en lugar de datos."""
    if len(pts) < 15:
        return False
    doc_c = solo_numeros((pts[1] or ""))
    if len(doc_c) >= 5:
        return False
    t0 = (pts[0] or "").lower()
    t1 = (pts[1] or "").lower()
    if "tipo" in t0 and "doc" in t0.replace(" ", ""):
        return True
    if "documento" in t1 and ("est" in t1 or "estudiante" in t1 or "alumno" in t1):
        return True
    if "identificación" in t1 or "identificacion" in t1:
        return True
    return False


def _is_legacy_header_row(pts: list[str]) -> bool:
    if len(pts) >= 15:
        return False
    a = (pts[0] or "").strip().lower()
    b = (pts[1] or "").strip().lower() if len(pts) > 1 else ""
    if ("nombre" in a or "estudiante" in a) and ("curso" in b or "grado" in b or "grupo" in b or "salón" in b or "salon" in b):
        return True
    return False


def _import_insert_estudiante(
    conn,
    col_id,
    curso,
    doc_id,
    nombre,
    barr,
    acudiente,
    cedula,
    telefono,
    direccion,
    tipo_doc_est,
    ap1e,
    ap2e,
    n1e,
    n2e,
    tipo_doc_acu,
    ap1a,
    ap2a,
    n1a,
    n2a,
    parentesco,
    clave_portal: Optional[str] = None,
):
    p = ph()
    execute(
        conn,
        f"INSERT INTO estudiantes (documento_identidad,nombre,curso,discapacidad,acudiente,cedula_acudiente,telefono,direccion,colegio_id,"
        f"tipo_doc_est,apellido1_est,apellido2_est,nombre1_est,nombre2_est,barreras,"
        f"tipo_doc_acu,apellido1_acu,apellido2_acu,nombre1_acu,nombre2_acu,parentesco_acu,reporte_token,reporte_pin_hash) VALUES ({p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p})",
        (
            doc_id,
            nombre,
            curso,
            barr,
            acudiente,
            cedula,
            telefono,
            direccion,
            col_id,
            (tipo_doc_est or "")[:80],
            ap1e,
            ap2e,
            n1e,
            n2e,
            barr[:200],
            (tipo_doc_acu or "")[:80],
            ap1a,
            ap2a,
            n1a,
            n2a,
            parentesco[:60],
            "",
            "",
        ),
    )
    if USE_PG:
        eid = execute(conn, "SELECT lastval() as lid", fetch="one")["lid"]
    else:
        eid = execute(conn, "SELECT last_insert_rowid() as lid", fetch="one")["lid"]
    if cedula:
        _crear_acudiente(conn, cedula, acudiente, curso, col_id, eid)
    dnum = solo_numeros(doc_id)
    if len(dnum) >= 5:
        clave_eff = (clave_portal or "").strip() or None
        ok_m, err_m = _sync_usuario_estudiante(conn, eid, col_id, nombre, curso, dnum, clave_eff)
        if not ok_m:
            execute(conn, f"DELETE FROM usuarios WHERE estudiante_id={p}", (eid,))
            execute(conn, f"DELETE FROM estudiantes WHERE id={p}", (eid,))
            raise ValueError(err_m or "No se pudo crear usuario portal estudiante")
    return eid


@bp.route("/api/estudiantes")
@login_required
def api_estudiantes():
    u = cu()
    tenant_id, terr = resolve_colegio_id(u)
    if terr:
        return jsonify({"error": terr}), 400
    conn = get_db()
    p = ph()
    if u["rol"] == "Acudiente":
        try:
            eid = int(u.get("estudiante_id") or 0)
        except (TypeError, ValueError):
            eid = 0
        if not eid:
            conn.close()
            return jsonify({"error": "Sesión de acudiente sin estudiante asociado."}), 400
        rows = execute(conn, f"SELECT * FROM estudiantes WHERE colegio_id={p} AND id={p}", (tenant_id, eid), fetch="all")
        conn.close()
        return jsonify(rows or [])
    curso = request.args.get("curso", "")
    q = f"SELECT * FROM estudiantes WHERE colegio_id={p}"
    params = [tenant_id]
    if u["rol"] == "Director" and u["curso"] and not curso:
        q += f" AND curso={p}"
        params.append(u["curso"])
    elif curso:
        q += f" AND curso={p}"
        params.append(curso)
    rows = execute(conn, q + " ORDER BY curso,nombre", params, fetch="all")
    conn.close()
    return jsonify(rows)


@bp.route("/api/estudiantes", methods=["POST"])
@roles("Superadmin", "Coordinador", "Director")
def api_estudiante_crear():
    d = request.json or {}
    u = cu()
    col_id, terr = resolve_colegio_id(u)
    if terr:
        return jsonify({"ok": False, "error": terr}), 400
    conn = get_db()
    p = ph()
    nombre = _nombre_estudiante_payload(d)
    acudiente = _nombre_acudiente_payload(d)
    cedula = solo_numeros(d.get("cedula_acudiente", "") or d.get("documento_acudiente", ""))
    doc_id = solo_numeros(d.get("documento_identidad", ""))
    barr = (d.get("barreras") or d.get("discapacidad") or "").strip()[:200]
    if not barr:
        barr = "Ninguna identificada"
    if not nombre or not d.get("curso"):
        conn.close()
        return jsonify({"ok": False, "error": "Apellidos/nombres del estudiante y curso son obligatorios"}), 400
    if not acudiente or not cedula or len(cedula) < 5:
        conn.close()
        return jsonify({"ok": False, "error": "Datos completos del acudiente (nombres y documento) son obligatorios"}), 400
    if len(doc_id) < 5:
        conn.close()
        return jsonify(
            {"ok": False, "error": "El documento del estudiante debe tener al menos 5 dígitos (sin puntos) para el acceso al portal."}
        ), 400
    execute(
        conn,
        f"INSERT INTO estudiantes (documento_identidad,nombre,curso,discapacidad,acudiente,cedula_acudiente,telefono,direccion,colegio_id,"
        f"tipo_doc_est,apellido1_est,apellido2_est,nombre1_est,nombre2_est,barreras,"
        f"tipo_doc_acu,apellido1_acu,apellido2_acu,nombre1_acu,nombre2_acu,parentesco_acu,reporte_token,reporte_pin_hash) VALUES ({p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p})",
        (
            doc_id,
            nombre,
            d["curso"],
            barr,
            acudiente,
            cedula,
            solo_numeros(d.get("telefono", "")),
            d.get("direccion", "").strip(),
            col_id,
            (d.get("tipo_doc_est") or "")[:80],
            solo_letras(d.get("apellido1_est", "")),
            solo_letras(d.get("apellido2_est", "")),
            solo_letras(d.get("nombre1_est", "")),
            solo_letras(d.get("nombre2_est", "")),
            barr[:200],
            (d.get("tipo_doc_acu") or "")[:80],
            solo_letras(d.get("apellido1_acu", "")),
            solo_letras(d.get("apellido2_acu", "")),
            solo_letras(d.get("nombre1_acu", "")),
            solo_letras(d.get("nombre2_acu", "")),
            solo_letras(d.get("parentesco_acu", d.get("parentesco", "")))[:60],
            "",
            "",
        ),
    )
    if USE_PG:
        eid = execute(conn, "SELECT lastval() as lid", fetch="one")["lid"]
    else:
        eid = execute(conn, "SELECT last_insert_rowid() as lid", fetch="one")["lid"]
    _crear_acudiente(conn, cedula, acudiente, d["curso"], col_id, eid)
    clave_opt = (d.get("clave_estudiante") or "").strip() or None
    ok_m, err_m = _sync_usuario_estudiante(conn, eid, col_id, nombre, d["curso"], doc_id, clave_opt)
    if not ok_m:
        conn.close()
        return jsonify({"ok": False, "error": err_m}), 400
    commit(conn)
    conn.close()
    return jsonify({"ok": True, "id": eid})


@bp.route("/api/estudiantes/<int:eid>", methods=["PATCH"])
@roles("Superadmin", "Coordinador", "Director")
def api_estudiante_editar(eid):
    d = request.json or {}
    u = cu()
    tenant_id, terr = resolve_colegio_id(u)
    if terr:
        return jsonify({"ok": False, "error": terr}), 400
    conn = get_db()
    p = ph()
    nombre = _nombre_estudiante_payload(d)
    acudiente = _nombre_acudiente_payload(d)
    cedula = solo_numeros(d.get("cedula_acudiente", "") or d.get("documento_acudiente", ""))
    doc_id = solo_numeros(d.get("documento_identidad", ""))
    est = execute(conn, f"SELECT * FROM estudiantes WHERE id={p}", (eid,), fetch="one")
    if not est or int(est.get("colegio_id") or 0) != int(tenant_id):
        conn.close()
        return jsonify({"ok": False, "error": "No encontrado"}), 404
    barr = (d.get("barreras") or d.get("discapacidad") or "").strip()[:200]
    if not barr:
        barr = est.get("barreras") or est.get("discapacidad") or "Ninguna identificada"
    if not nombre or not d.get("curso"):
        conn.close()
        return jsonify({"ok": False, "error": "Apellidos/nombres del estudiante y curso son obligatorios"}), 400
    execute(
        conn,
        f"UPDATE estudiantes SET documento_identidad={p},nombre={p},curso={p},discapacidad={p},acudiente={p},cedula_acudiente={p},telefono={p},direccion={p},"
        f"tipo_doc_est={p},apellido1_est={p},apellido2_est={p},nombre1_est={p},nombre2_est={p},barreras={p},"
        f"tipo_doc_acu={p},apellido1_acu={p},apellido2_acu={p},nombre1_acu={p},nombre2_acu={p},parentesco_acu={p} WHERE id={p}",
        (
            doc_id,
            nombre,
            d["curso"],
            barr,
            acudiente,
            cedula,
            solo_numeros(d.get("telefono", "")),
            d.get("direccion", "").strip(),
            (d.get("tipo_doc_est") or "")[:80],
            solo_letras(d.get("apellido1_est", "")),
            solo_letras(d.get("apellido2_est", "")),
            solo_letras(d.get("nombre1_est", "")),
            solo_letras(d.get("nombre2_est", "")),
            barr[:200],
            (d.get("tipo_doc_acu") or "")[:80],
            solo_letras(d.get("apellido1_acu", "")),
            solo_letras(d.get("apellido2_acu", "")),
            solo_letras(d.get("nombre1_acu", "")),
            solo_letras(d.get("nombre2_acu", "")),
            solo_letras(d.get("parentesco_acu", d.get("parentesco", "")))[:60],
            eid,
        ),
    )
    if cedula and cedula != solo_numeros(est.get("cedula_acudiente", "") or ""):
        _crear_acudiente(conn, cedula, acudiente, d["curso"], est.get("colegio_id", 1), eid)
    elif cedula:
        execute(conn, f"UPDATE usuarios SET nombre={p} WHERE usuario={p} AND rol='Acudiente'", (acudiente, cedula))
    col_e = int(est.get("colegio_id") or tenant_id)
    clave_est = (d.get("clave_estudiante") or "").strip()
    if clave_est:
        ok_m, err_m = _sync_usuario_estudiante(conn, eid, col_e, nombre, d["curso"], doc_id, clave_est)
        if not ok_m:
            conn.close()
            return jsonify({"ok": False, "error": err_m}), 400
    commit(conn)
    conn.close()
    return jsonify({"ok": True})


@bp.route("/api/estudiantes/<int:eid>/reset-clave-portal", methods=["POST"])
@roles("Superadmin", "Coordinador", "Director")
def api_estudiante_reset_clave_portal(eid):
    """Deja la contraseña del portal estudiante en los 4 últimos dígitos del documento."""
    u = cu()
    tenant_id, terr = resolve_colegio_id(u)
    if terr:
        return jsonify({"ok": False, "error": terr}), 400
    conn = get_db()
    p = ph()
    est2 = execute(
        conn,
        f"SELECT id, documento_identidad, nombre, curso, colegio_id FROM estudiantes WHERE id={p}",
        (eid,),
        fetch="one",
    )
    if not est2 or int(est2.get("colegio_id") or 0) != int(tenant_id):
        conn.close()
        return jsonify({"ok": False, "error": "No encontrado"}), 404
    doc = solo_numeros((est2.get("documento_identidad") or ""))
    if len(doc) < 5:
        conn.close()
        return jsonify({"ok": False, "error": "El documento del estudiante debe tener al menos 5 dígitos."}), 400
    ok_m, err_m = _sync_usuario_estudiante(
        conn,
        eid,
        int(est2.get("colegio_id") or tenant_id),
        (est2.get("nombre") or "")[:120],
        (est2.get("curso") or "")[:80],
        doc,
        None,
    )
    if not ok_m:
        conn.close()
        return jsonify({"ok": False, "error": err_m}), 400
    commit(conn)
    conn.close()
    return jsonify({"ok": True})


@bp.route("/api/estudiantes/<int:eid>", methods=["DELETE"])
@roles("Superadmin", "Coordinador")
def api_estudiante_borrar(eid):
    u = cu()
    tenant_id, terr = resolve_colegio_id(u)
    if terr:
        return jsonify({"ok": False, "error": terr}), 400
    conn = get_db()
    p = ph()
    est = execute(conn, f"SELECT id, colegio_id FROM estudiantes WHERE id={p}", (eid,), fetch="one")
    if not est or int(est.get("colegio_id") or 0) != int(tenant_id):
        conn.close()
        return jsonify({"ok": False, "error": "No encontrado"}), 404
    execute(conn, f"DELETE FROM usuarios WHERE estudiante_id={p} AND rol='Estudiante'", (eid,))
    execute(conn, f"DELETE FROM estudiantes WHERE id={p}", (eid,))
    commit(conn)
    conn.close()
    return jsonify({"ok": True})


_PLANTILLA_CSV = (
    "tipo_doc_est,documento_est,apellido1,apellido2,nombre1,nombre2,curso,barreras,"
    "tipo_doc_acu,documento_acu,apellido1_acu,apellido2_acu,nombre1_acu,nombre2_acu,"
    "parentesco,telefono,direccion,clave_portal\r\n"
    "# Ejemplo (quite el # al inicio de la siguiente línea para probar):\r\n"
    "# CC,1234567890123,García,López,Ana,María,6A,Ninguna identificada,CC,9876543210987,"
    "García,Pérez,Carlos,,Padre,3001234567,Calle 10 5-20,\r\n"
)


@bp.route("/api/estudiantes/plantilla-importacion")
@login_required
@roles("Superadmin", "Coordinador", "Director")
def api_plantilla_importacion_estudiantes():
    """CSV UTF-8 con encabezados recomendados (misma convención que la carga masiva)."""
    return Response(
        _PLANTILLA_CSV,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="plantilla_estudiantes_convivencia.csv"'},
    )


@bp.route("/api/estudiantes/importar", methods=["POST"])
@roles("Superadmin", "Coordinador", "Director")
def api_importar_estudiantes():
    d = request.json or {}
    u = cu()
    col_id, terr = resolve_colegio_id(u)
    if terr:
        return jsonify({"ok": False, "error": terr}), 400
    conn = get_db()
    curso_def = (d.get("curso_default") or "").strip()
    count = 0
    errores = []
    rows = _import_csv_rows(d.get("texto", ""))
    start = 0
    if rows and _is_extended_header_row(rows[0]):
        start = 1
    elif rows and _is_legacy_header_row(rows[0]):
        start = 1

    for i, pts in enumerate(rows[start:], start=start + 1):
        pts = [(x or "").strip() for x in pts]
        if not any(pts):
            continue
        if pts[0].startswith("#"):
            continue
        low0 = pts[0].lower().replace("_", " ")
        if low0 in ("tipo doc est", "tipo_doc_est"):
            continue
        if len(pts) >= 15:
            tipo_doc_est = pts[0]
            doc_id = solo_numeros(pts[1])
            ap1e = solo_letras(pts[2])
            ap2e = solo_letras(pts[3])
            n1e = solo_letras(pts[4])
            n2e = solo_letras(pts[5]) if len(pts) > 5 else ""
            curso = (pts[6] or "").strip() or curso_def
            barr = (pts[7] or "").strip()[:200] if len(pts) > 7 else ""
            if not barr:
                barr = "Ninguna identificada"
            tipo_doc_acu = pts[8] if len(pts) > 8 else ""
            cedula = solo_numeros(pts[9]) if len(pts) > 9 else ""
            ap1a = solo_letras(pts[10]) if len(pts) > 10 else ""
            ap2a = solo_letras(pts[11]) if len(pts) > 11 else ""
            n1a = solo_letras(pts[12]) if len(pts) > 12 else ""
            n2a = solo_letras(pts[13]) if len(pts) > 13 else ""
            parentesco = (pts[14] or "").strip()[:60] if len(pts) > 14 else ""
            telefono = solo_numeros(pts[15]) if len(pts) > 15 else ""
            direccion = pts[16].strip() if len(pts) > 16 else ""
            clave_portal = (pts[17] or "").strip() if len(pts) > 17 else ""
            # Archivos reales suelen dejar dirección vacía y ponerla al final como "columna extra".
            # Si la dirección está vacía y la "clave" parece una dirección (tiene espacios / #),
            # se reasigna como dirección y se deja clave vacía.
            if not direccion and clave_portal and (" " in clave_portal or "#" in clave_portal):
                direccion = clave_portal[:120]
                clave_portal = ""
            nombre = nombre_desde_partes(ap1e, ap2e, n1e, n2e)
            acudiente = nombre_desde_partes(ap1a, ap2a, n1a, n2a)
            if not ap1e or not n1e or not curso:
                errores.append(f"Línea {i}: estudiante requiere apellido 1, nombre 1 y curso")
                continue
            if not acudiente or len(cedula) < 5:
                errores.append(f"Línea {i}: acudiente (nombres) y documento (mín. 5 dígitos) obligatorios")
                continue
            try:
                _import_insert_estudiante(
                    conn,
                    col_id,
                    curso,
                    doc_id,
                    nombre,
                    barr,
                    acudiente,
                    cedula,
                    telefono,
                    direccion,
                    tipo_doc_est,
                    ap1e,
                    ap2e,
                    n1e,
                    n2e,
                    tipo_doc_acu,
                    ap1a,
                    ap2a,
                    n1a,
                    n2a,
                    parentesco,
                    clave_portal or None,
                )
                commit(conn)  # evita que un error posterior anule filas ya buenas
            except ValueError as ex:
                try:
                    conn.rollback()
                except Exception:
                    pass
                errores.append(f"Línea {i}: {ex}")
                continue
            except Exception as ex:
                # En Postgres, un error deja la transacción en estado inválido hasta rollback.
                try:
                    conn.rollback()
                except Exception:
                    pass
                errores.append(f"Línea {i}: error interno al importar (revise formato/valores). {ex}")
                continue
            count += 1
            continue
        nombre = solo_letras(pts[0]) if pts else ""
        curso = (pts[1] or "").strip() or curso_def
        barr = (pts[2] or "").strip()[:200] if len(pts) > 2 else ""
        if not barr:
            barr = "Ninguna identificada"
        acudiente = solo_letras(pts[3]) if len(pts) > 3 else ""
        cedula = solo_numeros(pts[4]) if len(pts) > 4 else ""
        telefono = solo_numeros(pts[5]) if len(pts) > 5 else ""
        direccion = pts[6].strip() if len(pts) > 6 else ""
        doc_id = solo_numeros(pts[7]) if len(pts) > 7 else ""
        clave_portal = (pts[8] or "").strip() if len(pts) > 8 else ""
        if not nombre or not curso:
            errores.append(f"Línea {i}: falta nombre completo o curso (o use formato extendido de 17 columnas)")
            continue
        if not acudiente or len(cedula) < 5:
            errores.append(f"Línea {i}: acudiente y documento del acudiente (mín. 5 dígitos) obligatorios")
            continue
        try:
            _import_insert_estudiante(
                conn,
                col_id,
                curso,
                doc_id,
                nombre,
                barr,
                acudiente,
                cedula,
                telefono,
                direccion,
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                clave_portal or None,
            )
            commit(conn)  # evita que un error posterior anule filas ya buenas
        except ValueError as ex:
            try:
                conn.rollback()
            except Exception:
                pass
            errores.append(f"Línea {i}: {ex}")
            continue
        except Exception as ex:
            try:
                conn.rollback()
            except Exception:
                pass
            errores.append(f"Línea {i}: error interno al importar (revise formato/valores). {ex}")
            continue
        count += 1
    conn.close()
    return jsonify({"ok": True, "insertados": count, "errores": errores})
