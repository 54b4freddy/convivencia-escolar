"""Consultas reutilizadas por las rutas API (filtros por rol, agregación de notas)."""
from datetime import datetime

from ce_db import USE_PG, execute, get_db, ph


def fq(usuario, anio):
    """Query base de faltas según rol y año. Retorna (sql, params)."""
    try:
        anio = int(anio)
    except (TypeError, ValueError):
        anio = datetime.now().year
    p = ph()
    params = [usuario["colegio_id"] or 1, anio]
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
