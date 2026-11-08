"""Los cuatro métodos como funciones `(datos, params)`.

Cada una recibe el train completo y devuelve las filas con las que se entrena y los parámetros de LightGBM que la variante
fija encima del baseline. Valen igual en los trials de Optuna y en el final. `docs/diseno.md` § Variantes.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from comun import variantes, muestreo

METODOS = ("uniforme", "bagging", "goss", "opt-muestra")


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


FUNCIONES = {"uniforme": uniforme, "bagging": bagging, "goss": goss, "opt-muestra": opt_muestra}


def validar(metodo: str, tasa: float) -> None:
    """Falla antes de cargar datos nombrando el parámetro inválido."""
    if metodo not in METODOS:
        raise ValueError(f"--metodo inválido: {metodo!r} (opciones: {', '.join(METODOS)})")
    if not 0 < tasa <= 1:
        raise ValueError(f"--tasa inválida: {tasa} (tiene que estar en (0, 1])")
    if metodo == "opt-muestra" and tasa >= 1:
        raise ValueError("--tasa inválida para opt-muestra: la muestra de optimización tiene que ser r < 1")


def sin_bagging_fraction(metodo: str) -> bool:
    """`bagging` y `goss` sacan `bagging_fraction` del espacio de Optuna (adaptación de H2)."""
    return metodo in ("bagging", "goss")


def estudio(metodo: str, tasa: float) -> str:
    """Nombre del estudio de Optuna, del registro de variantes. `opt-muestra` usa el de `uniforme` con la misma tasa."""
    return variantes.variante(variantes.nombre(metodo, tasa)).estudio


def variante(metodo: str, tasa: float) -> str:
    """Nombre de la variante de la grilla (`C-rep` se pide con `--variante`). Falla nombrándolo si no está en el registro."""
    return variantes.variante(variantes.nombre(metodo, tasa)).nombre
