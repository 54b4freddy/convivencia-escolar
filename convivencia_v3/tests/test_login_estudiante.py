"""Login estudiante: documento + clave; colegio_id solo si hay ambigüedad."""


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
    eid = None
    for row in est:
        d = (row.get("documento_identidad") or "").strip()
        if len(d) >= 5:
            doc = d
            eid = row["id"]
            break
    assert doc and eid, "seed estudiante con documento"
    # Asegura contraseña por defecto (últimos 4 dígitos) aunque el estudiante venga de importación.
    rv = client.post(f"/api/estudiantes/{eid}/reset-clave-portal", json={})
    assert rv.status_code == 200, rv.get_json()
    _logout(client)

    bad = _login(client, doc, "mala", colegio_id=1)
    assert bad.status_code == 401

    clave_def = doc[-4:]
    ok = _login(client, doc, clave_def, colegio_id=1)
    assert ok.status_code == 200
    j = ok.get_json()
    assert j.get("ok") is True
    assert j.get("usuario", {}).get("rol") == "Estudiante"
    assert j.get("usuario", {}).get("estudiante_id") == eid
    assert j.get("sugerir_cambio_clave_estudiante") is True
    _logout(client)

    ok_sin_col = _login(client, doc, clave_def)
    assert ok_sin_col.status_code == 200
    assert ok_sin_col.get_json().get("usuario", {}).get("estudiante_id") == eid
    _logout(client)


def test_login_docente_no_afectado_por_rama_estudiante(client):
    rv = _login(client, "docente1", "doc123")
    assert rv.status_code == 200
    assert rv.get_json().get("usuario", {}).get("rol") == "Docente"


def test_estudiante_desambigua_por_nombre_institucion(client):
    """Mismo documento en dos colegios: nombre de la I.E. acota el login."""
    _login(client, "admin", "admin123")
    est = client.get("/api/estudiantes").get_json()
    row0 = next(x for x in est if len((x.get("documento_identidad") or "").strip()) >= 5)
    doc = row0["documento_identidad"].strip()
    eid_a = row0["id"]
    cur_a = row0["curso"]

    _logout(client)
    _login(client, "superadmin", "super123")
    rv_col = client.post(
        "/api/colegios",
        json={
            "nombre": "IE Pablo Vi Puerto Triunfo Test",
            "nit": "",
            "municipio": "",
            "rector": "",
            "direccion": "",
            "telefono": "",
            "email": "",
        },
    )
    assert rv_col.status_code == 200, rv_col.get_json()
    cols = client.get("/api/colegios").get_json()
    cid_b = next(c["id"] for c in cols if c.get("nombre") == "IE Pablo Vi Puerto Triunfo Test")

    rv_e2 = client.post(
        "/api/estudiantes",
        json={
            "colegio_id": cid_b,
            "curso": "8A",
            "tipo_doc_est": "CC",
            "documento_identidad": doc,
            "apellido1_est": "Otro",
            "nombre1_est": "Colegio",
            "barreras": "Ninguna identificada",
            "tipo_doc_acu": "CC",
            "apellido1_acu": "Acu",
            "nombre1_acu": "Tutor",
            "parentesco_acu": "Tutor",
            "cedula_acudiente": "99888777666",
            "telefono": "3001112233",
            "direccion": "Dir",
            "clave_estudiante": "dupclave1",
        },
    )
    assert rv_e2.status_code == 200, rv_e2.get_json()
    _logout(client)

    _login(client, "admin", "admin123")
    rv_pa = client.patch(
        f"/api/estudiantes/{eid_a}",
        json={
            "curso": cur_a,
            "tipo_doc_est": "CC",
            "documento_identidad": doc,
            "apellido1_est": row0.get("apellido1_est") or "Pérez",
            "nombre1_est": row0.get("nombre1_est") or "Uno",
            "apellido1_acu": "García",
            "nombre1_acu": "Acudiente",
            "parentesco_acu": "Madre",
            "cedula_acudiente": "12345678901",
            "telefono": "3001234567",
            "direccion": "Calle 1",
            "barreras": "Ninguna identificada",
            "clave_estudiante": "dupclave1",
        },
    )
    assert rv_pa.status_code == 200, rv_pa.get_json()
    _logout(client)

    amb = client.post("/api/login", json={"usuario": doc, "contrasena": "dupclave1"})
    assert amb.status_code == 401
    jamb = amb.get_json()
    assert jamb.get("need_institucion") is True

    ok_sj = client.post(
        "/api/login",
        json={"usuario": doc, "contrasena": "dupclave1", "colegio_nombre": "San José"},
    )
    assert ok_sj.status_code == 200
    assert ok_sj.get_json().get("usuario", {}).get("colegio_id") == 1

    _logout(client)

    ok_pb = client.post(
        "/api/login",
        json={"usuario": doc, "contrasena": "dupclave1", "colegio_nombre": "Pablo Vi Puerto"},
    )
    assert ok_pb.status_code == 200
    assert ok_pb.get_json().get("usuario", {}).get("colegio_id") == cid_b

    _logout(client)

    bad = client.post(
        "/api/login",
        json={"usuario": doc, "contrasena": "dupclave1", "colegio_nombre": "Instituto Inexistente XYZ"},
    )
    assert bad.status_code == 401
    assert bad.get_json().get("need_institucion") is True


