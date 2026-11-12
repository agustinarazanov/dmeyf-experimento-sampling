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
    with pytest.raises(ValueError, match="fracción"):
        metodos.validar("fast-retrain-opt", 0.25)


def test_la_muestra_de_busqueda_tiene_todas_las_bajas_y_la_mitad_de_las_continua():
    train = _train()
    datos, params, idx = metodos.FUNCIONES_OPT["fast-retrain-opt"](train, 0.5, 3)
    y, y0 = datos[dt.Y].to_numpy(), train[dt.Y].to_numpy()
    assert y.sum() == y0.sum()
    assert (y == 0).sum() == round((y0 == 0).sum() * 0.5)
    assert params == {"bagging_freq": 1}
    otra = metodos.FUNCIONES_OPT["fast-retrain-opt"](train, 0.5, 4)[2]
    assert not np.array_equal(idx, otra)  # la semilla de la réplica cambia el sorteo
    w = metodos.pesos("fast-retrain-opt", datos)
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
