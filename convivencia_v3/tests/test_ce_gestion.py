"""Tests unitarios del flujo de gestión disciplinar (sin BD)."""
from ce_gestion import enriquecer_falta_gestion, estado_gestion_falta, siguiente_rol_falta


def test_tipo_i_sin_anotaciones_siguiente_director():
    f = {"tipo_falta": "Tipo I", "gestion_coordinador": None}
    assert siguiente_rol_falta(f, []) == "Director"


def test_tipo_i_tras_director_none():
    f = {"tipo_falta": "Tipo I", "gestion_coordinador": None}
    a = [{"rol": "Docente"}, {"rol": "Director"}]
    assert siguiente_rol_falta(f, a) is None


def test_tipo_ii_flujo_docente_a_director():
    f = {"tipo_falta": "Tipo II", "gestion_coordinador": None}
    assert siguiente_rol_falta(f, []) == "Director"
    a1 = [{"rol": "Docente"}]
    assert siguiente_rol_falta(f, a1) == "Director"


def test_tipo_ii_tras_director_coordinador():
    f = {"tipo_falta": "Tipo II", "gestion_coordinador": None}
    a = [{"rol": "Docente"}, {"rol": "Director"}]
    assert siguiente_rol_falta(f, a) == "Coordinador"


def test_gestion_cerrada_por_columna():
    f = {"tipo_falta": "Tipo II", "gestion_coordinador": "cerrada"}
    assert estado_gestion_falta(f, []) == "cerrada"


def test_gestion_en_revision_por_columna():
    f = {"tipo_falta": "Tipo I", "gestion_coordinador": "en_revision"}
    assert estado_gestion_falta(f, []) == "en_revision"


def test_estado_pendiente_cuando_falta_director():
    f = {"tipo_falta": "Tipo I", "gestion_coordinador": None}
    assert estado_gestion_falta(f, []) == "pendiente"


def test_enriquecer_anade_campos():
    f = {"tipo_falta": "Tipo I", "gestion_coordinador": None, "anotaciones": []}
    enriquecer_falta_gestion(f)
    assert "siguiente_rol" in f and "estado_gestion" in f
    assert f["estado_gestion"] == "pendiente"
    assert f["siguiente_rol"] == "Director"
