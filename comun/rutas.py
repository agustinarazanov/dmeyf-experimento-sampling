"""Rutas de cada experimento, siempre desde la raíz del repo (no desde `__file__` de quien las usa)."""

from __future__ import annotations

from pathlib import Path

from comun import baseline as bl

RAIZ = Path(__file__).resolve().parents[1]
EXPERIMENTOS = RAIZ / "experimentos"


def experimento(exp: str) -> Path:
    return EXPERIMENTOS / exp


def ledger(exp: str) -> Path:
    return experimento(exp) / "ledger"


def ledger_datos(exp: str) -> Path:
    """Donde van las predicciones de test: `DATOS_DIR/ledger/<exp>/`, fuera del repo (D18). Lee `DATOS_DIR` cada vez,
    porque los tests y el smoke lo reemplazan."""
    return bl.DATOS_DIR / "ledger" / exp


def prediccion(exp: str, rel: str) -> Path:
    """Ruta absoluta de una predicción del ledger de `exp`, dada la ruta relativa que guarda `predicciones_201910`: en
    `DATOS_DIR` si está ahí y, si no, en la ruta vieja dentro del repo."""
    nueva = ledger_datos(exp) / rel
    return nueva if nueva.exists() else ledger(exp) / rel


def docs(exp: str) -> Path:
    return experimento(exp) / "docs"


def informe(exp: str) -> Path:
    return experimento(exp) / "informe"
