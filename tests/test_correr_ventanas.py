"""Ventanas de train de `optimizar` y `final` (D1, D3, D4), con un panel sintético y todo en un directorio temporal."""
import numpy as np
import pandas as pd
import pytest

from comun import baseline as bl
from comun import correr
from comun import datos as dt
from comun import ledger as lg
from comun import rutas


def _panel(meses, n=400, seed=0):
    rng = np.random.default_rng(seed)
    filas = []
    for m in meses:
        y = (rng.random(n) < 0.1).astype(int)
        df = pd.DataFrame({dt.ID: np.arange(n), dt.MES: m, dt.CLASE: np.where(y, "BAJA+2", "CONTINUA"),
                           dt.Y: y, dt.BAJA2: y, "a": rng.normal(size=n) + y, "b": rng.normal(size=n)})
        filas.append(df)
    return pd.concat(filas, ignore_index=True)


@pytest.fixture
def entorno(tmp_path, monkeypatch):
    """Panel sintético, ledger y datos temporales; devuelve la lista de meses pedidos a `cargar_meses`."""
    pedidos: list[list[int]] = []
    todo = _panel(bl.MESES_PANEL)

    def cargar(meses, filas=None):
        pedidos.append(list(meses))
        dt.MESES_LEIDOS.extend(meses)
        return todo[todo[dt.MES].isin(meses)].reset_index(drop=True)

    monkeypatch.setattr(dt, "cargar_meses", cargar)
    monkeypatch.setattr(dt, "asegurar_panel", lambda filas=None: (tmp_path / "panel.parquet", 0.0))
    monkeypatch.setattr(dt, "MESES_LEIDOS", [])
    monkeypatch.setattr(bl, "DATOS_DIR", tmp_path / "datos")
    monkeypatch.setattr(rutas, "EXPERIMENTOS", tmp_path / "experimentos")
    monkeypatch.setattr(correr, "commit_y_sucio", lambda: ("abc1234", False))
    return pedidos


def _argv(etapa, *extra):
    return ["--metodo", "uniforme", "--tasa", "0.5", "--etapa", etapa, "--trials", "2", "--filas", "1", *extra]


def test_optimizar_lee_solo_201903_a_201906_y_201908(entorno):
    correr.main(_argv("optimizar"))
    leidos = {m for p in entorno for m in p}
    assert leidos == set(bl.MESES_TRAIN_OPT) | {bl.MES_VALIDACION}
    assert 201907 not in leidos and bl.MES_TEST not in leidos


def test_optimizar_falla_si_alguien_leyo_201907(entorno):
    dt.MESES_LEIDOS.append(201907)
    with pytest.raises(RuntimeError, match="201907"):
        correr.main(_argv("optimizar"))


def test_final_entrena_201903_a_201908_y_no_predice_201908(entorno):
    correr.main(_argv("optimizar"))
    entorno.clear()
    correr.main(_argv("final", "--semilla", "100003"))
    assert entorno[0] == bl.MESES_TRAIN_FINAL and entorno[1] == [bl.MES_TEST]
    assert bl.MES_VALIDACION in entorno[0]
    filas = lg.leer_corridas(rutas.ledger("h1") / "exploracion" / "corridas")
    f = filas[filas["etapa_corrida"] == "final"].iloc[0]
    assert f["meses_final"] == "201903-201908"
    assert pd.isna(f["auc_val"]) and pd.isna(f["curva_201908"])
    assert not pd.isna(f["auc_test"]) and f["curva_201910"]
    assert not list((rutas.ledger("h1") / "exploracion" / "curvas").glob("*_201908.csv"))


def test_final_sin_meses_final_no_se_escribe(tmp_path):
    fila = {c: "" for c in lg.COLUMNAS}
    fila.update(id="x", etapa="final", etapa_corrida="final", meses_final=None)
    with pytest.raises(ValueError, match="meses_final"):
        lg.escribir_fila(tmp_path, fila)
    assert not list(tmp_path.glob("*.csv"))
    fila["meses_final"] = "201903-201908"
    lg.escribir_fila(tmp_path, fila)
    assert lg.existe_fila(tmp_path, "x")


def test_el_id_del_final_lleva_la_ventana():
    assert correr.ventana(bl.MESES_TRAIN_FINAL) == "201903-201908"
    assert correr.ventana_corta(bl.MESES_TRAIN_FINAL) == "0308"
    a = correr.parsear(_argv("final"))
    cx = correr.Contexto(a)
    assert "final-0308" in cx.id(100003, "final")
    assert "optimizar" in cx.id(0, "optimizar") and "0308" not in cx.id(0, "optimizar")


def test_una_ronda_nueva_no_reemplaza_a_la_vieja():
    base = {c: "" for c in lg.COLUMNAS}
    base.update(variante="C", metodo="uniforme", tasa=1.0, replica_opt=0, semilla=1, etapa="final", etapa_corrida="final",
                valida=True, commit="abc")
    vieja = {**base, "id": "v", "fecha": "2026-11-01T10:00:00", "meses_final": "201903-201906"}
    nueva = {**base, "id": "n", "fecha": "2026-11-20T10:00:00", "meses_final": "201903-201908"}
    res, repl = lg.consolidar_corridas(pd.DataFrame([vieja, nueva]))
    assert sorted(res["id"]) == ["n", "v"] and repl.empty
