"""Multi-colegio: resolve_colegio_id, superadmin sin colegio en sesión, alcance Coordinador."""

import pytest

from app import app as flask_app


def _login(client, usuario, contrasena):
    rv = client.post("/api/login", json={"usuario": usuario, "contrasena": contrasena})
    assert rv.status_code == 200, rv.get_json()
    return rv.get_json()


@pytest.mark.parametrize(
    "user,path,method,expected_cid,expect_err",
    [
        ({"rol": "Coordinador", "colegio_id": 5}, "/", "GET", 5, None),
        ({"rol": "Docente", "colegio_id": None}, "/", "GET", 1, None),
        ({"rol": "Superadmin", "colegio_id": 9}, "/", "GET", 9, None),
    ],
)
def test_resolve_colegio_id_sin_request_superadmin_o_coordinador(user, path, method, expected_cid, expect_err):
    with flask_app.test_request_context(path, method=method):
        from routes.authz import resolve_colegio_id

        cid, err = resolve_colegio_id(user)
        assert err == expect_err
        assert cid == expected_cid


def test_resolve_superadmin_sin_colegio_get_sin_param():
    with flask_app.test_request_context("/", method="GET"):
        from routes.authz import resolve_colegio_id

        cid, err = resolve_colegio_id({"rol": "Superadmin", "colegio_id": None})
        assert cid is None
        assert err == "Para Superadmin, envíe colegio_id"


def test_resolve_superadmin_sin_colegio_get_con_query():
    with flask_app.test_request_context("/?colegio_id=1", method="GET"):
        from routes.authz import resolve_colegio_id

        cid, err = resolve_colegio_id({"rol": "Superadmin", "colegio_id": None})
        assert err is None
        assert cid == 1


def test_resolve_superadmin_json_body():
    with flask_app.test_request_context(
        "/api/x",
        method="POST",
        json={"colegio_id": 2},
        content_type="application/json",
    ):
        from routes.authz import resolve_colegio_id

        cid, err = resolve_colegio_id({"rol": "Superadmin", "colegio_id": None})
        assert err is None
        assert cid == 2


def test_reportes_superadmin_sin_colegio_400(client):
    _login(client, "superadmin", "super123")
    rv = client.get("/api/reportes?anio=2026")
    assert rv.status_code == 400
    assert "colegio_id" in (rv.get_json() or {}).get("error", "").lower()


def test_reportes_superadmin_con_colegio_query_200(client):
    _login(client, "superadmin", "super123")
    rv = client.get("/api/reportes?anio=2026&colegio_id=1")
    assert rv.status_code == 200
    data = rv.get_json()
    assert "total" in data


def test_coordinador_no_patch_usuario_otro_colegio(client):
    _login(client, "superadmin", "super123")
    rv_col = client.post(
        "/api/colegios",
        json={
            "nombre": "IE Test Multitenant",
            "nit": "",
            "municipio": "",
            "rector": "",
            "direccion": "",
            "telefono": "",
            "email": "",
        },
    )
    assert rv_col.status_code == 200
    rv_list = client.get("/api/colegios")
    cols = rv_list.get_json()
    col_b = next(c for c in cols if c.get("nombre") == "IE Test Multitenant")
    cid_b = col_b["id"]

    rv_u = client.post(
        "/api/usuarios",
        json={
            "usuario": "docente_otro_col",
            "contrasena": "secreta1",
            "rol": "Docente",
            "colegio_id": cid_b,
            "apellido1": "Otro",
            "nombre1": "Colegio",
        },
    )
    assert rv_u.status_code == 200, rv_u.get_json()

    rv_all = client.get("/api/usuarios")
    users = rv_all.get_json()
    uid = next(u["id"] for u in users if u.get("usuario") == "docente_otro_col")

    _login(client, "admin", "admin123")
    rv_patch = client.patch(
        f"/api/usuarios/{uid}",
        json={
            "rol": "Docente",
            "nombre": "Nombre",
            "apellido1": "Otro",
            "nombre1": "Hackeo",
            "apellido2": "",
            "nombre2": "",
            "curso": "",
            "asignatura": "",
            "tipo_doc": "",
            "documento_personal": "",
            "telefono": "",
        },
    )
    assert rv_patch.status_code == 403
