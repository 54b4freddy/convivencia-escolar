"""Reportes ciudadanos estudiantiles (sin sesión) y bandeja del comité."""


def _login(client, usuario, contrasena):
    rv = client.post("/api/login", json={"usuario": usuario, "contrasena": contrasena})
    assert rv.status_code == 200
    assert rv.get_json().get("ok") is True


def _logout(client):
    client.post("/api/logout", json={})


def test_public_colegio_nombre(client):
    rv = client.get("/api/public/colegios/1")
    assert rv.status_code == 200
    j = rv.get_json()
    assert j.get("ok") is True
    assert j.get("nombre")


def test_reporte_requiere_identidad(client):
    rv = client.post(
        "/api/reportes-convivencia",
        json={
            "colegio_id": 1,
            "categoria_visual": "mal",
            "a_quien": "yo",
            "descripcion": "Necesito ayuda con algo que me preocupa.",
            "lugar_clave": "salon",
            "urgencia": "normal",
        },
    )
    assert rv.status_code == 400
    assert "Identifícate" in (rv.get_json() or {}).get("error", "")


def test_reporte_con_token_y_listado_comite(client):
    _login(client, "admin", "admin123")
    est_list = client.get("/api/estudiantes").get_json()
    assert isinstance(est_list, list) and est_list
    tok = (est_list[0].get("reporte_token") or "").strip()
    assert len(tok) > 8
    _logout(client)

    rv = client.post(
        "/api/reportes-convivencia",
        json={
            "colegio_id": 1,
            "token": tok,
            "categoria_visual": "molestan",
            "a_quien": "yo",
            "descripcion": "Un compañero me molesta en clase y no sé cómo decirlo.",
            "lugar_clave": "salon",
            "urgencia": "normal",
            "fue_hoy": "1",
        },
    )
    assert rv.status_code == 200
    j = rv.get_json()
    assert j.get("ok") is True
    assert j.get("id")
    assert "confiar" in (j.get("mensaje_confirmacion") or "").lower() or "Gracias" in (j.get("mensaje_confirmacion") or "")

    _login(client, "admin", "admin123")
    lst = client.get("/api/reportes-convivencia").get_json()
    assert isinstance(lst, list)
    assert any(x.get("descripcion", "").startswith("Un compañero") for x in lst)

    rid = j["id"]
    rv2 = client.patch(
        f"/api/reportes-convivencia/{rid}",
        json={"estado": "orientacion", "nota_comite": ""},
    )
    assert rv2.status_code == 200
    assert rv2.get_json().get("ok") is True


def test_descartar_requiere_nota(client):
    _login(client, "admin", "admin123")
    est_list = client.get("/api/estudiantes").get_json()
    tok = (est_list[0].get("reporte_token") or "").strip()
    _logout(client)
    rv = client.post(
        "/api/reportes-convivencia",
        json={
            "colegio_id": 1,
            "token": tok,
            "categoria_visual": "peligro",
            "a_quien": "grupo",
            "descripcion": "Prueba de descarte con nota obligatoria en el flujo.",
            "lugar_clave": "otro",
            "urgencia": "urgente",
        },
    )
    rid = rv.get_json()["id"]
    _login(client, "orientador1", "ori123")
    rv_bad = client.patch(f"/api/reportes-convivencia/{rid}", json={"estado": "descartado", "nota_comite": ""})
    assert rv_bad.status_code == 400
    rv_ok = client.patch(
        f"/api/reportes-convivencia/{rid}",
        json={"estado": "descartado", "nota_comite": "Prueba / falso positivo"},
    )
    assert rv_ok.status_code == 200
