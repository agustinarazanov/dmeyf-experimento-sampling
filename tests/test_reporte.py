"""El reporte se regenera igual salvo la fecha, y con un ledger vacío deja las variantes pendientes sin fallar."""

import re

import pytest

from comun import variantes as reg
from comun import reporte, rutas

EXPERIMENTOS = [reg.CONTROL, *[e for e in reg.duenos() if e != reg.CONTROL], reg.AGREGADOR]


def sin_fecha(html: str) -> str:
    return re.sub(r"Generado \d{4}-\d\d-\d\d \d\d:\d\d", "Generado", html)


@pytest.mark.parametrize("exp", EXPERIMENTOS)
def test_dos_veces_da_lo_mismo(exp):
    assert sin_fecha(reporte.generar(exp)) == sin_fecha(reporte.generar(exp))


def test_agregador_lista_todos_los_variantes_de_las_hipotesis():
    ctx = reporte.Contexto(reg.AGREGADOR)
    esperados = {b.nombre for b in reg.VARIANTES.values() if b.dueno != reg.CONTROL}
    assert set(ctx.variantes) == esperados


def test_hipotesis_nueva_aparece_sin_tocar_el_generador(monkeypatch):
    nuevo = reg.Variante("X1", "h1", "uniforme", 0.7, "U0.5")
    monkeypatch.setitem(reg.VARIANTES, "X1", nuevo)
    monkeypatch.setattr(reporte, "N_SEMILLAS", 10)
    monkeypatch.setattr(reporte, "VENTANA", "201903-201906")  # hasta que haya finales de la ronda nueva
    assert "X1" in reporte.Contexto(reg.AGREGADOR).variantes
    assert "X1" in reporte.generar(reg.AGREGADOR)


def test_ledger_vacio_deja_pendientes(monkeypatch, tmp_path):
    monkeypatch.setattr(rutas, "EXPERIMENTOS", tmp_path)
    for e in EXPERIMENTOS:
        (tmp_path / e / "ledger").mkdir(parents=True)
    html = reporte.generar("h1")
    assert "pendiente" in html and "<table>" in html


def test_exploratorio_sin_csv_sale_pendiente_con_el_nombre_del_archivo(tmp_path):
    import json
    carpeta = tmp_path / "experimentos" / "h3" / "sm"
    carpeta.mkdir(parents=True)
    (carpeta / "exploratorio.json").write_text(json.dumps(dict(
        autor="A", fecha="2026-11-04", pregunta="p", protocolo="q", advertencia="w",
        tablas=[dict(csv="resultados/falta.csv", columnas=["x"])])))
    (fila,) = reporte.bloque_b(tmp_path)
    assert fila["cifras"] == ["pendiente: falta resultados/falta.csv"]
    assert fila["advertencia"] == "w"
    assert "  - pendiente: falta resultados/falta.csv" in reporte.lista_b([fila])
    assert "<li class='pend'>pendiente: falta resultados/falta.csv</li>" in reporte.tarjetas_b([fila])


def test_variante_de_una_replica_lleva_la_nota_sin_replicas():
    import pandas as pd
    ctx = reporte.Contexto(reg.AGREGADOR)
    ap = pd.DataFrame(dict(g_control=[1e8], delta_g_media=[1e6], delta_g_ic_inf=[0.0], delta_g_ic_sup=[2e6],
                           tiempo_total_s=[100.0], aceleracion=[3.0], veredicto=["no pierde"]), index=["U0.1"])
    fin = pd.DataFrame(dict(variante=["U0.1"] * 10))
    f = reporte.fila_bloque_a(ctx, "U0.1", fin, ap, pd.DataFrame(), None, None, None)
    assert f["nota"] == "sin réplicas" and f["fuente"] == "réplica 0" and f["dR"] is None
    celdas = reporte.celdas_bloque_a(f)
    assert celdas[4] == "—" and celdas[8] == "sin réplicas"


def test_variante_con_replicas_marca_su_g_y_la_referencia_del_control():
    """Ḡ de una variante con réplicas es la media entre réplicas: la celda lo dice y la cabecera da Ḡ_C con réplicas."""
    import pandas as pd
    ctx = reporte.Contexto(reg.AGREGADOR)
    ap = pd.DataFrame(dict(g_control=[1e8], delta_g_media=[3e6], delta_g_ic_inf=[0.0], delta_g_ic_sup=[6e6],
                           tiempo_total_s=[100.0], aceleracion=[3.0], veredicto=["no pierde"]), index=["H3-0.1"])
    rep = pd.DataFrame(dict(delta_g_media=[1e6, None], delta_g_ic_inf=[-1e6, None], delta_g_ic_sup=[3e6, None],
                            n_replicas=[8, 8], g_media_replicas=[1.01e8, 1e8], veredicto=["no pierde", ""]),
                       index=["H3-0.1", reg.CONTROL])
    f = reporte.fila_bloque_a(ctx, "H3-0.1", pd.DataFrame(), ap, rep, None, None, None)
    assert reporte.celdas_bloque_a(f)[2] == "101.00 (R=8)"
    a = dict(n_est=3300, g_c1=9.9e7, g_c10=None, g_cR=1e8, n_cR=8)
    assert "Ḡ_C con réplicas = 100.00 M$ (R=8)" in reporte.referencia_control(a)


