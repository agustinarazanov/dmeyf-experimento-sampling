"""Rutas de cada experimento, siempre desde la raíz del repo (no desde `__file__` de quien las usa)."""

from __future__ import annotations

from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
EXPERIMENTOS = RAIZ / "experimentos"


def experimento(exp: str) -> Path:
    return EXPERIMENTOS / exp


def ledger(exp: str) -> Path:
    return experimento(exp) / "ledger"


def docs(exp: str) -> Path:
    return experimento(exp) / "docs"


def informe(exp: str) -> Path:
    return experimento(exp) / "informe"
