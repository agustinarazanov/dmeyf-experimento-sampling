"""`replicas.csv` (`h3-semillas-optuna` D5): Δ con réplicas, descomposición de la varianza y diferencia apareada de H3R y H3."""

import numpy as np
import pandas as pd
import pytest
from scipy import stats

from comun import consolidar
from comun import ledger as lg

N_ESTRELLA = 300


def corrida(led, variante, semilla, replica, escala, estudio=None, metodo="uniforme"):
    """Una fila final cuya ganancia al corte N* = 300 es `escala` · 300."""
    id_ = f"{variante}@{replica}_{semilla}" if replica else f"{variante}_{semilla}"
    envios = list(range(50, 301, 50))
    for mes in (201908, 201910):
        pd.DataFrame({"envios": envios, "ganancia": [escala * e for e in envios]}).to_csv(led / "curvas" / f"{id_}_{mes}.csv", index=False)
    f = {c: "" for c in lg.COLUMNAS}
    f.update(id=id_, fecha="2026-11-01T10:00:00", variante=variante, metodo=metodo, tasa=1 if variante == "C" else 0.1,
             semilla=semilla, replica_opt=replica, etapa="final", etapa_corrida="final", estudio=estudio or variante, valida=True,
             tiempo_optimizacion_s=0.0, commit="abc", auc_test=0.9, tiempo_entrenamiento_s=10.0, maquina="n2", cpu="ice",
             hilos=8, curva_201908=f"curvas/{id_}_201908.csv", curva_201910=f"curvas/{id_}_201910.csv")
    lg.escribir_fila(led / "corridas", f)


def sintetico(variante, led, replicas, semillas, media, sd_rep, sd_sem, rng):
    """Escribe réplicas × semillas finales y devuelve las ganancias (escala · 300) por (réplica, semilla)."""
    g = {}
    for k in replicas:
        centro = media + rng.normal(0, sd_rep)
        for s in semillas:
            escala = (centro + rng.normal(0, sd_sem)) / N_ESTRELLA
            corrida(led, variante, s, k, escala)
            g[(k, s)] = escala * N_ESTRELLA
    return g


@pytest.fixture
def ledger_3_replicas(tmp_path):
    (tmp_path / "curvas").mkdir()
    rng = np.random.default_rng(1)
    gc = sintetico("C", tmp_path, [0, 1, 2], [1, 2, 3, 4], 1000.0, 20.0, 10.0, rng)
    gv = sintetico("U0.5", tmp_path, [0, 1, 2], [1, 2, 3, 4], 1030.0, 20.0, 10.0, rng)
    return tmp_path, gc, gv


def test_suma_de_cuadrados_exacta(ledger_3_replicas):
    led, gc, _ = ledger_3_replicas
    r = consolidar.consolidar(led)["replicas"].set_index("variante")
    c = r.loc["C"]
    x = np.array(list(gc.values()))
    assert c["ss_entre"] + c["ss_dentro"] == pytest.approx(c["ss_total"], rel=1e-12)
    assert c["ss_total"] == pytest.approx(((x - x.mean()) ** 2).sum(), rel=1e-12)
    assert c["var_entre"] + c["var_dentro"] == pytest.approx(x.var(), rel=1e-12)
    medias = [np.mean([v for (k, _), v in gc.items() if k == kk]) for kk in (0, 1, 2)]
    assert c["sd_entre_replicas"] == pytest.approx(np.std(medias, ddof=1))
    assert (c["n_replicas"], c["n_semillas"]) == (3, 12)


def test_delta_con_replicas_con_ic_de_welch(ledger_3_replicas):
    led, gc, gv = ledger_3_replicas
    r = consolidar.consolidar(led)["replicas"].set_index("variante")
    mc = [np.mean([v for (k, _), v in gc.items() if k == kk]) for kk in (0, 1, 2)]
    mv = [np.mean([v for (k, _), v in gv.items() if k == kk]) for kk in (0, 1, 2)]
    fila = r.loc["U0.5"]
    assert fila["delta_g_media"] == pytest.approx(np.mean(mv) - np.mean(mc))
    ic = stats.ttest_ind(mv, mc, equal_var=False).confidence_interval(0.95)
    assert fila["delta_g_ic_inf"] == pytest.approx(ic.low) and fila["delta_g_ic_sup"] == pytest.approx(ic.high)
    assert fila["contra"] == "C" and fila["n_replicas_control"] == 3 and fila["n_semillas_control"] == 12
    assert fila["delta_g_margen"] == pytest.approx(lg.DELTA_REL * np.mean([v for (k, _), v in gc.items() if k == 0]))
    assert "veredicto" in r.columns and "C" in r.index and pd.isna(r.loc["C", "delta_g_media"])


