"""Los cuatro métodos como funciones `(datos, params)`.

Cada una recibe el train completo y devuelve las filas con las que se entrena y los parámetros de LightGBM que la variante
fija encima del baseline. Valen igual en los trials de Optuna y en el final. `docs/diseno.md` § Variantes.
"""

from __future__ import annotations

import time

import numpy as np
import pandas as pd

from comun import baseline as bl
from comun import datos as dt
from comun import muestreo, variantes

METODOS = ("uniforme", "bagging", "goss", "opt-muestra", "opt-muestra-reescalado", "opt-muestra-lineal", "opt-muestra-cliente",
           "clase-dificil", "clase-uniforme", "fast-retrain", "fast-retrain-opt")
#: Los métodos de H3 optimizan sobre una muestra y entrenan con todo; los de H4 (`incorporar-aportes` D3) también, salvo
#: `fast-retrain`, que usa el estudio `U{r}` y entrena con las bajas y una fracción de las CONTINUA con peso.
METODOS_H3 = ("opt-muestra", "opt-muestra-reescalado", "opt-muestra-lineal", "opt-muestra-cliente")
METODOS_H4 = ("clase-dificil", "clase-uniforme", "fast-retrain", "fast-retrain-opt")
#: Métodos de H4 con estudio propio (no reusan `U{r}`): `fast-retrain-opt` optimiza sobre la receta de `fast-retrain` (D11).
METODOS_ESTUDIO_PROPIO = ("opt-muestra-cliente", "clase-dificil", "clase-uniforme", "fast-retrain-opt")
#: Fracción de CONTINUA del final de `fast-retrain`; su peso es 1/f.
FRACCION_FAST_RETRAIN = 0.5
#: Sonda de H4H: 40 árboles, 31 hojas, `learning_rate` 0,08 sobre el 10 % uniforme del train.
TASA_SONDA = 0.1
PARAMS_SONDA = {"num_iterations": 40, "num_leaves": 31, "learning_rate": 0.08}
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


def opt_muestra_lineal(train: pd.DataFrame, tasa: float, semilla: int) -> tuple[pd.DataFrame, dict, np.ndarray]:
    """H3L: igual que `opt-muestra`; `ajustar_hp` multiplica `min_data_in_leaf` por 1/r."""
    return opt_muestra(train, tasa, semilla)


def opt_muestra_reescalado(train: pd.DataFrame, tasa: float, semilla: int) -> tuple[pd.DataFrame, dict, np.ndarray]:
    """H3R: igual que `opt-muestra`; el reescalado de `min_data_in_leaf` lo hace `ajustar_hp` sobre los hp del estudio."""
    return opt_muestra(train, tasa, semilla)


def cliente(train: pd.DataFrame, tasa: float, semilla: int) -> tuple[pd.DataFrame, dict, np.ndarray]:
    """H3K, búsqueda: el `tasa` de los clientes del train, con todas sus filas."""
    idx = muestreo.indices_por_cliente(train[dt.ID].to_numpy(), tasa, semilla)
    return train.iloc[idx], {"bagging_freq": 1}, idx


def sonda_pozo(train: pd.DataFrame, semilla: int) -> tuple[np.ndarray, float]:
    """Pozo de negativos difíciles y segundos que tardó la sonda (entrenar con el 10 % uniforme y predecir todo el train)."""
    import lightgbm as lgb
    t0 = time.perf_counter()
    cols = dt.columnas_predictoras(train)
    idx = muestreo.indices_uniformes(len(train), TASA_SONDA, semilla)
    y = train[dt.Y].to_numpy()
    ds = lgb.Dataset(dt.matriz(train.iloc[idx], cols), label=y[idx], params=bl.PARAMS_DATASET)
    modelo = lgb.train({**bl.PARAMS_FIJOS, **PARAMS_SONDA, "seed": semilla}, ds)
    pozo = muestreo.pozo_dificil(y, modelo.predict(dt.matriz(train, cols)))
    return pozo, time.perf_counter() - t0


def clase_dificil(train: pd.DataFrame, tasa: float, semilla: int, pozo: np.ndarray | None = None
                  ) -> tuple[pd.DataFrame, dict, np.ndarray]:
    """H4H, búsqueda: todas las bajas y el `tasa` de las CONTINUA, sorteadas dentro del pozo de la sonda de esa semilla."""
    if pozo is None:
        pozo, _ = sonda_pozo(train, semilla)
    idx = muestreo.indices_por_clase(train[dt.Y].to_numpy(), tasa, semilla, pozo)
    return train.iloc[idx], {"bagging_freq": 1}, idx


def clase_uniforme(train: pd.DataFrame, tasa: float, semilla: int) -> tuple[pd.DataFrame, dict, np.ndarray]:
    """H4U, búsqueda: igual que H4H pero las CONTINUA salen al azar entre todas."""
    idx = muestreo.indices_por_clase(train[dt.Y].to_numpy(), tasa, semilla)
    return train.iloc[idx], {"bagging_freq": 1}, idx


