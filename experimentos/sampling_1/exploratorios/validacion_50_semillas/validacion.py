"""Validación con 50 semillas del aporte de Luis (commit 9e1889e): el loop de entrenamiento final de sus nueve estrategias.

PORTADO sin cambios de lógica: el entrenamiento por semilla (`full` y fast-retrain con peso 2), los parámetros de LightGBM,
la medición del tiempo (construcción del dataset + entrenamiento + predicción de test) y los ensambles acumulados.
Cambia el entorno: los datos salen de `comun.datos` y la ganancia de `comun.ganancia`; no hay Colab, Drive ni `FACTOR_VM`.

    python -m experimentos.sampling_1.exploratorios.validacion_50_semillas.validacion --estrategia 1 --hp original
"""

from __future__ import annotations

import logging
import time

import lightgbm as lgb
import numpy as np
from sklearn.metrics import roc_auc_score

from comun import baseline as bl
from comun import datos as dt
from comun import ganancia as gn
from comun import muestreo

from . import estrategias as es

log = logging.getLogger("validacion_50")


def _auc(y, p) -> float:
    try:
        return float(roc_auc_score(y, p))
    except ValueError:  # una sola clase (solo pasa con muestras de smoke)
        return float("nan")


def _params_dataset() -> dict:
    return {**bl.PARAMS_DATASET, "num_threads": bl.NUM_THREADS}


class Datos:
    """Train (201903-201906), validación (201908) y test (201910) como matrices float32."""

    def __init__(self, filas: int | None = None):
        dt.asegurar_panel(filas)
        train = dt.cargar_meses(bl.MESES_TRAIN, filas)
        val = dt.cargar_meses([bl.MES_VALIDACION], filas)
        test = dt.cargar_meses([bl.MES_TEST], filas)
        cols = dt.columnas_predictoras(train)
        self.x_tr, self.y_tr = dt.matriz(train, cols), train[dt.Y].to_numpy()
        self.x_va, self.y_va, self.b2_va = dt.matriz(val, cols), val[dt.Y].to_numpy(), val[dt.BAJA2].to_numpy()
        self.x_te, self.y_te, self.b2_te = dt.matriz(test, cols), test[dt.Y].to_numpy(), test[dt.BAJA2].to_numpy()
        t0 = time.perf_counter()
        self.dtrain_full = lgb.Dataset(self.x_tr, label=self.y_tr, params=_params_dataset(), free_raw_data=False)
        self.dtrain_full.construct()
        self.t_construct_full = time.perf_counter() - t0


def entrenar_semilla(e: es.Estrategia, hp: dict, semilla: int, d: Datos) -> tuple[np.ndarray, np.ndarray, float]:
    """(predicción en 201908, predicción en 201910, segundos). Los segundos no incluyen la predicción de 201908."""
    params = {**bl.PARAMS_FIJOS, "bagging_freq": 1, **hp, "seed": semilla}
    if e.modo == "full":
        t1 = time.perf_counter()
        modelo = lgb.train(params, d.dtrain_full)
        p_te = modelo.predict(d.x_te)
        t_raw = d.t_construct_full + (time.perf_counter() - t1)
    elif e.modo == "h4_50_pesos":
        t0 = time.perf_counter()
        idx = muestreo.indices_por_clase(d.y_tr, es.FRACCION_FAST, semilla)   # todas las bajas + 50 % de CONTINUA
        y_s = d.y_tr[idx]
        w_s = muestreo.peso_inverso(y_s, es.FRACCION_FAST).astype(np.float32)  # peso 2 en las CONTINUA
        d_sub = lgb.Dataset(d.x_tr[idx], label=y_s, weight=w_s, params=_params_dataset(), free_raw_data=False)
        d_sub.construct()
        modelo = lgb.train(params, d_sub)
        p_te = modelo.predict(d.x_te)
        t_raw = time.perf_counter() - t0
    else:
        raise ValueError(f"modo inválido: {e.modo!r}")
    return modelo.predict(d.x_va), p_te, t_raw


def correr_estrategia(e: es.Estrategia, hp: dict, t_opt: float, lista_semillas: list[int], d: Datos,
                      modo_hp: str = "original") -> tuple[list[dict], list[dict]]:
    """Entrena una semilla tras otra. Devuelve (una fila por semilla, una fila por K del ensamble de las primeras K).

    Por semilla: G al corte `N_ESTRELLA`, ganancia máxima de la curva y AUC en 201908, y G y AUC en 201910. En 201910 no se
    calcula el máximo de la curva (sería elegir el corte en test; `design.md` D9).
    """
    filas, ensambles = [], []
    suma_va = np.zeros(len(d.x_va), dtype=np.float64)
    suma_te = np.zeros(len(d.x_te), dtype=np.float64)
    for orden, semilla in enumerate(lista_semillas, start=1):
        p_va, p_te, t_raw = entrenar_semilla(e, hp, semilla, d)
        curva_va = gn.curva_de_corte(p_va, d.b2_va)
        filas.append({
            "estrategia": e.id, "nombre": e.nombre, "hp": modo_hp, "t_opt_s": t_opt, "orden": orden, "semilla": semilla,
            "tiempo_s": t_raw,
            "g_201908": gn.ganancia(p_va, d.b2_va, es.N_ESTRELLA), "gmax_201908": gn.ganancia_maxima(curva_va)[1],
            "auc_201908": _auc(d.y_va, p_va),
            "g_201910": gn.ganancia(p_te, d.b2_te, es.N_ESTRELLA), "auc_201910": _auc(d.y_te, p_te),
        })
        suma_va += p_va.astype(np.float32)
        suma_te += p_te.astype(np.float32)
        ensambles.append({"estrategia": e.id, "k": orden,
                          "g_201908": gn.ganancia(suma_va / orden, d.b2_va, es.N_ESTRELLA),
                          "g_201910": gn.ganancia(suma_te / orden, d.b2_te, es.N_ESTRELLA)})
        log.info("estrategia %d semilla %d (%d/%d): G201908=%.2fM %.1fs", e.id, semilla, orden, len(lista_semillas),
                 filas[-1]["g_201908"] / 1e6, t_raw)
    return filas, ensambles