def test_el_apareado_usa_solo_la_replica_0(ledger_3_replicas):
    led, gc, gv = ledger_3_replicas
    ap = consolidar.consolidar(led)["apareado"].iloc[0]
    assert ap["n_semillas"] == 4 and ap["n_estrella"] == N_ESTRELLA
    esperado = np.mean([gv[(0, s)] - gc[(0, s)] for s in (1, 2, 3, 4)])
    assert ap["delta_g_media"] == pytest.approx(esperado)
    assert ap["g_control"] == pytest.approx(np.mean([gc[(0, s)] for s in (1, 2, 3, 4)]))


def test_replicas_incompletas(tmp_path):
    (tmp_path / "curvas").mkdir()
    rng = np.random.default_rng(2)
    sintetico("C", tmp_path, [0, 1, 2], list(range(10)), 1000.0, 20.0, 10.0, rng)
    sintetico("H3-0.1", tmp_path, [0, 1], list(range(10)), 1000.0, 20.0, 10.0, rng)
    sintetico("H3-0.1", tmp_path, [2], [0, 1, 2], 1000.0, 20.0, 10.0, rng)  # la réplica 2 llegó con 3 semillas
    f = consolidar.consolidar(tmp_path)["replicas"].set_index("variante").loc["H3-0.1"]
    assert (f["n_replicas"], f["n_semillas"]) == (3, 23)
    assert "menos de 10 semillas" in f["nota"] and f["replicas"] == "0 1 2"
    assert np.isfinite(f["delta_g_ic_inf"])
    # réplicas que el control no tiene: lo dice
    sintetico("H3-0.05", tmp_path, [0, 1, 5], list(range(10)), 1000.0, 20.0, 10.0, rng)
    g = consolidar.consolidar(tmp_path)["replicas"].set_index("variante").loc["H3-0.05"]
    assert "réplicas distintas a las del control" in g["nota"]


def test_variante_de_una_replica_no_tiene_fila(ledger_3_replicas):
    led, _, _ = ledger_3_replicas
    rng = np.random.default_rng(3)
    sintetico("U0.25", led, [0], [1, 2, 3, 4], 1000.0, 20.0, 10.0, rng)
    r = consolidar.consolidar(led)
    assert "U0.25" not in set(r["replicas"]["variante"])
    assert "U0.25" in set(r["apareado"]["variante"])  # en el apareado de la réplica 0 sigue


def test_control_con_una_replica_no_da_delta(tmp_path):
    (tmp_path / "curvas").mkdir()
    rng = np.random.default_rng(4)
    sintetico("C", tmp_path, [0], [1, 2, 3], 1000.0, 20.0, 10.0, rng)
    sintetico("H3-0.1", tmp_path, [0, 1, 2], [1, 2, 3], 1000.0, 20.0, 10.0, rng)
    r = consolidar.consolidar(tmp_path)["replicas"].set_index("variante")
    assert list(r.index) == ["H3-0.1"] and "delta_g_media" not in r.columns
    assert "menos de dos réplicas" in r.loc["H3-0.1", "nota"]


def test_replicas_solo_con_las_variantes_del_experimento(tmp_path):
    ctrl, h3 = tmp_path / "control", tmp_path / "h3"
    for led in (ctrl, h3):
        (led / "curvas").mkdir(parents=True)
    rng = np.random.default_rng(5)
    sintetico("C", ctrl, [0, 1, 2], [1, 2, 3], 1000.0, 20.0, 10.0, rng)
    sintetico("H3-0.1", h3, [0, 1, 2], [1, 2, 3], 1000.0, 20.0, 10.0, rng)
    consolidar.consolidar(ctrl)
    assert list(pd.read_csv(ctrl / "replicas.csv")["variante"]) == ["C"]
    r = consolidar.consolidar(h3, control=ctrl)["replicas"]
    assert list(r["variante"]) == ["H3-0.1"] and r["n_replicas_control"].iloc[0] == 3
    assert list(pd.read_csv(h3 / "replicas.csv")["variante"]) == ["H3-0.1"]


def test_fila_sin_columna_replica_opt_es_la_replica_0(tmp_path):
    (tmp_path / "curvas").mkdir()
    corrida(tmp_path, "C", 1, 0, 1.0)
    ruta = next((tmp_path / "corridas").glob("*.csv"))
    pd.read_csv(ruta).drop(columns="replica_opt").to_csv(ruta, index=False)
    c = lg.leer_corridas(tmp_path / "corridas")
    assert list(c["replica_opt"]) == [0]


