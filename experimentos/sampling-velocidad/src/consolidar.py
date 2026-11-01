"""Consolida el ledger del experimento.

    python -m src.consolidar

Lee `ledger/corridas/*.csv` y escribe `ledger/resultados.csv` (corridas válidas, sin duplicados por clave),
`ledger/reemplazadas.csv`, `ledger/estudios.csv` (hiperparámetros y tiempo de cada estudio) y `ledger/apareado.csv`
(Δ contra el control por semilla, con N*, δ y veredicto). Todo sale de acá; nada se calcula a mano.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from comun import ledger as lg

LEDGER = Path(__file__).resolve().parents[1] / "ledger"


def consolidar(ledger: Path = LEDGER) -> dict[str, pd.DataFrame]:
    corridas = lg.leer_corridas(ledger / "corridas")
    resultados, reemplazadas = lg.consolidar_corridas(corridas)
    resultados.to_csv(ledger / "resultados.csv", index=False)
    reemplazadas.to_csv(ledger / "reemplazadas.csv", index=False)
    salida = {"resultados": resultados, "reemplazadas": reemplazadas}
    finales = resultados[resultados["etapa"] == "final"]
    estudios = resultados[resultados["etapa"] == "optimizar"]
    estudios.to_csv(ledger / "estudios.csv", index=False)
    if finales["brazo"].eq(lg.CONTROL).any():
        leer = lambda ruta: lg.leer_curva(ledger, ruta)
        n_estrella = lg.corte_control(finales, leer)
        con_g = lg.agregar_ganancia(finales, leer, n_estrella)
        tabla = lg.apareado(con_g, estudios)
        tabla.insert(1, "n_estrella", n_estrella)
        tabla.to_csv(ledger / "apareado.csv", index=False)
        salida["apareado"] = tabla
    return salida


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--ledger", type=Path, default=LEDGER)
    a = p.parse_args()
    r = consolidar(a.ledger)
    print(f"{len(r['resultados'])} corridas válidas, {len(r['reemplazadas'])} reemplazadas, "
          f"{len(r['apareado']) if 'apareado' in r else 0} brazos apareados")


if __name__ == "__main__":
    main()
