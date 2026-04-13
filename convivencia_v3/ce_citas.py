"""Operaciones de citas con acudientes vinculadas a faltas."""
from datetime import datetime

from ce_db import execute, ph

CITA_ROLES_DESTINO = frozenset({"Coordinador", "Director", "Orientador", "Docente"})


def cancelar_citas_abiertas_por_falta(conn, falta_id):
    p = ph()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    execute(
        conn,
        f"UPDATE citas_acudiente SET estado='cancelada', actualizado_en={p} "
        f"WHERE falta_id={p} AND estado IN ('pendiente_agenda','pendiente_confirmacion_acudiente')",
        (now, falta_id),
    )


def insert_cita_escuela(conn, falta_id, colegio_id, fecha_hora, u):
    """Cita propuesta por la institución (fecha conocida), pendiente de confirmación del acudiente."""
    p = ph()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    execute(
        conn,
        f"INSERT INTO citas_acudiente (falta_id,colegio_id,origen,estado,rol_destino,fecha_hora,"
        f"creado_por_id,creado_por_nombre,creado_por_rol,agenda_por_id,agenda_por_nombre,creado_en,actualizado_en) "
        f"VALUES ({p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p})",
        (
            falta_id,
            colegio_id,
            "escuela",
            "pendiente_confirmacion_acudiente",
            "",
            fecha_hora,
            u.get("id"),
            (u.get("nombre") or "")[:200],
            (u.get("rol") or "")[:40],
            None,
            "",
            now,
            now,
        ),
    )
