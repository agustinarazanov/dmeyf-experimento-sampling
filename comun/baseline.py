"""El baseline oficial (Bolaños, 28-oct, Zulip 208135) y las decisiones de `experimentos/control/README.md`.

Solo constantes y el espacio de búsqueda; nada de este módulo lee datos.
"""

from __future__ import annotations

import os
from pathlib import Path

# --- meses -----------------------------------------------------------------

#: Solo historia para los lags; sin target en el panel.
MESES_HISTORIA: list[int] = [201901, 201902]
#: Meses con los que `optimizar` busca hiperparámetros (D1). No incluye 201907: la validación es 201908.
MESES_TRAIN_OPT: list[int] = [201903, 201904, 201905, 201906]
#: Meses con los que entrena el `final` (D1): los de optimización más 201907 y 201908. Registrados en el ledger como `meses_final`.
MESES_TRAIN_FINAL: list[int] = [201903, 201904, 201905, 201906, 201907, 201908]
#: Ventana de un final como la registra el ledger en `meses_final`: `201903-201908`.
def ventana(meses: list[int]) -> str:
    return f"{meses[0]}-{meses[-1]}"


VENTANA_FINAL: str = ventana(MESES_TRAIN_FINAL)
MES_VALIDACION: int = 201908
MES_TEST: int = 201910
#: Meses que quedan en el panel (el target de 201910 mira hasta 201912 en el crudo, pero esos meses no se usan).
MESES_PANEL: list[int] = sorted(set(MESES_HISTORIA + MESES_TRAIN_FINAL + [MES_VALIDACION, MES_TEST]))
#: Meses del crudo que alcanzan para lags (desde 201901) y para el target de 201910 (hasta 201912).
CRUDO_DESDE: int = 201901
CRUDO_HASTA: int = 201912

# --- target ------------------------------------------------------------------

POSITIVOS: tuple[str, ...] = ("BAJA+1", "BAJA+2")
LAGS: int = 2  # lag1, lag2, delta1, delta2

# --- datos -------------------------------------------------------------------

DATOS_DIR: Path = Path(os.environ.get("DATOS_DIR", "~/datos/experimentos-dmeyf")).expanduser()
URL_CRUDO: str = "https://storage.googleapis.com/open-courses/dmeyf2026-9c6f/competencia_02_crudo.csv.gz"

# --- corrida -----------------------------------------------------------------

SEMILLA_OPTUNA: int = 0  # también sortea la muestra de optimización; ninguna semilla final la usa
#: Las 10 oficiales de la ronda 201903-201906 y, a continuación, 10 más (110017 + i·19937; 110017 … 289450, sin choques).
#: El orden importa: las primeras 10 son las de la ronda anterior (D5).
SEMILLAS_OFICIALES: list[int] = [100003, 200003, 300007, 400009, 500009, 600011, 700001, 800011, 900001, 999983]
SEMILLAS_FINALES: list[int] = SEMILLAS_OFICIALES + [110017 + i * 19937 for i in range(10)]
#: Corte de envíos fijo para δ y la ganancia de la ronda 201903-201908 (D3): el N* de la ronda anterior, calculado en
#: validación (201908) con la media de las curvas de los `C`. Los finales nuevos no predicen 201908 fuera de muestra.
N_ESTRELLA: int = 3300
N_TRIALS: int = 40
NUM_THREADS: int = 8

#: Defaults de LightGBM salvo lo declarado en `hipotesis.md` § Control. `seed` lo pone cada etapa.
PARAMS_FIJOS: dict = {
    "objective": "binary",
    "num_iterations": 100,
    "num_threads": NUM_THREADS,
    "verbosity": -1,
    "deterministic": True,
    "force_col_wise": True,
}
#: Parámetros del `lgb.Dataset` (Optuna cambia `min_data_in_leaf` entre trials).
PARAMS_DATASET: dict = {"feature_pre_filter": False, "verbosity": -1}

#: Espacio de búsqueda: nombre -> (tipo, mínimo, máximo, escala log). `experimentos/control/README.md`.
ESPACIO: dict[str, tuple[str, float, float, bool]] = {
    "num_leaves": ("int", 8, 1024, True),
    "learning_rate": ("float", 0.01, 0.3, True),
    "min_data_in_leaf": ("int", 10, 5000, True),
    "feature_fraction": ("float", 0.1, 1.0, False),
    "bagging_fraction": ("float", 0.1, 1.0, False),
}


def sugerir(trial, sin_bagging_fraction: bool = False) -> dict:
    """Hiperparámetros de un trial de Optuna. Sin `bagging_fraction` es el espacio de 4 hp de H2."""
    hp: dict = {}
    for nombre, (tipo, lo, hi, log) in ESPACIO.items():
        if sin_bagging_fraction and nombre == "bagging_fraction":
            continue
        if tipo == "int":
            hp[nombre] = trial.suggest_int(nombre, int(lo), int(hi), log=log)
        else:
            hp[nombre] = trial.suggest_float(nombre, lo, hi, log=log)
    return hp


def con_bagging(hp: dict) -> dict:
    """El baseline pide `bagging_freq ≥ 1` cuando se optimiza `bagging_fraction`."""
    return {**hp, "bagging_freq": 1}