def test_clave_con_replica_no_reemplaza_a_otra_replica(tmp_path):
    (tmp_path / "curvas").mkdir()
    corrida(tmp_path, "C", 1, 0, 1.0)
    corrida(tmp_path, "C", 1, 1, 1.0)
    resultados, reemplazadas = lg.consolidar_corridas(lg.leer_corridas(tmp_path / "corridas"))
    assert len(resultados) == 2 and reemplazadas.empty


# --- diferencia apareada H3R − H3 (tarea 2.4) -----------------------------------


def test_diferencia_apareada_h3r_menos_h3_por_replica_y_semilla(tmp_path):
    (tmp_path / "curvas").mkdir()
    rng = np.random.default_rng(6)
    sintetico("C", tmp_path, range(4), range(5), 1000.0, 20.0, 10.0, rng)
    gh = sintetico("H3-0.1", tmp_path, range(4), range(5), 1000.0, 20.0, 10.0, rng)
    gr = {}
    for (k, s), v in gh.items():  # H3R = H3 + 5 + ruido por réplica y semilla
        gr[(k, s)] = v + 5 + rng.normal(0, 3)
        corrida(tmp_path, "H3R-0.1", s, k, gr[(k, s)] / N_ESTRELLA, estudio="U0.1", metodo="opt-muestra-reescalado")
    r = consolidar.consolidar(tmp_path)["replicas"].set_index("variante")
    f = r.loc["H3R-0.1 - H3-0.1"]
    por_k = [np.mean([gr[(k, s)] - gh[(k, s)] for s in range(5)]) for k in range(4)]
    assert f["delta_g_media"] == pytest.approx(np.mean(por_k))
    ic = stats.t.interval(0.95, 3, loc=np.mean(por_k), scale=stats.sem(por_k))
    assert f["delta_g_ic_inf"] == pytest.approx(ic[0]) and f["delta_g_ic_sup"] == pytest.approx(ic[1])
    assert (f["n_replicas"], f["n_semillas"]) == (4, 20) and f["contra"] == "H3-0.1"
    assert f["veredicto"] in ("mejora", "no cambia", "empeora")
    assert "3 g.l." in f["nota"]


@pytest.mark.parametrize("lo,hi,esperado", [(0.1, 2.0, "mejora"), (-3.0, -0.1, "empeora"), (-1.0, 1.0, "no cambia")])
def test_veredicto_del_par(lo, hi, esperado):
    assert lg._veredicto_par(lo, hi) == esperado


def test_diferencia_welch_h3k_menos_h3_sin_aparear(tmp_path):
    (tmp_path / "curvas").mkdir()
    rng = np.random.default_rng(8)
    sintetico("C", tmp_path, range(4), range(5), 1000.0, 20.0, 10.0, rng)
    gh = sintetico("H3-0.1", tmp_path, range(4), range(5), 1000.0, 20.0, 10.0, rng)
    gk = {}
    for (k, s), v in gh.items():
        gk[(k, s)] = v - 30 + rng.normal(0, 15)
        corrida(tmp_path, "H3K-0.1", s, k, gk[(k, s)] / N_ESTRELLA, estudio="K0.1", metodo="opt-muestra-cliente")
    f = consolidar.consolidar(tmp_path)["replicas"].set_index("variante").loc["H3K-0.1 - H3-0.1"]
    mk = [np.mean([gk[(k, s)] for s in range(5)]) for k in range(4)]
    mh = [np.mean([gh[(k, s)] for s in range(5)]) for k in range(4)]
    ic = stats.ttest_ind(mk, mh, equal_var=False).confidence_interval(0.95)
    assert f["delta_g_media"] == pytest.approx(np.mean(mk) - np.mean(mh))
    assert f["delta_g_ic_inf"] == pytest.approx(ic.low) and f["delta_g_ic_sup"] == pytest.approx(ic.high)
    assert f["contra"] == "H3-0.1" and f["nota"].startswith("sin aparear")


def test_par_sin_replicas_en_una_de_las_variantes_no_tiene_fila(tmp_path):
    (tmp_path / "curvas").mkdir()
    rng = np.random.default_rng(7)
    sintetico("C", tmp_path, range(3), range(3), 1000.0, 20.0, 10.0, rng)
    sintetico("H3-0.1", tmp_path, range(3), range(3), 1000.0, 20.0, 10.0, rng)
    sintetico("H3R-0.1", tmp_path, [0], range(3), 1000.0, 20.0, 10.0, rng)
    r = consolidar.consolidar(tmp_path)["replicas"]
    assert not r["variante"].str.contains(" - ").any()
