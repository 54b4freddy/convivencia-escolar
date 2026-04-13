"""Smoke tests HTTP del blueprint de faltas (sesión)."""


def test_api_faltas_sin_sesion_401(client):
    rv = client.get("/api/faltas?anio=2025")
    assert rv.status_code == 401
    data = rv.get_json()
    assert data.get("error")


def test_api_falta_detalle_sin_sesion_401(client):
    rv = client.get("/api/faltas/1")
    assert rv.status_code == 401
