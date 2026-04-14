"""Acta de descargos: persistencia, firma y verificación pública."""

from datetime import datetime


def _login(client, usuario, contrasena):
    rv = client.post("/api/login", json={"usuario": usuario, "contrasena": contrasena})
    assert rv.status_code == 200, rv.get_json()
    return rv.get_json()


def test_verificar_descargos_token_corto_400(client):
    rv = client.get("/api/verificar-descargos/abc")
    assert rv.status_code == 400


def test_acta_descargos_put_get_y_verificacion_publica(client):
    _login(client, "admin", "admin123")
    y = datetime.now().year
    rv = client.get(f"/api/faltas?anio={y}")
    assert rv.status_code == 200
    faltas = rv.get_json()
    assert isinstance(faltas, list) and faltas
    fid = faltas[0]["id"]
    datos = {
        "informedado_hechos_si": True,
        "desea_version_si": True,
        "version_estudiante": "Versión libre del estudiante (prueba).",
        "actitud": "parcial",
        "consideracion_si": False,
        "consideracion_cual": "",
        "estudiante_se_nego_firmar": False,
        "constancia_negativa_firma": "",
        "estud_nombre": "Estudiante prueba",
        "estud_doc": "123456",
        "docente_nombre": "Docente prueba",
        "docente_doc": "987654",
        "fecha_acta": "2026-04-10",
        "hora_acta": "10:30",
    }
    rv = client.put(f"/api/faltas/{fid}/acta-descargos", json={"datos": datos})
    assert rv.status_code == 200, rv.get_json()
    body = rv.get_json()
    assert body.get("ok") is True
    acta = body.get("acta_descargos") or {}
    token = acta.get("verificacion_token")
    assert token and len(token) > 12

    rv2 = client.get(f"/api/faltas/{fid}")
    assert rv2.status_code == 200
    det = rv2.get_json()
    assert det.get("acta_descargos") and det["acta_descargos"].get("verificacion_url")

    rv3 = client.get(f"/api/verificar-descargos/{token}")
    assert rv3.status_code == 200
    vj = rv3.get_json()
    assert vj.get("ok") is True
    assert vj.get("integridad") == "válida"
    assert vj.get("registro_falta_id") == fid
