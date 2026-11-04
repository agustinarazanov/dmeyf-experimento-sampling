"""Grilla de 06, ajuste de LightGBM y verificación de parámetros efectivos (de 06_comparar_control_h3.py).

La grilla está versionada en `referencia/grilla_06.json` (las 20 configuraciones exactas, su orden, fijos y sha256).
`cargar_grilla()` la regenera con el generador de 06 y se detiene ante cualquier diferencia: no hace falta la carpeta
de la corrida 06 para obtenerla.

Generador (06): SeedSequence(20261102).spawn(2)[1] -> default_rng; para cada id 0..19, en este orden:
  num_leaves         entero uniforme en [8, 64]
  learning_rate      log-uniforme en [0.01, 0.10]
  min_data_in_leaf   entero log-uniforme en [100, 2000]
  feature_fraction   uniforme en [0.5, 1.0]
  bagging_fraction   uniforme en [0.5, 1.0]
Los reales se redondean a 6 cifras significativas. Fijos: bagging_freq=1, 100 árboles sin early stopping,
objective=binary, metric=auc, 4 hilos, seed=20261102, sin pesos de clase; el resto en defaults de LightGBM.
Se usa lgb.train con nombres canónicos y el Dataset se reconstruye en cada ajuste (feature_pre_filter depende de
min_data_in_leaf).
"""
from __future__ import annotations

import gc
import hashlib
import json
import time

import lightgbm as lgb
import numpy as np

from experimentos.h3.sensibilidad_muestra import rutas

SEMILLA = 20261102
HILOS = 4
N_CONFIG = 20
ARBOLES = 100
FIJOS = {"objective": "binary", "metric": "auc", "bagging_freq": 1, "num_threads": HILOS, "seed": SEMILLA,
         "verbosity": -1}
GRILLA = rutas.REFERENCIA / "grilla_06.json"


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sig6(x: float) -> float:
    return float(f"{x:.6g}")


def generar_configuraciones(rng: np.random.Generator) -> list[dict]:
    out = []
    for i in range(N_CONFIG):
        out.append({
            "id": i,
            "num_leaves": int(rng.integers(8, 65)),
            "learning_rate": sig6(float(np.exp(rng.uniform(np.log(0.01), np.log(0.10))))),
            "min_data_in_leaf": int(np.clip(round(float(np.exp(rng.uniform(np.log(100), np.log(2000))))), 100, 2000)),
            "feature_fraction": sig6(float(rng.uniform(0.5, 1.0))),
            "bagging_fraction": sig6(float(rng.uniform(0.5, 1.0))),
        })
    return out


def regenerar() -> tuple[list[dict], str]:
    rng_config = np.random.default_rng(np.random.SeedSequence(SEMILLA).spawn(2)[1])
    regen = generar_configuraciones(rng_config)
    return regen, sha256_bytes(json.dumps(regen, sort_keys=True).encode())


def cargar_grilla() -> tuple[list[dict], str]:
    """Las 20 configuraciones de 06: regeneradas y comparadas con la grilla versionada. Cualquier diferencia bloquea."""
    guardado = json.loads(GRILLA.read_text(encoding="utf-8"))
    params06 = json.loads((rutas.REFERENCIA / "corrida_06.json").read_text(encoding="utf-8"))["parametros_por_id"]
    regen, huella = regenerar()
    problemas = []
    if guardado["configuraciones"] != regen:
        problemas.append("las regeneradas no son iguales a grilla_06.json")
    if guardado["sha256"] != huella:
        problemas.append("sha256 distinto al guardado")
    if [c["id"] for c in guardado["configuraciones"]] != list(range(N_CONFIG)):
        problemas.append("ids fuera de orden")
    if any(params06.get(str(c["id"])) != {k: v for k, v in c.items() if k != "id"} for c in regen):
        problemas.append("la corrida 06 usó otros parámetros (corrida_06.json)")
    if guardado["fijos"] != FIJOS or guardado["arboles"] != ARBOLES:
        problemas.append("parámetros fijos o árboles distintos a 06")
    if problemas:
        raise RuntimeError(f"BLOQUEO: no se pueden recuperar las configuraciones de 06: {problemas}")
    return regen, huella


def params_de(cfg: dict) -> dict:
    return {**FIJOS, **{k: v for k, v in cfg.items() if k != "id"}}


def efectivos(booster: lgb.Booster) -> dict:
    txt = booster.model_to_string()
    ini, fin = txt.find("parameters:\n"), txt.find("end of parameters")
    out = {}
    for linea in txt[ini:fin].splitlines()[1:]:
        if linea.startswith("[") and ": " in linea:
            k, v = linea[1:-1].split(": ", 1)
            out[k] = v
    return out


def verificar_parametros(pedidos: dict, ef: dict) -> dict:
    """Cada parámetro pedido debe figurar con el mismo valor en la configuración efectiva del modelo."""
    malos = {}
    for k, v in {**pedidos, "num_iterations": ARBOLES}.items():
        if k not in ef:
            malos[k] = ("ausente", v)
        elif isinstance(v, float):
            if float(ef[k]) != v:
                malos[k] = (ef[k], v)
        elif str(v) != ef[k]:
            malos[k] = (ef[k], v)
    # defaults que no deben haber cambiado por algún alias
    for k, v in {"is_unbalance": "0", "scale_pos_weight": "1", "early_stopping_round": "0", "boosting": "gbdt",
                 "lambda_l1": "0", "lambda_l2": "0", "max_depth": "-1", "min_sum_hessian_in_leaf": "0.001",
                 "max_bin": "255", "feature_pre_filter": "1"}.items():
        if ef.get(k) != v:
            malos[k] = (ef.get(k), v)
    if malos:
        raise RuntimeError(f"parámetros que no llegaron a LightGBM como se pidieron: {malos}")
    return {"verificados": sorted({**pedidos, "num_iterations": ARBOLES}), "ok": True}


def ajustar(X, y, pred: list[str], params: dict) -> tuple[lgb.Booster, dict]:
    t = time.perf_counter()
    ds = lgb.Dataset(X, label=y, feature_name=pred, free_raw_data=True, params={"verbosity": -1})
    ds.construct()
    t_ds = time.perf_counter() - t
    t = time.perf_counter()
    booster = lgb.train(params, ds, num_boost_round=ARBOLES)
    t_tr = time.perf_counter() - t
    del ds
    gc.collect()
    return booster, {"dataset_s": round(t_ds, 1), "entrenamiento_s": round(t_tr, 1)}
