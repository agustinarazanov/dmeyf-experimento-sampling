"""`fast-retrain-opt` / `H4O-0.5` (D11), sin datos reales."""
import lightgbm as lgb
import numpy as np
import pandas as pd
import pytest

from comun import baseline as bl
from comun import correr, metodos, rutas
from comun import datos as dt
from comun import variantes


def _train(n=2000, seed=0):
    rng = np.random.default_rng(seed)
    y = (rng.random(n) < 0.1).astype(int)
    return pd.DataFrame({dt.ID: np.arange(n), dt.MES: 201903, dt.CLASE: np.where(y, "BAJA+2", "CONTINUA"), dt.Y: y,
                         dt.BAJA2: y, "a": rng.normal(size=n) + y, "b": rng.normal(size=n)})


def test_registro_de_h4o():
    b = variantes.variante("H4O-0.5")
    assert (b.dueno, b.metodo, b.tasa, b.estudio, b.replicas) == ("h4", "fast-retrain-opt", 0.5, "F0.5", True)
    assert variantes.dueno_estudio("F0.5") == "h4" and variantes.dueno_estudio("F0.5@3") == "h4"
    assert ("H4O-0.5", "H4F-0.05") in variantes.PARES_WELCH
    assert variantes.nombre("fast-retrain-opt", 0.5) == "H4O-0.5"
    assert metodos.metodo_optimizacion("fast-retrain-opt") == "fast-retrain-opt"  # estudio propio, no `U{r}`
    assert metodos.metodo_optimizacion("fast-retrain") == "uniforme"
    for f in (0.5, 0.25, 0.1, 0.05):
        metodos.validar("fast-retrain-opt", f)  # D8: las cuatro tasas de la grilla
        metodos.validar("clase-peso", f)
    with pytest.raises(ValueError, match="fracción"):
        metodos.validar("fast-retrain-opt", 0.3)


def test_la_muestra_de_busqueda_tiene_todas_las_bajas_y_la_mitad_de_las_continua():
    train = _train()
    datos, params, idx = metodos.FUNCIONES_OPT["fast-retrain-opt"](train, 0.5, 3)
    y, y0 = datos[dt.Y].to_numpy(), train[dt.Y].to_numpy()
    assert y.sum() == y0.sum()
    assert (y == 0).sum() == round((y0 == 0).sum() * 0.5)
    assert params == {"bagging_freq": 1}
    otra = metodos.FUNCIONES_OPT["fast-retrain-opt"](train, 0.5, 4)[2]
    assert not np.array_equal(idx, otra)  # la semilla de la réplica cambia el sorteo
    w = metodos.pesos("fast-retrain-opt", datos, 0.5)
    assert set(np.unique(w[y == 1])) == {1.0} and set(np.unique(w[y == 0])) == {2.0}


def test_los_pesos_llegan_al_dataset_de_cada_trial_y_la_validacion_no_lleva(tmp_path, monkeypatch):
    todo = pd.concat([_train(seed=m).assign(**{dt.MES: m}) for m in bl.MESES_PANEL], ignore_index=True)
    monkeypatch.setattr(dt, "cargar_meses", lambda meses, filas=None: todo[todo[dt.MES].isin(meses)].reset_index(drop=True))
    monkeypatch.setattr(dt, "asegurar_panel", lambda filas=None: (tmp_path / "p.parquet", 0.0))
    monkeypatch.setattr(dt, "MESES_LEIDOS", [])
    monkeypatch.setattr(bl, "DATOS_DIR", tmp_path / "datos")
    monkeypatch.setattr(rutas, "EXPERIMENTOS", tmp_path / "experimentos")
    monkeypatch.setattr(correr, "commit_y_sucio", lambda: ("abc1234", False))
    datasets, entrenos = [], []
    real_dataset, real_train = lgb.Dataset, lgb.train

    def dataset(*a, **kw):
        datasets.append(kw.get("weight"))
        return real_dataset(*a, **kw)

    def entrenar(params, ds, *a, **kw):
        entrenos.append(ds)
        return real_train(params, ds, *a, **kw)

    monkeypatch.setattr(correr.lgb, "Dataset", dataset)
    monkeypatch.setattr(correr.lgb, "train", entrenar)
    correr.main(["--metodo", "fast-retrain-opt", "--tasa", "0.5", "--etapa", "optimizar", "--trials", "3", "--filas", "1"])
    assert len(datasets) == 1 and datasets[0] is not None  # un Dataset de train, con pesos; la validación no es un Dataset
    assert len(entrenos) == 3 and all(e is entrenos[0] for e in entrenos)  # los 3 trials usan ese Dataset ponderado
    assert set(np.unique(datasets[0])) == {1.0, 2.0}
    hp = rutas.ledger("h4") / "exploracion" / "hp" / "F0.5.json"
    assert hp.exists()
    # el final lee ese estudio y entrena con la receta sobre 201903-201908, con pesos
    datasets.clear()
    correr.main(["--metodo", "fast-retrain-opt", "--tasa", "0.5", "--etapa", "final", "--semilla", "100003", "--filas", "1"])
    assert len(datasets) == 1 and set(np.unique(datasets[0])) == {1.0, 2.0}


# --- `tiempos-confiables-y-consistencia` D8: H4O en las cuatro tasas y H4P ---------------------------------------


