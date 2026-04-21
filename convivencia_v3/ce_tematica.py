"""
Dimensión temática del manual de convivencia (alineada a catálogo por colegio).
Inferencia automática por palabras clave en la descripción — revisable en catálogo.
"""
from __future__ import annotations

import re
import unicodedata

# Etiquetas canónicas (deben coincidir con UI / importación opcional CSV).
TEMATICAS: tuple[str, ...] = (
    "Relaciones Respetuosas",
    "Normas de convivencia",
    "Gestión Emocional",
    "Ambiente Físico y seguro",
    "Participación activa",
    "Prevención de conflictos",
)

_DEFAULT = "Normas de convivencia"

# (temática, lista de fragmentos a buscar en texto normalizado)
_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "Relaciones Respetuosas",
        (
            "acoso",
            "bullying",
            "calumni",
            "difam",
            "insult",
            "irrespet",
            "soez",
            "vocabular inadec",
            "discrimin",
            "genero",
            "género",
            "orientacion sexual",
            "religion",
            "religión",
            "abuso sexual",
            "acos",
            "pareja",
            "afectiv",
            "pornograf",
            "material porn",
        ),
    ),
    (
        "Gestión Emocional",
        (
            "grito",
            "grita",
            "voz alt",
            "tono alt",
            "emocional",
            "ansiedad",
            "estres",
            "estrés",
            "llanto",
            "bienestar",
            "suicid",
            "autoles",
            "capacidad",
            "violencia con incapac",
        ),
    ),
    (
        "Ambiente Físico y seguro",
        (
            "medicament",
            "prescripcion",
            "prescripción",
            "basura",
            "sucio",
            "aseo",
            "laboratorio",
            "biene",
            "daño",
            "dano",
            "perdida",
            "pérdida",
            "vape",
            "vaporiz",
            "fumar",
            "cigar",
            "sustancia",
            "psicoactiv",
            "deton",
            "inflam",
            "polvor",
            "maicena",
            "celebracion",
            "integridad",
            "arma",
            "portar ar",
        ),
    ),
    (
        "Participación activa",
        (
            "implemento",
            "tarea",
            "curricular",
            "extracurricular",
            "plagio",
            "falsific",
            "documento ofic",
            "rifa",
            "lucrativ",
            "evaluacion",
            "evaluación",
            "entrega",
            "comunicado",
            "citacion",
            "citación",
            "incumplimiento",
        ),
    ),
    (
        "Prevención de conflictos",
        (
            "pelea",
            "conflict",
            "agresion",
            "agresión",
            "ciberacos",
            "ciberacoso",
            "redes soc",
            "whatsapp",
            "delito",
            "homicid",
            "extorsion",
            "extorsión",
            "secuest",
            "juego brus",
            "azar",
            "apuesta",
            "desorden",
            "provoc",
            "incit",
        ),
    ),
    (
        "Normas de convivencia",
        (
            "uniforme",
            "celular",
            "dispositiv",
            "llegada tarde",
            "tarde",
            "ausent",
            "evasion",
            "evasión",
            "ingreso",
            "autoriz",
            "dependenc",
            "biciclet",
            "maquillaje",
            "chicle",
            "alimento",
            "clase",
            "aula",
            "formacion",
            "acto",
            "permanec",
            "jornada",
            "horario",
            "lugar no autor",
        ),
    ),
)


def _norm(s: str) -> str:
    if not s:
        return ""
    t = unicodedata.normalize("NFKD", s)
    t = "".join(c for c in t if not unicodedata.combining(c))
    return t.lower()


def infer_tematica(descripcion: str) -> str:
    """
    Sugiere una temática a partir del texto (título o descripción del ítem de catálogo).
    Heurística por palabras clave; si hay empate gana la regla con más coincidencias.
    """
    t = _norm(descripcion)
    if not t.strip():
        return _DEFAULT
    scores: dict[str, int] = {k: 0 for k in TEMATICAS}
    for tem, kws in _RULES:
        for kw in kws:
            if kw in t:
                scores[tem] += 1
    best = max(scores.values())
    if best == 0:
        return _DEFAULT
    # Desempate estable: orden en TEMATICAS
    for k in TEMATICAS:
        if scores.get(k, 0) == best:
            return k
    return _DEFAULT


def tematica_valida(val: str) -> bool:
    v = (val or "").strip()
    return v in TEMATICAS
