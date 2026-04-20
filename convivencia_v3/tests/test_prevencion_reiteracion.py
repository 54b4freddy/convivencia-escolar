from datetime import date, timedelta


def _login(client, usuario, contrasena):
    rv = client.post("/api/login", json={"usuario": usuario, "contrasena": contrasena})
    assert rv.status_code == 200, rv.get_json()
    return rv.get_json()


def test_prevencion_reiteracion_requires_auth(client):
    hoy = date.today().isoformat()
    rv = client.get(f"/api/prevencion/reiteracion?desde={hoy}&hasta={hoy}")
    assert rv.status_code in (302, 401, 403)


def test_prevencion_reiteracion_ok(client):
    _login(client, "admin", "admin123")
    hoy = date.today().isoformat()
    desde = (date.today() - timedelta(days=30)).isoformat()
    rv = client.get(f"/api/prevencion/reiteracion?desde={desde}&hasta={hoy}")
    assert rv.status_code == 200, rv.get_json()
    j = rv.get_json()
    assert "rank_ausencias" in j
    assert "rank_tipoI" in j
    assert "rank_lugares" in j
    assert "rank_victimas" in j
    assert len(j.get("rank_tipoI") or []) >= 1
    assert len(j.get("rank_lugares") or []) >= 1
    assert len(j.get("rank_ausencias") or []) >= 1
    assert len(j.get("rank_victimas") or []) >= 1


def test_prevencion_reiteracion_detalle_ok(client):
    _login(client, "admin", "admin123")
    hoy = date.today().isoformat()
    desde = (date.today() - timedelta(days=30)).isoformat()
    rv = client.get(f"/api/prevencion/reiteracion/detalle?desde={desde}&hasta={hoy}&kind=lugar&lugar=Patio")
    assert rv.status_code == 200, rv.get_json()
    j = rv.get_json()
    assert "items" in j
    assert len(j.get("items") or []) >= 1


def test_prevencion_reiteracion_mt_superadmin(client):
    _login(client, "superadmin", "super123")
    hoy = date.today().isoformat()
    desde = (date.today() - timedelta(days=30)).isoformat()
    rv = client.get(f"/api/prevencion/reiteracion-mt?desde={desde}&hasta={hoy}")
    assert rv.status_code == 200, rv.get_json()
    j = rv.get_json()
    assert "instituciones" in j
    assert len(j.get("instituciones") or []) >= 1
    first = j["instituciones"][0]
    assert "colegio_id" in first and "nombre" in first
    assert "rank_ausencias" in first and "rank_victimas" in first


def test_prevencion_reiteracion_mt_denied_coordinador(client):
    _login(client, "admin", "admin123")
    hoy = date.today().isoformat()
    desde = (date.today() - timedelta(days=30)).isoformat()
    rv = client.get(f"/api/prevencion/reiteracion-mt?desde={desde}&hasta={hoy}")
    assert rv.status_code == 403


def test_prevencion_detalle_superadmin_colegio_query(client):
    _login(client, "superadmin", "super123")
    hoy = date.today().isoformat()
    desde = (date.today() - timedelta(days=30)).isoformat()
    rv = client.get(
        f"/api/prevencion/reiteracion/detalle?desde={desde}&hasta={hoy}&kind=lugar&lugar=Patio&colegio_id=1"
    )
    assert rv.status_code == 200, rv.get_json()
    assert len(rv.get_json().get("items") or []) >= 1

