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
    assert "pendiente" in reporte.tabla_md(reporte.CAB_B, reporte.filas_b([fila]))


def test_variante_de_una_replica_lleva_la_nota_sin_replicas():
    import pandas as pd
    ctx = reporte.Contexto(reg.AGREGADOR)
    ap = pd.DataFrame(dict(g_control=[1e8], delta_g_media=[1e6], delta_g_ic_inf=[0.0], delta_g_ic_sup=[2e6],
                           tiempo_total_s=[100.0], aceleracion=[3.0], veredicto=["no pierde"]), index=["U0.1"])
    fin = pd.DataFrame(dict(variante=["U0.1"] * 10))
    f = reporte.fila_bloque_a(ctx, "U0.1", fin, ap, pd.DataFrame(), None, None, None)
    assert f["nota"] == "sin réplicas" and f["fuente"] == "réplica 0" and f["dR"] is None
    celdas = reporte.celdas_bloque_a(f)
    assert celdas[4] == "—" and celdas[7] == "sin réplicas"


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
    fin = pd.DataFrame(_predicciones(tmp_path, "C", 1, 10) + _predicciones(tmp_path, "U0.5", 2, 10))
    datos = {"U0.5": (10.0, 5.0, 3, 1.0)}
    a = reporte.bootstrap_tiempo_igual(fin, datos, 300, n_boot=50)
    b = reporte.bootstrap_tiempo_igual(fin, datos, 300, n_boot=50)
    assert a == b and a["U0.5"][1] <= a["U0.5"][0] <= a["U0.5"][2]
