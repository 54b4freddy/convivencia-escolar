import hashlib
import re


def hpwd(p: str) -> str:
    return hashlib.sha256(str(p).encode()).hexdigest()


def solo_letras(s: str) -> str:
    s = re.sub(r"[^a-záéíóúüñA-ZÁÉÍÓÚÜÑ\s]", "", str(s).strip())
    return " ".join(w.capitalize() for w in s.split())


def solo_numeros(s: str) -> str:
    return re.sub(r"[^0-9]", "", str(s))


def clave_portal_estudiante_por_defecto(documento: str) -> str:
    """Contraseña inicial del portal estudiante: últimos 4 dígitos del documento (solo números)."""
    d = solo_numeros(str(documento or ""))
    if len(d) >= 4:
        return d[-4:]
    return d.zfill(4)[:4]


def fmt_tel(s: str) -> str:
    n = solo_numeros(s)
    return n if len(n) >= 7 else ""


def nombre_desde_partes(ap1: str, ap2: str, n1: str, n2: str) -> str:
    """Nombre completo legible a partir de apellidos y nombres (orden: apellidos primero)."""
    partes = []
    for p in (ap1, ap2, n1, n2):
        t = solo_letras(str(p or ""))
        if t:
            partes.append(t)
    return " ".join(partes) if partes else ""

