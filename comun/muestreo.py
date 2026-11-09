"""Muestreo uniforme sin estratificar por semilla, con hash de la muestra."""

from __future__ import annotations

import hashlib

import numpy as np


def indices_uniformes(n: int, tasa: float, semilla: int) -> np.ndarray:
    """Índices ordenados de round(n · tasa) filas elegidas al azar sin reposición, sin mirar la clase."""
    if not 0 < tasa <= 1:
        raise ValueError(f"tasa fuera de (0, 1]: {tasa}")
    if tasa == 1:
        return np.arange(n)
    k = int(round(n * tasa))
    return np.sort(np.random.default_rng(semilla).choice(n, size=k, replace=False))


def hash_muestra(indices: np.ndarray, n: int) -> str:
    """Hash corto de la muestra: depende de los índices y del tamaño del conjunto del que salen."""
    h = hashlib.sha256(np.asarray(indices, dtype="<i8").tobytes())
    h.update(str(n).encode())
    return h.hexdigest()[:16]


# --- muestras informadas por clase y por cliente (`incorporar-aportes` D3) ---------------------------------------------

#: Parte de los negativos que forma el pozo de negativos difíciles (los de mayor probabilidad según la sonda).
FRACCION_POZO = 0.35


def indices_por_cliente(clientes: np.ndarray, tasa: float, semilla: int) -> np.ndarray:
    """Índices ordenados de todas las filas de round(c · tasa) clientes sorteados sin reposición entre los c distintos."""
    if not 0 < tasa <= 1:
        raise ValueError(f"tasa fuera de (0, 1]: {tasa}")
    clientes = np.asarray(clientes)
    if tasa == 1:
        return np.arange(len(clientes))
    unicos = np.unique(clientes)
    k = int(round(len(unicos) * tasa))
    elegidos = np.random.default_rng(semilla).choice(unicos, size=k, replace=False)
    return np.flatnonzero(np.isin(clientes, elegidos))


def pozo_dificil(y: np.ndarray, prob: np.ndarray, fraccion: float = FRACCION_POZO) -> np.ndarray:
    """Índices ordenados del `fraccion` de los negativos con mayor `prob` (empates: gana el de menor índice)."""
    negativos = np.flatnonzero(np.asarray(y) == 0)
    k = int(round(len(negativos) * fraccion))
    orden = np.argsort(-np.asarray(prob)[negativos], kind="stable")
    return np.sort(negativos[orden[:k]])


def indices_por_clase(y: np.ndarray, tasa: float, semilla: int, pozo: np.ndarray | None = None) -> np.ndarray:
    """Índices ordenados de todos los positivos y de round(negativos · tasa) negativos sorteados al azar entre todos los
    negativos (`pozo=None`, uniforme) o dentro de `pozo` (difícil). La cantidad de cada clase no depende del pozo."""
    if not 0 < tasa <= 1:
        raise ValueError(f"tasa fuera de (0, 1]: {tasa}")
    y = np.asarray(y)
    positivos, negativos = np.flatnonzero(y == 1), np.flatnonzero(y == 0)
    k = int(round(len(negativos) * tasa))
    candidatos = negativos if pozo is None else np.asarray(pozo)
    if pozo is not None and (np.any(y[candidatos] != 0) or k > len(candidatos)):
        raise ValueError(f"el pozo ({len(candidatos)} negativos) no alcanza para {k} negativos o tiene positivos")
    elegidos = np.random.default_rng(semilla).choice(candidatos, size=k, replace=False)
    return np.sort(np.concatenate([positivos, elegidos]))


def peso_inverso(y: np.ndarray, fraccion: float) -> np.ndarray:
    """Peso 1 en los positivos y 1/f en los negativos: la proporción ponderada de la muestra es la del train completo."""
    if not 0 < fraccion <= 1:
        raise ValueError(f"fracción fuera de (0, 1]: {fraccion}")
    return np.where(np.asarray(y) == 1, 1.0, 1.0 / fraccion)
