"""Acudiente: estudiantes acotados, conductas de riesgo y anti‑abuso de recurrencia."""


def _login(client, usuario, contrasena):
    rv = client.post("/api/login", json={"usuario": usuario, "contrasena": contrasena})
    assert rv.status_code == 200, rv.get_json()
    return rv.get_json()


def test_acudiente_get_senales_403(client):
    _login(client, "1234567", "1234567")
    rv = client.get("/api/senales-atencion")
    assert rv.status_code == 403


def test_acudiente_estudiantes_solo_su_hijo(client):
    _login(client, "1234567", "1234567")
    rv = client.get("/api/estudiantes")
    assert rv.status_code == 200
    rows = rv.get_json()
    assert isinstance(rows, list) and len(rows) == 1
    assert rows[0].get("nombre") == "Alejandro Pérez"


def test_acudiente_post_senal_otro_estudiante_403(client):
    _login(client, "1234567", "1234567")
    rv = client.post(
        "/api/senales-atencion",
        json={
            "estudiante_id": 99,
            "tipo_conducta": "conv_i",
            "subtipo": "conflictos_manejables",
            "urgencia": "moderada",
            "descripcion_objetiva": "Descripción objetiva con suficiente texto.",
        },
    )
    assert rv.status_code == 403


def test_acudiente_recurrencia_conducta_400(client):
    _login(client, "admin", "admin123")
    body = {
        "estudiante_id": 1,
        "tipo_conducta": "conv_i",
        "subtipo": "conflictos_manejables",
        "urgencia": "moderada",
        "descripcion_objetiva": "Descripción objetiva con suficiente texto.",
    }
    for _ in range(3):
        rv = client.post("/api/senales-atencion", json=body)
        assert rv.status_code == 200, rv.get_json()

    _login(client, "1234567", "1234567")
    rv4 = client.post("/api/senales-atencion", json=body)
    assert rv4.status_code == 400
    assert "recurrencia" in (rv4.get_json() or {}).get("error", "").lower()


def test_acudiente_json_categoria_legacy_403(client):
    _login(client, "1234567", "1234567")
    rv = client.post(
        "/api/senales-atencion",
        json={
            "estudiante_id": 1,
            "categoria": "alimentacion",
            "observacion": "Observación con más de diez caracteres para validar.",
        },
    )
    assert rv.status_code == 403
