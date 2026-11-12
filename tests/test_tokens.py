"""`comun.tokens` con varios experimentos: dueño por declaración, sin dueño a sampling_1, doble declaración falla."""

import csv

import pytest

from comun import tokens

A = "11111111-1111-1111-1111-111111111111"
B = "22222222-2222-2222-2222-222222222222"
C = "33333333-3333-3333-3333-333333333333"
D = "44444444-4444-4444-4444-444444444444"


def _exp(raiz, nombre, bitacora="", costos=None):
    docs = raiz / "experimentos" / nombre / "docs"
    docs.mkdir(parents=True)
    (docs / "bitacora.md").write_text(bitacora)
    if costos:
        ses = raiz / "experimentos" / nombre / "ledger" / "sesiones"
        ses.mkdir(parents=True)
        (ses / "costos.csv").write_text(costos)


def _entrada(sesion, etapa):
    return f"### 2026-11-03 entrada\n\netapa: **{etapa}** · sesión `{sesion}`\n\n"


def _leer(raiz, nombre):
    with (raiz / "experimentos" / nombre / "ledger" / "tokens.csv").open() as f:
        return {f_["sesion"]: f_ for f_ in csv.DictReader(f)}


def test_cada_experimento_registra_lo_que_declara(tmp_path):
    _exp(tmp_path, "sampling_1")
    _exp(tmp_path, "h1", _entrada(A, "codigo"))
    _exp(tmp_path, "h2", _entrada(B, "diseno"))
    for e in ("sampling_1", "h1", "h2"):
        tokens.registrar(e, tmp_path, tmp_path / "proy")
    assert set(_leer(tmp_path, "h1")) == {A}
    assert set(_leer(tmp_path, "h2")) == {B}
    assert _leer(tmp_path, "h1")[A]["etapa"] == "codigo"


def test_sin_dueno_va_a_sampling_1(tmp_path):
    _exp(tmp_path, "sampling_1")
    _exp(tmp_path, "h1", _entrada(A, "codigo"))
    proy = tmp_path / "proy" / str(tmp_path).replace("/", "-").replace("_", "-").replace(".", "-")
    proy.mkdir(parents=True)
    for s in (A, C):
        (proy / f"{s}.jsonl").write_text("")
    tokens.registrar("sampling_1", tmp_path, tmp_path / "proy")
    tokens.registrar("h1", tmp_path, tmp_path / "proy")
    assert set(_leer(tmp_path, "sampling_1")) == {C}
    assert _leer(tmp_path, "sampling_1")[C]["etapa"] == "sin-etapa"
    assert set(_leer(tmp_path, "h1")) == {A}


def test_doble_declaracion_falla(tmp_path):
    _exp(tmp_path, "sampling_1")
    _exp(tmp_path, "h1", _entrada(A, "codigo"))
    _exp(tmp_path, "h2", _entrada(A, "diseno"))
    with pytest.raises(SystemExit, match=A):
        tokens.registrar("h1", tmp_path, tmp_path / "proy")


def test_etapa_headless_sale_del_cambio_y_del_grupo(tmp_path):
    costos = (
        "fecha,grupo,rol,modelo,turnos,costo_usd,sesion,resultado,codigo,cambio\n"
        f"2026-11-01T19:55,4,aplicar,m,1,0.5,{A},success,0,experimento-sampling-velocidad\n"
        f"2026-11-03T01:09,4,aplicar,m,1,0.5,{B},success,0,separar-hipotesis\n"
        f"2026-11-03T01:10,5,aplicar,m,1,0.5,{C},success,0,separar-hipotesis\n"
        f"2026-11-03T01:11,4,aplicar,m,1,0.5,{D},success,0,\n"
    )
    _exp(tmp_path, "sampling_1", costos=costos)
    tokens.registrar("sampling_1", tmp_path, tmp_path / "proy")
    filas = _leer(tmp_path, "sampling_1")
    assert filas[A]["etapa"] == "codigo"      # grupo 4 del cambio archivado
    assert filas[B]["etapa"] == "diseno"      # grupo 4 de separar-hipotesis
    assert filas[C]["etapa"] == "informe"
    assert filas[D]["etapa"] == "codigo"      # sin cambio: el archivado
    assert filas[A]["costo_fuente"] == "costos.csv"


def test_etapa_de_sitio_github_pages():
    g = tokens.ETAPA_DE_GRUPO_POR_CAMBIO["sitio-github-pages"]
    assert [g[str(n)] for n in range(1, 5)] == ["codigo"] * 4
    assert g["5"] == "informe"
