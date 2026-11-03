"""El reporte se regenera igual salvo la fecha, y con un ledger vacío deja los brazos pendientes sin fallar."""

import re

import pytest

from comun import brazos as reg
from comun import reporte, rutas

EXPERIMENTOS = [reg.CONTROL, *[e for e in reg.duenos() if e != reg.CONTROL], reg.AGREGADOR]


def sin_fecha(html: str) -> str:
    return re.sub(r"Generado \d{4}-\d\d-\d\d \d\d:\d\d", "Generado", html)


@pytest.mark.parametrize("exp", EXPERIMENTOS)
def test_dos_veces_da_lo_mismo(exp):
    assert sin_fecha(reporte.generar(exp)) == sin_fecha(reporte.generar(exp))


def test_agregador_lista_todos_los_brazos_de_las_hipotesis():
    ctx = reporte.Contexto(reg.AGREGADOR)
    esperados = {b.nombre for b in reg.BRAZOS.values() if b.dueno != reg.CONTROL}
    assert set(ctx.brazos) == esperados


def test_hipotesis_nueva_aparece_sin_tocar_el_generador(monkeypatch):
    nuevo = reg.Brazo("X1", "h1", "uniforme", 0.7, "U0.5")
    monkeypatch.setitem(reg.BRAZOS, "X1", nuevo)
    assert "X1" in reporte.Contexto(reg.AGREGADOR).brazos
    assert "X1" in reporte.generar(reg.AGREGADOR)


def test_ledger_vacio_deja_pendientes(monkeypatch, tmp_path):
    monkeypatch.setattr(rutas, "EXPERIMENTOS", tmp_path)
    for e in EXPERIMENTOS:
        (tmp_path / e / "ledger").mkdir(parents=True)
    html = reporte.generar("h1")
    assert "pendiente" in html and "<table>" in html
