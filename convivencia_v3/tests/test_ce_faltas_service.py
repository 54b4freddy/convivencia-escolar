"""Tests de parseo de filtros para listado de faltas (sin HTTP)."""
from werkzeug.datastructures import ImmutableMultiDict

from ce_faltas_service import parse_filtros_faltas_args


def test_parse_vacio():
    assert parse_filtros_faltas_args(ImmutableMultiDict()) == {}


def test_parse_curso_y_tipo():
    args = ImmutableMultiDict([("curso", "10A"), ("tipo_falta", "Tipo II")])
    assert parse_filtros_faltas_args(args) == {"curso": "10A", "tipo_falta": "Tipo II"}


def test_parse_fechas_validas():
    args = ImmutableMultiDict([("fecha_desde", "2025-01-15"), ("fecha_hasta", "2025-06-30")])
    assert parse_filtros_faltas_args(args) == {"fecha_desde": "2025-01-15", "fecha_hasta": "2025-06-30"}


def test_parse_fecha_invalida_ignorada():
    args = ImmutableMultiDict([("fecha_desde", "15-01-2025")])
    assert parse_filtros_faltas_args(args) == {}


def test_tipo_invalido_ignorado():
    args = ImmutableMultiDict([("tipo_falta", "Tipo IV")])
    assert parse_filtros_faltas_args(args) == {}
