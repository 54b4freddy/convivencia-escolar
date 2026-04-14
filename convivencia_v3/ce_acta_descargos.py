"""Acta de descargos (Ley 1620/2013): normalización de datos e integridad (hash + HMAC)."""
from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from typing import Any

ACTA_KEYS = (
    "informedado_hechos_si",
    "desea_version_si",
    "version_estudiante",
    "actitud",
    "consideracion_si",
    "consideracion_cual",
    "estudiante_se_nego_firmar",
    "constancia_negativa_firma",
    "estud_doc",
    "estud_nombre",
    "docente_doc",
    "docente_nombre",
    "fecha_acta",
    "hora_acta",
)


def _tri(v: Any) -> bool | None:
    if v is True or v is False:
        return v
    if v in (1, 0):
        return bool(v)
    s = str(v or "").strip().lower()
    if s in ("1", "true", "si", "sí", "yes"):
        return True
    if s in ("0", "false", "no"):
        return False
    if s == "" or s is None:
        return None
    return None


def normalize_acta_datos(raw: dict[str, Any] | None) -> dict[str, Any]:
    raw = raw or {}
    out: dict[str, Any] = {}
    for k in ACTA_KEYS:
        v = raw.get(k)
        if k in ("informedado_hechos_si", "desea_version_si"):
            out[k] = _tri(v)
        elif k in ("consideracion_si", "estudiante_se_nego_firmar"):
            tv = _tri(v)
            out[k] = False if tv is None else bool(tv)
        elif k == "actitud":
            av = (str(v or "")).strip().lower()
            out[k] = av if av in ("reconoce", "niega", "parcial", "no_pronuncia") else ""
        elif v is None:
            out[k] = ""
        else:
            out[k] = str(v).strip()
    return out


def _secret_bytes(secret_key: Any) -> bytes:
    if secret_key is None:
        return b"convivencia-insecure-dev"
    if isinstance(secret_key, str):
        return secret_key.encode("utf-8")
    if isinstance(secret_key, bytes):
        return secret_key
    return str(secret_key).encode("utf-8")


def integrity_payload(falta_id: int, colegio_id: int, datos: dict[str, Any]) -> bytes:
    wrap = {"falta_id": int(falta_id), "colegio_id": int(colegio_id), "datos": datos}
    return json.dumps(wrap, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def compute_content_hash(falta_id: int, colegio_id: int, datos: dict[str, Any]) -> str:
    return hashlib.sha256(integrity_payload(falta_id, colegio_id, datos)).hexdigest()


def compute_firma(secret_key: Any, content_hash_hex: str) -> str:
    return hmac.new(_secret_bytes(secret_key), content_hash_hex.encode("ascii"), hashlib.sha256).hexdigest()


def verify_integrity(secret_key: Any, falta_id: int, colegio_id: int, datos: dict[str, Any], content_hash: str, firma_hmac: str) -> bool:
    ch = compute_content_hash(falta_id, colegio_id, datos)
    if not hmac.compare_digest(ch, (content_hash or "").strip()):
        return False
    exp = compute_firma(secret_key, ch)
    return hmac.compare_digest(exp, (firma_hmac or "").strip())


def new_verification_token() -> str:
    return secrets.token_urlsafe(32)
