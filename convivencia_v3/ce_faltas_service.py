"""Listado y enriquecimiento de faltas (lógica reutilizable fuera de las rutas HTTP)."""
import re

from ce_db import execute, ph
from ce_gestion import enriquecer_falta_gestion
from ce_queries import fq

_FECHA_ISO_FALTAS = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def parse_filtros_faltas_args(args):
    """
    args: objeto tipo request.args con .get(key, default).
    Devuelve dict para fq(..., filtros). El caller debe pasar usuario con colegio_id resuelto.
    """
    curso = (args.get("curso") or "").strip()
    tipo_falta = (args.get("tipo_falta") or "").strip()
    fd = (args.get("fecha_desde") or "").strip()
    fh = (args.get("fecha_hasta") or "").strip()
    if fd and not _FECHA_ISO_FALTAS.match(fd):
        fd = ""
    if fh and not _FECHA_ISO_FALTAS.match(fh):
        fh = ""
    out = {}
    if curso:
        out["curso"] = curso
    if tipo_falta in ("Tipo I", "Tipo II", "Tipo III"):
        out["tipo_falta"] = tipo_falta
    if fd:
        out["fecha_desde"] = fd
    if fh:
        out["fecha_hasta"] = fh
    return out


def attach_cita_falta(conn, f):
    if not f or f.get("id") is None:
        return
    p = ph()
    c = execute(
        conn,
        f"SELECT * FROM citas_acudiente WHERE falta_id={p} ORDER BY id DESC LIMIT 1",
        (f["id"],),
        fetch="one",
    )
    f["cita_acudiente"] = c


def listar_faltas_enriquecidas(conn, usuario, anio, filtros_sql=None, estado_gestion=None):
    """
    Lista faltas según rol + filtros SQL opcionales; adjunta anotaciones, cita y estado_gestion.
    No cierra conn. estado_gestion: 'pendiente'|'en_revision'|'cerrada' o None.
    """
    q, params = fq(usuario, anio, filtros_sql)
    faltas = execute(conn, q, params, fetch="all")
    ph_ = ph()
    for f in faltas:
        f["anotaciones"] = execute(
            conn,
            f"SELECT * FROM anotaciones WHERE falta_id={ph_} ORDER BY id",
            (f["id"],),
            fetch="all",
        )
        attach_cita_falta(conn, f)
        enriquecer_falta_gestion(f)
    if estado_gestion:
        faltas = [f for f in faltas if f.get("estado_gestion") == estado_gestion]
    return faltas
