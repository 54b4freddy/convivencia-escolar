"""Promoción: crear y listar actividades."""


def _login(client, usuario, contrasena):
    rv = client.post("/api/login", json={"usuario": usuario, "contrasena": contrasena})
    assert rv.status_code == 200


def test_promocion_crear_y_listar(client):
    _login(client, "admin", "admin123")
    data = {
        "titulo": "Taller convivencia",
        "tema": "gestion_emocional",
        "fecha": "2026-04-15",
        "lugar": "Biblioteca",
        "recursos": "Proyector",
        "descripcion": "Actividad de promoción",
        "publico_tipo": "curso",
        "publico_curso": "6A",
    }
    rv = client.post("/api/promocion/actividades", data=data, content_type="multipart/form-data")
    assert rv.status_code == 200, rv.get_json()
    assert rv.get_json().get("ok") is True
    aid = rv.get_json().get("id")
    assert aid

    lst = client.get("/api/promocion/actividades").get_json()
    assert isinstance(lst, list)
    assert any(x.get("titulo") == "Taller convivencia" for x in lst)

    # A) editar
    rv2 = client.patch(
        f"/api/promocion/actividades/{aid}",
        json={
            "titulo": "Taller convivencia (editado)",
            "tema": "gestion_emocional",
            "fecha": "2026-04-16",
            "lugar": "Auditorio",
            "recursos": "Parlante",
            "descripcion": "Actividad editada",
            "publico_tipo": "colegio",
            "publico_curso": "",
            "publico_json": "",
        },
    )
    assert rv2.status_code == 200, rv2.get_json()
    assert rv2.get_json().get("ok") is True

    row = client.get(f"/api/promocion/actividades/{aid}").get_json()
    assert row.get("titulo") == "Taller convivencia (editado)"

    # C) filtros
    f1 = client.get("/api/promocion/actividades?tema=gestion_emocional").get_json()
    assert isinstance(f1, list)
    assert any(x.get("id") == aid for x in f1)

    f2 = client.get("/api/promocion/actividades?desde=2026-04-16&hasta=2026-04-16").get_json()
    assert any(x.get("id") == aid for x in f2)


def test_promocion_focos_calor(client):
    _login(client, "admin", "admin123")
    rv = client.get("/api/promocion/focos-calor?dias=30")
    assert rv.status_code == 200
    j = rv.get_json()
    assert "filas" in j and "desde" in j and "hasta" in j
    assert isinstance(j["filas"], list)
    assert "max_total" in j