def _predicciones(tmp_path, variante, semilla_azar, k):
    import numpy as np
    import pandas as pd
    rng = np.random.default_rng(semilla_azar)
    n = 3000
    baja2 = np.arange(n) < 100
    filas = []
    for s in reporte.SEMILLAS_FINALES[:k]:
        ruta = tmp_path / f"{variante}_{s}.parquet"
        pd.DataFrame(dict(numero_de_cliente=np.arange(n), prob=rng.random(n) + baja2 * 0.5, es_baja2=baja2)).to_parquet(ruta)
        filas.append(dict(variante=variante, semilla=s, predicciones_201910=str(ruta)))
    return filas


def test_bootstrap_de_clientes_identico_en_dos_corridas(tmp_path):
    import pandas as pd
    fin = pd.DataFrame(_predicciones(tmp_path, "C", 1, 20) + _predicciones(tmp_path, "U0.5", 2, 20))
    datos = {"U0.5": (10.0, 5.0, 3, 1.0)}
    a = reporte.bootstrap_tiempo_igual(fin, datos, 300, n_boot=50)
    b = reporte.bootstrap_tiempo_igual(fin, datos, 300, n_boot=50)
    assert a == b and a["U0.5"][1] <= a["U0.5"][0] <= a["U0.5"][2]


@pytest.mark.parametrize("exp", EXPERIMENTOS)
def test_es_una_pagina_jekyll(exp):
    pagina = reporte.generar(exp)
    assert pagina.startswith("---")
    assert "<html" not in pagina and "<style" not in pagina


@pytest.fixture
def ronda_anterior(monkeypatch):
    """La ronda 201903-201906 de 10 semillas, completa en el ledger: con ella hay figuras y tablas con números."""
    monkeypatch.setattr(reporte, "VENTANA", "201903-201906")
    monkeypatch.setattr(reporte, "N_SEMILLAS", 10)


@pytest.fixture(scope="module")
def pagina_s1():
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(reporte, "VENTANA", "201903-201906")
        mp.setattr(reporte, "N_SEMILLAS", 10)
        return reporte.generar(reg.AGREGADOR)


@pytest.mark.parametrize("exp", ["h3", reg.AGREGADOR])
def test_con_figuras_dos_veces_da_lo_mismo_en_svg(ronda_anterior, exp):
    pagina = reporte.generar(exp)
    assert "<svg" in pagina and "data:image/png" not in pagina
    assert "<html" not in pagina and "<style" not in pagina
    assert sin_fecha(pagina) == sin_fecha(reporte.generar(exp))


def test_figuras_guarda_png(ronda_anterior, tmp_path):
    reporte.generar("h1", tmp_path)
    assert {p.suffix for p in tmp_path.iterdir()} == {".png"}


def _figura(pagina: str, nombre: str) -> str:
    m = re.search(rf'<figure class="fig" id="fig-{nombre}".*?</figure>', pagina, re.S)
    assert m, f"falta la figura {nombre}"
    return m.group(0)


def _textos(svg: str) -> list[str]:
    return re.findall(r"<text[^>]*>([^<]*)</text>", svg)


@pytest.mark.parametrize("exp, nombre", [(reg.AGREGADOR, "tradeoff"), ("h1", "tradeoff_h1")])
def test_tradeoff_una_variante_por_fila_y_el_titulo(ronda_anterior, exp, nombre):
    pagina = reporte.generar(exp)
    textos = _textos(_figura(pagina, nombre))
    assert any(t.startswith("Tradeoff por variante") for t in textos)
    ctx = reporte.Contexto(exp)
    ap = reporte.cargar([reg.CONTROL, *ctx.exps])[1]
    for b in ctx.variantes:  # las que tienen Δ, una fila cada una; las pendientes no se dibujan
        assert textos.count(f"{b} ({ctx.hip_de[b]})") == (1 if b in ap.index else 0)
    # va antes de las tablas de resultados (las generadas; las de los docs vienen antes, en la introducción)
    assert pagina.index(f'id="fig-{nombre}"') < pagina.index("<div class='table-wrapper'>")