def test_reset_clave_portal_estudiante(client):
    _login(client, "admin", "admin123")
    est = client.get("/api/estudiantes").get_json()
    eid = est[0]["id"]
    rv = client.post(f"/api/estudiantes/{eid}/reset-clave-portal", json={})
    assert rv.status_code == 200
    assert rv.get_json().get("ok") is True


def test_cambiar_clave_estudiante_me(client):
    _login(client, "admin", "admin123")
    est = client.get("/api/estudiantes").get_json()
    row = next(x for x in est if len((x.get("documento_identidad") or "").strip()) >= 5)
    doc = row["documento_identidad"].strip()
    eid = row["id"]
    cur = row["curso"]
    rv = client.patch(
        f"/api/estudiantes/{eid}",
        json={
            "curso": cur,
            "tipo_doc_est": "CC",
            "documento_identidad": doc,
            "apellido1_est": row.get("apellido1_est") or "Pérez",
            "nombre1_est": row.get("nombre1_est") or "Test",
            "apellido1_acu": "García",
            "nombre1_acu": "Acudiente",
            "parentesco_acu": "Madre",
            "cedula_acudiente": "12345678901",
            "telefono": "3001234567",
            "direccion": "Calle 1",
            "barreras": "Ninguna identificada",
            "clave_estudiante": "miClaveNueva9",
        },
    )
    assert rv.status_code == 200, rv.get_json()
    _logout(client)

    _login(client, doc, "miClaveNueva9")
    rv2 = client.post(
        "/api/me/cambiar-clave-estudiante",
        json={"contrasena_actual": "miClaveNueva9", "contrasena_nueva": "otraMas123"},
    )
    assert rv2.status_code == 200, rv2.get_json()
    _logout(client)
    ok = client.post("/api/login", json={"usuario": doc, "contrasena": "otraMas123"})
    assert ok.status_code == 200


def test_import_estudiante_clave_portal_columna_opcional(client):
    """Carga masiva extendida: columna 18 opcional fija la contraseña del portal estudiante."""
    _login(client, "admin", "admin123")
    doc = "9988776655443"
    line = (
        "CC,"
        + doc
        + ",ImpZ,ZZ,Alum,Test,6A,Ninguna identificada,"
        "CC,11122233344,Garcia,Lopez,Papa,,Padre,3001112233,Calle 1,ClaveImp99"
    )
    rv = client.post("/api/estudiantes/importar", json={"texto": line, "curso_default": ""})
    assert rv.status_code == 200, rv.get_json()
    assert rv.get_json().get("insertados") == 1
    _logout(client)
    ok = _login(client, doc, "ClaveImp99", colegio_id=1)
    assert ok.status_code == 200
    assert ok.get_json().get("usuario", {}).get("rol") == "Estudiante"


def test_plantilla_importacion_estudiantes_csv(client):
    _login(client, "admin", "admin123")
    rv = client.get("/api/estudiantes/plantilla-importacion")
    assert rv.status_code == 200
    assert b"tipo_doc_est" in rv.data
    assert b"documento_est" in rv.data


def test_import_estudiantes_bom_y_fila_encabezado(client):
    """UTF-8 BOM + primera fila de títulos (export Excel)."""
    _login(client, "admin", "admin123")
    doc = "8877665544332"
    block = (
        "\ufefftipo_doc_est,documento_est,apellido1,apellido2,nombre1,nombre2,curso,barreras,"
        "tipo_doc_acu,documento_acu,apellido1_acu,apellido2_acu,nombre1_acu,nombre2_acu,parentesco,telefono,direccion\n"
        f"CC,{doc},Bo,Z,Uno,Dos,6B,Ninguna identificada,CC,11122233344,Acu,Lo,No,Mb,Madre,300,\n"
    )
    rv = client.post("/api/estudiantes/importar", json={"texto": block, "curso_default": ""})
    assert rv.status_code == 200, rv.get_json()
    assert rv.get_json().get("insertados") == 1
    _logout(client)


def test_import_estudiantes_campo_con_coma_entre_comillas(client):
    _login(client, "admin", "admin123")
    doc = "7766554433221"
    line = (
        "CC,"
        + doc
        + ",Bo,Z,Uno,Dos,6B,Ninguna identificada,"
        'CC,11122233344,Acu,Lo,No,Mb,Madre,300,"Calle 10, 5-20"\n'
    )
    rv = client.post("/api/estudiantes/importar", json={"texto": line, "curso_default": ""})
    assert rv.status_code == 200, rv.get_json()
    assert rv.get_json().get("insertados") == 1
    _logout(client)
