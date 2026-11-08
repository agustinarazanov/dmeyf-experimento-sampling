"""Bandas de curvas de ganancia (mínimo, mediana, máximo entre semillas) de cada variante junto al control.

    python scripts/graficar.py [--mes 201910] [--variantes U0.5 B0.5 ...]

Lee `ledger/resultados.csv` y las curvas; escribe un PNG por variante en `informe/figuras/`.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

EXPERIMENTO = Path(__file__).resolve().parents[1]
LEDGER = EXPERIMENTO / "ledger"


def banda(finales: pd.DataFrame, variante: str, mes: int) -> pd.DataFrame:
    curvas = [
        pd.read_csv(LEDGER / r).set_index("envios")["ganancia"]
        for r in finales.loc[finales["variante"] == variante, f"curva_{mes}"]
    ]
    if not curvas:
        raise ValueError(f"no hay curvas de la variante {variante}")
    m = pd.concat(curvas, axis=1)
    return pd.DataFrame({"min": m.min(axis=1), "mediana": m.median(axis=1), "max": m.max(axis=1)})


def graficar(variante: str, finales: pd.DataFrame, mes: int, destino: Path) -> Path:
    fig, ax = plt.subplots(figsize=(7, 4))
    for nombre, color in (("C", "#555555"), (variante, "#c4501b")):
        b = banda(finales, nombre, mes)
        ax.fill_between(b.index, b["min"], b["max"], color=color, alpha=0.2)
        ax.plot(b.index, b["mediana"], color=color, label=f"{nombre} (mediana, banda mín–máx)")
    ax.set_xlabel("envíos")
    ax.set_ylabel(f"ganancia {mes}")
    ax.legend()
    ax.set_title(f"{variante} vs control")
    destino.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(destino, dpi=150)
    plt.close(fig)
    return destino


def main() -> None:
    global LEDGER
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--mes", type=int, default=201910)
    p.add_argument("--variantes", nargs="*")
    p.add_argument("--ledger", type=Path, default=LEDGER)
    a = p.parse_args()
    LEDGER = a.ledger
    res = pd.read_csv(LEDGER / "resultados.csv")
    finales = res[res["etapa"] == "final"]
    variantes = a.variantes or sorted(set(finales["variante"]) - {"C", "C-rep"})
    for b in variantes:
        print(graficar(b, finales, a.mes, EXPERIMENTO / "informe" / "figuras" / f"curva_{b}_{a.mes}.png"))


if __name__ == "__main__":
    main()
