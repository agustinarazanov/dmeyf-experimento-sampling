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
