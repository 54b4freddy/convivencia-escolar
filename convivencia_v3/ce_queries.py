"""Consultas reutilizadas por las rutas API (filtros por rol, agregación de notas)."""
from datetime import datetime

from ce_db import USE_PG, execute, get_db, ph


def fq(usuario, anio, filtros=None, colegio_id=None):
    """Query base de faltas según rol y año. Retorna (sql, params).

    filtros opcionales (dict): curso, tipo_falta, fecha_desde, fecha_hasta (YYYY-MM-DD).

    colegio_id opcional: si se pasa, se usa como tenant (prioridad sobre usuario["colegio_id"]).
    Si no se pasa, usuario debe incluir colegio_id entero ya resuelto (p. ej. tras resolve_colegio_id).
    """
    try:
        anio = int(anio)
    except (TypeError, ValueError):
        anio = datetime.now().year
    filtros = filtros or {}
    p = ph()
    _err = "colegio_id no resuelto en el usuario. Usa resolve_colegio_id() antes de llamar fq()."
    cid = colegio_id if colegio_id is not None else usuario.get("colegio_id")
    if cid is None or cid == "":
        raise ValueError(_err)
    try:
        cid = int(cid)
    except (TypeError, ValueError):
        raise ValueError(_err)
    if cid <= 0:
        raise ValueError(_err)
    params = [cid, anio]
    q = f"SELECT f.* FROM faltas f WHERE f.colegio_id={p} AND f.anio={p}"
    if usuario["rol"] == "Director":
        q += f" AND (f.curso={p} OR f.docente={p})"
        params += [usuario["curso"], usuario["nombre"]]
    elif usuario["rol"] == "Docente":
        q += f" AND f.docente={p}"
        params.append(usuario["nombre"])
    elif usuario["rol"] == "Acudiente":
        q += f" AND f.estudiante_id={p}"
        params.append(usuario["estudiante_id"])
    if filtros.get("curso"):
        q += f" AND f.curso = {p}"
        params.append(filtros["curso"])
    if filtros.get("tipo_falta") in ("Tipo I", "Tipo II", "Tipo III"):
        q += f" AND f.tipo_falta = {p}"
        params.append(filtros["tipo_falta"])
    if filtros.get("fecha_desde"):
        q += f" AND f.fecha >= {p}"
        params.append(filtros["fecha_desde"])
    if filtros.get("fecha_hasta"):
        q += f" AND f.fecha <= {p}"
        params.append(filtros["fecha_hasta"])
    return q + " ORDER BY f.fecha DESC, f.id DESC", params


def faltas_con_notas(conn, where_clause, params):
    if USE_PG:
        q = (
            f"SELECT f.*,STRING_AGG(a.rol||': '||a.texto,' | ') as notas "
            f"FROM faltas f LEFT JOIN anotaciones a ON a.falta_id=f.id "
            f"WHERE {where_clause} GROUP BY f.id ORDER BY f.estudiante,f.fecha"
        )
    else:
        q = (
            f"SELECT f.*,GROUP_CONCAT(a.rol||': '||a.texto,' | ') as notas "
            f"FROM faltas f LEFT JOIN anotaciones a ON a.falta_id=f.id "
            f"WHERE {where_clause} GROUP BY f.id ORDER BY f.estudiante,f.fecha"
        )
    return execute(conn, q, params, fetch="all")


def col_nom(colegio_id):
    conn = get_db()
    p = ph()
    c = execute(conn, f"SELECT nombre FROM colegios WHERE id={p}", (colegio_id or 1,), fetch="one")
    conn.close()
    return c["nombre"] if c else "Institución Educativa"