def fast_retrain(train: pd.DataFrame, tasa: float, semilla: int) -> tuple[pd.DataFrame, dict, np.ndarray]:
    """H4F, final: todas las bajas y la mitad de las CONTINUA (sorteo con la semilla final); el peso lo da `pesos`.
    H4O (`fast-retrain-opt`): la misma receta como muestra de búsqueda (semilla de la réplica) y como final (semilla final)."""
    idx = muestreo.indices_por_clase(train[dt.Y].to_numpy(), FRACCION_FAST_RETRAIN, semilla)
    return train.iloc[idx], {"bagging_freq": 1}, idx


def pesos(metodo: str, datos: pd.DataFrame) -> np.ndarray | None:
    """Peso por fila: 1/f en las CONTINUA de `fast-retrain` y `fast-retrain-opt` (en el final y en cada trial de
    `fast-retrain-opt`), nada en los demás métodos. La validación nunca lleva pesos."""
    if metodo not in ("fast-retrain", "fast-retrain-opt"):
        return None
    return muestreo.peso_inverso(datos[dt.Y].to_numpy(), FRACCION_FAST_RETRAIN)


#: Función del final de cada método (y de la muestra de optimización de los que no son de H3 ni de H4).
FUNCIONES = {"uniforme": uniforme, "bagging": bagging, "goss": goss, "opt-muestra": opt_muestra,
             "opt-muestra-reescalado": opt_muestra_reescalado, "opt-muestra-lineal": opt_muestra_lineal,
             "opt-muestra-cliente": opt_muestra, "clase-dificil": opt_muestra, "clase-uniforme": opt_muestra,
             "fast-retrain": fast_retrain, "fast-retrain-opt": fast_retrain}
#: Muestra de optimización de los métodos cuyo estudio no es `U{r}`.
FUNCIONES_OPT = {**FUNCIONES, "opt-muestra-cliente": cliente, "clase-dificil": clase_dificil, "clase-uniforme": clase_uniforme}


def metodo_optimizacion(metodo: str) -> str:
    """Método con el que se corre la etapa `optimizar`: H3 y `fast-retrain` reusan el estudio `U{r}` (`uniforme`); H3K y los
    de clase tienen estudio propio y se quedan con su nombre."""
    if metodo in METODOS_H3 + METODOS_H4 and metodo not in METODOS_ESTUDIO_PROPIO:
        return "uniforme"
    return metodo


def ajustar_hp(metodo: str, tasa: float, hp: dict) -> dict:
    """Hiperparámetros con los que se entrena el final. Solo los reescalados los tocan: `min_data_in_leaf` × √(1/r)
    (`opt-muestra-reescalado`) o × 1/r (`opt-muestra-lineal`), redondeado y recortado a [1; 8000]; el resto sale del estudio."""
    if metodo not in ("opt-muestra-reescalado", "opt-muestra-lineal"):
        return dict(hp)
    lo, hi = MIN_DATA_REESCALADO
    factor = (1 / tasa) ** 0.5 if metodo == "opt-muestra-reescalado" else 1 / tasa
    nuevo = int(round(hp["min_data_in_leaf"] * factor))
    return {**hp, "min_data_in_leaf": min(hi, max(lo, nuevo))}


def validar(metodo: str, tasa: float) -> None:
    """Falla antes de cargar datos nombrando el parámetro inválido."""
    if metodo not in METODOS:
        raise ValueError(f"--metodo inválido: {metodo!r} (opciones: {', '.join(METODOS)})")
    if not 0 < tasa <= 1:
        raise ValueError(f"--tasa inválida: {tasa} (tiene que estar en (0, 1])")
    if metodo in METODOS_H3 + METODOS_H4 and tasa >= 1:
        raise ValueError(f"--tasa inválida para {metodo}: la muestra de optimización tiene que ser r < 1")
    if metodo == "fast-retrain-opt" and tasa != FRACCION_FAST_RETRAIN:
        raise ValueError(f"--tasa inválida para {metodo}: es la fracción f de CONTINUA y vale {FRACCION_FAST_RETRAIN}")


def sin_bagging_fraction(metodo: str) -> bool:
    """`bagging` y `goss` sacan `bagging_fraction` del espacio de Optuna (adaptación de H2)."""
    return metodo in ("bagging", "goss")


def estudio(metodo: str, tasa: float) -> str:
    """Nombre del estudio de Optuna, del registro de variantes. `opt-muestra` usa el de `uniforme` con la misma tasa."""
    return variantes.variante(variantes.nombre(metodo, tasa)).estudio


def variante(metodo: str, tasa: float) -> str:
    """Nombre de la variante de la grilla (`C-rep` se pide con `--variante`). Falla nombrándolo si no está en el registro."""
    return variantes.variante(variantes.nombre(metodo, tasa)).nombre
