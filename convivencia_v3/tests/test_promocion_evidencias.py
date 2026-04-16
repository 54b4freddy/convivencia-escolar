"""Promoción: evidencias múltiples por actividad."""

from io import BytesIO


def _login(client, usuario, contrasena):
    rv = client.post("/api/login", json={"usuario": usuario, "contrasena": contrasena})
    assert rv.status_code == 200


def test_promocion_evidencias_crud(client):
    _login(client, "admin", "admin123")
    rv = client.post(
        "/api/promocion/actividades",
        data={
            "titulo": "Actividad con evidencias",
            "tema": "normas_convivencia",
            "fecha": "2026-04-15",
            "publico_tipo": "colegio",
        },
        content_type="multipart/form-data",
    )
    aid = rv.get_json()["id"]

    # B) subir evidencia
    data = {
        "evidencia": (BytesIO(b"%PDF-1.4 test"), "evid.pdf"),
        "set_como_principal": "1",
    }
    rv2 = client.post(f"/api/promocion/actividades/{aid}/evidencias", data=data, content_type="multipart/form-data")
    assert rv2.status_code == 200, rv2.get_json()
    assert rv2.get_json().get("ok") is True

    lst = client.get(f"/api/promocion/actividades/{aid}/evidencias").get_json()
    assert isinstance(lst, list) and lst
    eid = lst[0]["id"]

    # descargar/abrir archivo
    rv3 = client.get(f"/api/promocion/evidencias/{eid}/file")
    assert rv3.status_code == 200

    # eliminar evidencia
    rv4 = client.delete(f"/api/promocion/evidencias/{eid}")
    assert rv4.status_code == 200
    assert rv4.get_json().get("ok") is True

