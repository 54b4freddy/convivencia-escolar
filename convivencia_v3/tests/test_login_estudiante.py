"""Login estudiante: documento + clave + colegio_id."""


def _login(client, usuario, contrasena, colegio_id=None):
    body = {"usuario": usuario, "contrasena": contrasena}
    if colegio_id is not None:
        body["colegio_id"] = colegio_id
    return client.post("/api/login", json=body)


def _logout(client):
    client.post("/api/logout", json={})


def test_login_estudiante_documento_colegio(client):
    _login(client, "admin", "admin123")
    est = client.get("/api/estudiantes").get_json()
    doc = None
    for row in est:
        d = (row.get("documento_identidad") or "").strip()
        if len(d) >= 5:
            doc = d
            eid = row["id"]
            break
    assert doc, "seed estudiante con documento"
    rv = client.patch(
        f"/api/estudiantes/{eid}",
        json={
            "curso": next(r for r in est if r["id"] == eid)["curso"],
            "tipo_doc_est": "CC",
            "documento_identidad": doc,
            "apellido1_est": next(r for r in est if r["id"] == eid).get("apellido1_est") or "Pérez",
            "nombre1_est": next(r for r in est if r["id"] == eid).get("nombre1_est") or "Test",
            "apellido1_acu": "García",
            "nombre1_acu": "Acudiente",
            "parentesco_acu": "Madre",
            "cedula_acudiente": "12345678901",
            "telefono": "3001234567",
            "direccion": "Calle 1",
            "barreras": "Ninguna identificada",
            "clave_estudiante": "claveEst1",
        },
    )
    assert rv.status_code == 200, rv.get_json()
    _logout(client)

    bad = _login(client, doc, "mala", colegio_id=1)
    assert bad.status_code == 401

    ok = _login(client, doc, "claveEst1", colegio_id=1)
    assert ok.status_code == 200
    j = ok.get_json()
    assert j.get("ok") is True
    assert j.get("usuario", {}).get("rol") == "Estudiante"
    assert j.get("usuario", {}).get("estudiante_id") == eid

    _logout(client)


def test_login_docente_no_afectado_por_rama_estudiante(client):
    rv = _login(client, "docente1", "doc123")
    assert rv.status_code == 200
    assert rv.get_json().get("usuario", {}).get("rol") == "Docente"
