"""Ganancia de la competencia: acumulada, curva de corte y ganancia a envíos fijos.

Convención única: se estimula a los `envios` clientes de mayor score; cada BAJA+2 estimulado suma
`GANANCIA_ACIERTO` y cada estimulado que no era BAJA+2 resta `COSTO_ESTIMULO`.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

#: Valores de la cátedra (copiados de `competencia-2/src/fe_panel.py`): 2,2 M de valor anual del cliente por 50% de
#: aceptación, menos el costo del estímulo. Si la cátedra los cambia para 2019, se cambian acá y se recalcula desde las
#: curvas guardadas (`experimentos/sampling_1/corridas.md`).
GANANCIA_ACIERTO: int = 1_072_500
COSTO_ESTIMULO: int = 27_500

#: Resolución de las curvas que se guardan por corrida: de 0 a `CURVA_HASTA` envíos cada `CURVA_PASO`.
CURVA_HASTA: int = 30_000
CURVA_PASO: int = 50


def aporte(es_baja2: np.ndarray) -> np.ndarray:
    """Ganancia individual de estimular a cada cliente."""
    return np.where(np.asarray(es_baja2, dtype=bool), GANANCIA_ACIERTO, -COSTO_ESTIMULO).astype("float64")


def ganancia_acumulada(scores: np.ndarray, es_baja2: np.ndarray) -> np.ndarray:
    """`g[k-1]` = ganancia de estimular a los k clientes de mayor score. Empates por orden de aparición."""
    scores = np.asarray(scores)
    orden = np.argsort(-scores, kind="stable")
    return np.cumsum(aporte(es_baja2)[orden])


def ganancia(scores: np.ndarray, es_baja2: np.ndarray, envios: int) -> float:
    """Ganancia al estimular a los `envios` de mayor score (con `envios` > n se estimula a todos)."""
    g = ganancia_acumulada(scores, es_baja2)
    if envios <= 0:
        return 0.0
    return float(g[min(envios, len(g)) - 1])


def curva_de_corte(
    scores: np.ndarray, es_baja2: np.ndarray, hasta: int = CURVA_HASTA, paso: int = CURVA_PASO
) -> pd.DataFrame:
    """Ganancia en `envios` = paso, 2·paso, …, hasta (recortado al largo de los datos)."""
    g = ganancia_acumulada(scores, es_baja2)
    hasta = min(hasta, len(g))
    envios = np.arange(paso, hasta + 1, paso)
    return pd.DataFrame({"envios": envios, "ganancia": g[envios - 1]})


def ganancia_maxima(curva: pd.DataFrame) -> tuple[int, float]:
    """(envíos, ganancia) del máximo de la curva."""
    i = int(curva["ganancia"].to_numpy().argmax())
    return int(curva["envios"].iloc[i]), float(curva["ganancia"].iloc[i])
