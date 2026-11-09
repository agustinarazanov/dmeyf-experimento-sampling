"""Los cuatro métodos como funciones `(datos, params)`.

Cada una recibe el train completo y devuelve las filas con las que se entrena y los parámetros de LightGBM que la variante
fija encima del baseline. Valen igual en los trials de Optuna y en el final. `docs/diseno.md` § Variantes.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from comun import variantes, muestreo

METODOS = ("uniforme", "bagging", "goss", "opt-muestra", "opt-muestra-reescalado")
#: Los dos métodos de H3 optimizan sobre una muestra (como `uniforme`) y entrenan con todo.
METODOS_H3 = ("opt-muestra", "opt-muestra-reescalado")
#: `min_data_in_leaf` reescalado queda en [1; 8000] (`h3-semillas-optuna` D2).
MIN_DATA_REESCALADO = (1, 8000)


def uniforme(train: pd.DataFrame, tasa: float, semilla: int) -> tuple[pd.DataFrame, dict, np.ndarray]:
    """H1: muestra uniforme de tasa r; `bagging_fraction` sigue en el espacio de Optuna con `bagging_freq = 1`."""
    idx = muestreo.indices_uniformes(len(train), tasa, semilla)
    return train.iloc[idx], {"bagging_freq": 1}, idx


def bagging(train: pd.DataFrame, tasa: float, semilla: int) -> tuple[pd.DataFrame, dict, np.ndarray]:
    """H2: todas las filas; cada árbol ve una fracción `tasa` (`bagging_fraction` fijo, `bagging_freq = 1`)."""
    return train, {"bagging_fraction": tasa, "bagging_freq": 1}, np.arange(len(train))


def goss(train: pd.DataFrame, tasa: float, semilla: int) -> tuple[pd.DataFrame, dict, np.ndarray]:
    """H2 descriptivo: GOSS con `top_rate`/`other_rate` de LightGBM v4 y sin bagging."""
    return train, {"data_sample_strategy": "goss", "top_rate": 0.2, "other_rate": 0.1}, np.arange(len(train))


def opt_muestra(train: pd.DataFrame, tasa: float, semilla: int) -> tuple[pd.DataFrame, dict, np.ndarray]:
    """H3, etapa final: se entrena con todo y con los hp salidos de la muestra (la tasa solo elige el estudio)."""
    return train, {"bagging_freq": 1}, np.arange(len(train))


def opt_muestra_reescalado(train: pd.DataFrame, tasa: float, semilla: int) -> tuple[pd.DataFrame, dict, np.ndarray]:
    """H3R: igual que `opt-muestra`; el reescalado de `min_data_in_leaf` lo hace `ajustar_hp` sobre los hp del estudio."""
    return opt_muestra(train, tasa, semilla)


FUNCIONES = {"uniforme": uniforme, "bagging": bagging, "goss": goss, "opt-muestra": opt_muestra,
             "opt-muestra-reescalado": opt_muestra_reescalado}


def ajustar_hp(metodo: str, tasa: float, hp: dict) -> dict:
    """Hiperparámetros con los que se entrena el final. Solo `opt-muestra-reescalado` los toca: `min_data_in_leaf` × √(1/r),
    redondeado y recortado a [1; 8000]; el resto sale tal cual del estudio."""
    if metodo != "opt-muestra-reescalado":
        return dict(hp)
    lo, hi = MIN_DATA_REESCALADO
    nuevo = int(round(hp["min_data_in_leaf"] * (1 / tasa) ** 0.5))
    return {**hp, "min_data_in_leaf": min(hi, max(lo, nuevo))}


def validar(metodo: str, tasa: float) -> None:
    """Falla antes de cargar datos nombrando el parámetro inválido."""
    if metodo not in METODOS:
        raise ValueError(f"--metodo inválido: {metodo!r} (opciones: {', '.join(METODOS)})")
    if not 0 < tasa <= 1:
        raise ValueError(f"--tasa inválida: {tasa} (tiene que estar en (0, 1])")
    if metodo in METODOS_H3 and tasa >= 1:
        raise ValueError(f"--tasa inválida para {metodo}: la muestra de optimización tiene que ser r < 1")


def sin_bagging_fraction(metodo: str) -> bool:
    """`bagging` y `goss` sacan `bagging_fraction` del espacio de Optuna (adaptación de H2)."""
    return metodo in ("bagging", "goss")


def estudio(metodo: str, tasa: float) -> str:
    """Nombre del estudio de Optuna, del registro de variantes. `opt-muestra` usa el de `uniforme` con la misma tasa."""
    return variantes.variante(variantes.nombre(metodo, tasa)).estudio


def variante(metodo: str, tasa: float) -> str:
    """Nombre de la variante de la grilla (`C-rep` se pide con `--variante`). Falla nombrándolo si no está en el registro."""
    return variantes.variante(variantes.nombre(metodo, tasa)).nombre