def test_fraccion_sin_familias_de_dos_tasas_sale_pendiente(monkeypatch):
    for k, v in list(reg.VARIANTES.items()):
        monkeypatch.setitem(reg.VARIANTES, k, v._replace(tasa=1.0))
    ctx = reporte.Contexto(reg.AGREGADOR)
    f = dict(variante="U0.1", hipotesis="H1", dR=None, d0=(1.0, 0.0, 2.0))
    assert "pendiente" in reporte.fig_fraccion(ctx, {"filas": [f, dict(f, variante="U0.5")], "delta": 1.0}, None)


def test_desplazador_separa_etiquetas_en_el_mismo_punto():
    (x1, y1), (x2, y2) = reporte.desplazar([(0.5, 0.5), (0.5, 0.5)], alto=0.07, ancho=0.2)
    assert abs(y1 - y2) >= 0.07 - 1e-9
    # tres etiquetas pegadas cerca del techo se apilan hacia abajo y quedan dentro del panel
    pos = reporte.desplazar_dentro([(0.5, 0.9), (0.5, 0.9), (0.52, 0.91)], alto=0.07, ancho=0.2)
    assert max(y for _, y in pos) <= 0.97 and len({round(y, 6) for _, y in pos}) == 3


def test_sin_replicas_los_tres_graficos_salen_pendientes(ronda_anterior, monkeypatch):
    import pandas as pd
    ctx = reporte.Contexto(reg.AGREGADOR)
    a = {"filas": [], "rep": pd.DataFrame(), "g_rep": {}}
    for fig in (reporte.fig_replicas, reporte.fig_varianza, reporte.fig_diferencias):
        assert "class='pend'" in fig(ctx, a, None)
    cargar = reporte.cargar_replicas
    monkeypatch.setattr(reporte, "cargar_replicas",
                        lambda exps, n: (*cargar(exps, n)[:2], pd.DataFrame(columns=["variante"]).set_index("variante")))
    pagina = reporte.generar(reg.AGREGADOR)
    assert "pendiente: ninguna variante tiene réplicas" in pagina and 'id="fig-tradeoff"' in pagina


def _tabla(pagina: str, primera: str) -> str:
    m = re.search(rf"<table><tr><th>{re.escape(primera)}</th>.*?</table>", pagina, re.S)
    assert m
    return m.group(0)


def _filas(tabla: str) -> dict[str, list[str]]:
    filas = re.findall(r"<tr>(.*?)</tr>", tabla, re.S)[1:]
    celdas = [re.findall(r"<td[^>]*>.*?</td>", f, re.S) for f in filas]
    return {re.sub(r"<[^>]+>", "", c[0]): c for c in celdas}


def test_resumen_corto(pagina_s1):
    resumen = re.search(r"<table><tr><th>variante</th><th>hipótesis</th><th>R</th>.*?</table>", pagina_s1, re.S).group(0)
    assert len(re.findall(r"<th>", resumen.split("</tr>")[0])) <= 6
    for celdas in _filas(resumen).values():
        assert all(c.count("class='ic'") <= 1 for c in celdas)
    assert "<details><summary>Detalle del bloque A</summary>" in pagina_s1
    assert "(R=" not in resumen and "no aplica" not in resumen and "sin réplicas" not in resumen


def test_resaltado(pagina_s1):
    resumen = re.search(r"<table><tr><th>variante</th><th>hipótesis</th><th>R</th>.*?</table>", pagina_s1, re.S).group(0)
    filas = _filas(resumen)
    assert "class='sig-neg'" in filas["U0.05"][3]
    assert "<span class='pill pierde'>pierde</span>" in filas["U0.05"][5]
    for j in (3, 4):
        assert sum("mejor" in c[j] for c in filas.values()) == 1
    assert "mejor" in filas["H4F-0.05"][4]


def test_regenerar_resalta_igual(pagina_s1, ronda_anterior):
    clases = lambda p: re.findall(r"class='([^']*)'", p)
    assert clases(pagina_s1) == clases(reporte.generar(reg.AGREGADOR))


def test_tabla_de_resultados_conserva_el_bloque_a(ronda_anterior):
    """El bloque A de `tabla_resultados.md` sigue saliendo de `celdas_bloque_a`, con su (R=n) y sus notas en texto."""
    md = reporte.generar_con_tabla(reg.AGREGADOR)[1]
    bloque_a = md.split("## Bloque B")[0]
    assert "| " + " | ".join(reporte.CAB_A) + " |" in bloque_a
    assert "(R=8)" in bloque_a and "sin réplicas" in bloque_a
    assert "### experimentos/" in md.split("## Bloque B")[1]
