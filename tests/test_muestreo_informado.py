"""Muestras por cliente y por clase, final submuestreado con peso y reescalados (`incorporar-aportes` D3). Sin datos."""

import numpy as np
import pandas as pd
import pytest

from comun import datos as dt
from comun import metodos, muestreo


def _y(n=2000, pos=100, semilla=0):
    y = np.zeros(n, dtype=int)
    y[np.random.default_rng(semilla).choice(n, pos, replace=False)] = 1
    return y


def test_por_cliente_cada_cliente_esta_entero_o_ausente():
    clientes = np.repeat(np.arange(200), np.random.default_rng(1).integers(1, 5, 200))
    idx = muestreo.indices_por_cliente(clientes, 0.1, 3)
    elegidos = set(clientes[idx])
    assert len(elegidos) == 20
    assert set(np.flatnonzero(np.isin(clientes, list(elegidos)))) == set(idx)
    assert np.array_equal(idx, muestreo.indices_por_cliente(clientes, 0.1, 3))
    assert not np.array_equal(idx, muestreo.indices_por_cliente(clientes, 0.1, 4))


def test_por_clase_conserva_todos_los_positivos_y_la_fraccion_de_negativos():
    y = _y()
    idx = muestreo.indices_por_clase(y, 0.1, 0)
    assert y[idx].sum() == y.sum()
    assert (y[idx] == 0).sum() == round((y == 0).sum() * 0.1)


def test_dificil_y_uniforme_tienen_igual_cantidad_de_positivos_y_negativos():
    y = _y()
    prob = np.random.default_rng(2).random(len(y))
    pozo = muestreo.pozo_dificil(y, prob)
    assert len(pozo) == round((y == 0).sum() * 0.35) and (y[pozo] == 0).all()
    dif, uni = muestreo.indices_por_clase(y, 0.1, 5, pozo), muestreo.indices_por_clase(y, 0.1, 5)
    assert len(dif) == len(uni) and y[dif].sum() == y[uni].sum()
    assert set(dif) - set(np.flatnonzero(y == 1)) <= set(pozo)


def test_pozo_son_los_negativos_de_mayor_probabilidad():
    y = np.array([0, 0, 1, 0, 0, 0, 0, 0, 0, 0])
    prob = np.array([.9, .1, .99, .8, .2, .3, .4, .5, .6, .7])
    assert list(muestreo.pozo_dificil(y, prob, 0.35)) == [0, 3, 9]  # 9 negativos · 0,35 = 3


def test_pozo_chico_falla():
    y = _y()
    with pytest.raises(ValueError, match="pozo"):
        muestreo.indices_por_clase(y, 0.5, 0, muestreo.pozo_dificil(y, np.zeros(len(y))))


def test_peso_inverso_restituye_la_proporcion_de_clases():
    y = _y()
    idx = muestreo.indices_por_clase(y, 0.5, 7)
    w = muestreo.peso_inverso(y[idx], 0.5)
    assert w[y[idx] == 1].tolist() == [1.0] * y.sum() and set(w[y[idx] == 0]) == {2.0}
    assert w[y[idx] == 0].sum() == pytest.approx((y == 0).sum(), rel=1e-3)
    assert w[y[idx] == 1].sum() / w[y[idx] == 0].sum() == pytest.approx(y.sum() / (y == 0).sum(), rel=1e-3)


def test_pesos_solo_para_fast_retrain():
    df = pd.DataFrame({dt.Y: [1, 0, 0]})
    assert metodos.pesos("opt-muestra", df) is None
    assert metodos.pesos("fast-retrain", df).tolist() == [1.0, 2.0, 2.0]


@pytest.mark.parametrize("metodo,tasa,mdl,esperado", [
    ("opt-muestra-reescalado", 0.1, 100, 316), ("opt-muestra-lineal", 0.1, 100, 1000), ("opt-muestra-lineal", 0.25, 100, 400),
    ("opt-muestra-reescalado", 0.25, 100, 200), ("opt-muestra-lineal", 0.05, 1000, 8000), ("opt-muestra", 0.1, 100, 100),
])
def test_reescalado_redondea_y_recorta(metodo, tasa, mdl, esperado):
    hp = dict(min_data_in_leaf=mdl, num_leaves=31)
    assert metodos.ajustar_hp(metodo, tasa, hp) == dict(hp, min_data_in_leaf=esperado)


def test_lineal_recorta_a_8000_y_a_uno():
    assert metodos.ajustar_hp("opt-muestra-lineal", 0.1, dict(min_data_in_leaf=5000))["min_data_in_leaf"] == 8000
    assert metodos.ajustar_hp("opt-muestra-reescalado", 0.1, dict(min_data_in_leaf=0))["min_data_in_leaf"] == 1


def test_metodo_optimizacion_y_validacion():
    pedidos = ("opt-muestra-lineal", "fast-retrain", "opt-muestra-cliente", "clase-dificil")
    assert [metodos.metodo_optimizacion(m) for m in pedidos] == ["uniforme", "uniforme", "opt-muestra-cliente", "clase-dificil"]
    with pytest.raises(ValueError, match="tasa"):
        metodos.validar("clase-uniforme", 1.0)


def _train(n=3000):
    rng = np.random.default_rng(0)
    df = pd.DataFrame({dt.ID: np.arange(n) // 3, dt.MES: 201903, dt.CLASE: "CONTINUA", dt.BAJA2: 0,
                       "a": rng.normal(size=n), "b": rng.normal(size=n)})
    df[dt.Y] = (df["a"] + rng.normal(scale=.5, size=n) > 1.6).astype(int)
    return df


def test_sonda_y_muestra_dificil_sobre_datos_sinteticos():
    train = _train()
    pozo, t = metodos.sonda_pozo(train, 2)
    assert t > 0 and (train[dt.Y].to_numpy()[pozo] == 0).all()
    d, _, idx = metodos.clase_dificil(train, 0.1, 2, pozo)
    u, _, _ = metodos.clase_uniforme(train, 0.1, 2)
    assert len(d) == len(u) and d[dt.Y].sum() == u[dt.Y].sum() == train[dt.Y].sum()
    assert set(idx) - set(np.flatnonzero(train[dt.Y] == 1)) <= set(pozo)
    assert np.array_equal(pozo, metodos.sonda_pozo(train, 2)[0])


def test_cliente_toma_clientes_enteros():
    train = _train()
    datos, _, _ = metodos.cliente(train, 0.1, 0)
    assert len(datos) == train[dt.ID].isin(datos[dt.ID]).sum()
