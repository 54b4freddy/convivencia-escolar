"""
Estado de gestión disciplinar: deriva el siguiente rol en el flujo y el estado (pendiente / en_revisión / cerrada).
Alineado con inicioNextRole en static/app.js.
"""


def siguiente_rol_falta(f, anotaciones):
    """Quién debe actuar a continuación, o None si el flujo automático ya no exige otro paso."""
    t = f.get("tipo_falta") or ""
    T23 = t in ("Tipo II", "Tipo III")
    a = anotaciones or []
    if not a:
        return "Director"
    last = (a[-1] or {}).get("rol")
    if last == "Docente":
        if T23 and len(a) >= 2 and (a[-2] or {}).get("rol") == "Orientador":
            return None
        return "Director"
    if last == "Director":
        return "Coordinador" if T23 else None
    if last == "Coordinador":
        return "Orientador" if T23 else None
    if last == "Orientador":
        return "Docente" if T23 else None
    return None


def estado_gestion_falta(f, anotaciones):
    """
    - cerrada / en_revision: decisión explícita del coordinador (columna gestion_coordinador).
    - Si no hay decisión: pendiente si aún corresponde un rol; en_revision si el flujo ya no exige paso pero no está cerrada.
    """
    dec = (f.get("gestion_coordinador") or "").strip() or None
    if dec == "cerrada":
        return "cerrada"
    if dec == "en_revision":
        return "en_revision"
    sig = siguiente_rol_falta(f, anotaciones)
    if sig is not None:
        return "pendiente"
    return "en_revision"


def enriquecer_falta_gestion(f):
    """Añade estado_gestion y siguiente_rol al dict de falta (tras cargar anotaciones)."""
    anots = f.get("anotaciones") or []
    f["siguiente_rol"] = siguiente_rol_falta(f, anots)
    f["estado_gestion"] = estado_gestion_falta(f, anots)
    return f
