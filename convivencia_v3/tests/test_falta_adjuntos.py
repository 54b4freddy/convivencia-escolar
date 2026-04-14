"""Adjuntos de falta (acta descargos / sesión) y plantillas PDF vacías."""

from io import BytesIO


def _login(client, usuario, contrasena):
    rv = client.post("/api/login", json={"usuario": usuario, "contrasena": contrasena})
    assert rv.status_code == 200, rv.get_json()
    return rv.get_json()


def test_plantilla_acta_descargos_pdf(client):
    _login(client, "admin", "admin123")
    rv = client.get("/api/pdf/plantilla/acta-descargos")
    assert rv.status_code == 200
    assert rv.mimetype == "application/pdf"
    assert rv.data[:4] == b"%PDF"


def test_plantilla_acta_sesion_pdf(client):
    _login(client, "admin", "admin123")
    rv = client.get("/api/pdf/plantilla/acta-sesion")
    assert rv.status_code == 200
    assert rv.mimetype == "application/pdf"


def test_falta_adjunto_subir_listar_descargar(client):
    _login(client, "docente1", "doc123")
    from datetime import datetime

    y = datetime.now().year
    rv = client.get(f"/api/faltas?anio={y}")
    assert rv.status_code == 200
    faltas = rv.get_json()
    fid = next(f["id"] for f in faltas if f.get("docente") == "María Docente")
    data = {
        "categoria": "descargos_inicial",
        "archivo": (BytesIO(b"%PDF-1.4\n1 0 obj<<>>endobj trailer<<>>"), "prueba_acta.pdf"),
    }
    rv2 = client.post(f"/api/faltas/{fid}/adjuntos", data=data, content_type="multipart/form-data")
    assert rv2.status_code == 200, rv2.get_json()
    assert rv2.get_json().get("ok") is True
    adj = rv2.get_json().get("adjuntos") or []
    assert len(adj) >= 1
    aid = adj[-1]["id"]

    rv3 = client.get(f"/api/faltas/{fid}")
    det = rv3.get_json()
    assert any(a.get("id") == aid for a in (det.get("adjuntos") or []))

    rv4 = client.get(f"/api/faltas/{fid}/adjuntos/{aid}")
    assert rv4.status_code == 200
    assert "attachment" in (rv4.headers.get("Content-Disposition") or "").lower()


def test_coordinador_adjunto_sesion(client):
    _login(client, "admin", "admin123")
    from datetime import datetime

    y = datetime.now().year
    rv = client.get(f"/api/faltas?anio={y}")
    fid = rv.get_json()[0]["id"]
    data = {
        "categoria": "sesion_instancias",
        "archivo": (BytesIO(b"hello"), "notas.docx"),
    }
    rv2 = client.post(f"/api/faltas/{fid}/adjuntos", data=data, content_type="multipart/form-data")
    assert rv2.status_code == 200, rv2.get_json()