def test_la_replica_0_de_lo_que_ya_existe_no_cambia(tmp_path, monkeypatch):
    """Mismo `hash_muestra` e hiperparámetros con `--filas 20000` en `H4O-0.5`, `H4F-0.05` y `H4U-0.1`: `fast_retrain` sigue
    en 0,5 aunque la tasa sea otra, y `fast-retrain-opt` con 0,5 hace lo de antes."""
    train = _train(n=20000)
    y = train[dt.Y].to_numpy()
    antes = muestreo_viejo(y, 0.5, 7)
    assert np.array_equal(metodos.FUNCIONES_OPT["fast-retrain-opt"](train, 0.5, 7)[2], antes)
    for tasa in (0.05, 0.25):
        assert np.array_equal(metodos.FUNCIONES["fast-retrain"](train, tasa, 7)[2], antes)  # H4F: f = 0,5 fija
    assert np.array_equal(metodos.FUNCIONES_OPT["clase-uniforme"](train, 0.1, 7)[2],
                          muestreo_viejo(y, 0.1, 7))
    w = metodos.pesos("fast-retrain", train.iloc[:50], 0.05)
    assert set(np.unique(w[train.iloc[:50][dt.Y].to_numpy() == 0])) == {2.0}  # peso 2 en H4F-0.05


def muestreo_viejo(y, f, semilla):
    from comun import muestreo
    return muestreo.indices_por_clase(y, f, semilla)


@pytest.mark.parametrize("f", [0.25, 0.1, 0.05])
def test_la_muestra_de_h4o_tiene_todas_las_bajas_y_f_de_las_continua(f):
    train = _train()
    datos, _, _ = metodos.FUNCIONES_OPT["fast-retrain-opt"](train, f, 3)
    y, y0 = datos[dt.Y].to_numpy(), train[dt.Y].to_numpy()
    assert y.sum() == y0.sum() and (y == 0).sum() == round((y0 == 0).sum() * f)
    w = metodos.pesos("fast-retrain-opt", datos, f)
    assert set(np.unique(w[y == 0])) == {1.0 / f} and set(np.unique(w[y == 1])) == {1.0}
    final = metodos.FUNCIONES["fast-retrain-opt"](train, f, 100003)[0]  # el final usa la misma receta con la semilla final
    assert (final[dt.Y] == 0).sum() == (y == 0).sum()


def test_h4o_y_h4p_comparten_el_estudio_f():
    for f in (0.25, 0.1, 0.05):
        o, p = variantes.variante(f"H4O-{f:g}"), variantes.variante(f"H4P-{f:g}")
        assert o.estudio == p.estudio == f"F{f:g}" and variantes.dueno_estudio(p.estudio) == "h4"
        assert (p.metodo, p.dueno, p.replicas) == ("clase-peso", "h4", True)
    assert variantes.nombre("clase-peso", 0.1) == "H4P-0.1"


def test_clase_peso_optimiza_como_fast_retrain_opt_y_entrena_el_final_como_opt_muestra():
    assert metodos.metodo_optimizacion("clase-peso") == "fast-retrain-opt"  # no `uniforme`, que le daría el estudio U{r}
    assert metodos.estudio("clase-peso", 0.1) == "F0.1"
    train = _train()
    datos, params, idx = metodos.FUNCIONES["clase-peso"](train, 0.1, 100003)  # final: todo el train, sin peso
    assert len(datos) == len(train) and params == {"bagging_freq": 1}
    assert metodos.pesos("clase-peso", datos, 0.1) is None


def test_una_linea_clase_peso_optimizar_corre_f_y_no_u():
    a = correr.parsear(["--metodo", "clase-peso", "--tasa", "0.1", "--etapa", "optimizar", "--filas", "20000"])
    cx = correr.Contexto(a)
    assert cx.estudio == "F0.1" and cx.metodo == "fast-retrain-opt"
    assert cx.ruta_hp().name == "F0.1.json" and cx.ruta_hp().parent.parent.parent.name == "ledger"
    assert "h4" in str(cx.ruta_hp())
    f = correr.Contexto(correr.parsear(["--metodo", "clase-peso", "--tasa", "0.1", "--etapa", "final", "--filas", "20000"]))
    assert f.variante == "H4P-0.1" and f.estudio == "F0.1" and f.metodo == "clase-peso"


def test_la_busqueda_de_h4p_es_la_muestra_de_h4u():
    """La muestra de búsqueda de `H4P-0.1` y la de `H4U-0.1` salen de la misma función y la misma semilla."""
    train = _train(n=5000)
    p = metodos.FUNCIONES_OPT["fast-retrain-opt"](train, 0.1, 3)[2]
    u = metodos.FUNCIONES_OPT["clase-uniforme"](train, 0.1, 3)[2]
    assert np.array_equal(p, u)


def test_h4f_no_cambia_de_fraccion_con_la_tasa(tmp_path):
    assert metodos.FRACCION_FAST_RETRAIN == 0.5
    train = _train()
    a = metodos.FUNCIONES["fast-retrain"](train, 0.05, 11)[2]
    b = metodos.FUNCIONES["fast-retrain"](train, 0.25, 11)[2]
    assert np.array_equal(a, b)
