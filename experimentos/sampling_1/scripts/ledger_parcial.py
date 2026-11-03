"""Arma un ledger parcial de la fase 1 (C y H3) para probar `src/reporte.py` con brazos pendientes (tarea 6.0).

    python experimentos/sampling_1/scripts/ledger_parcial.py DESTINO

Copia las filas de C, H3-0.25 y H3-0.1 de `resultados.csv` y `apareado.csv` y enlaza `curvas/`.
"""

import sys
from pathlib import Path

import pandas as pd

FASE1 = ["C", "H3-0.25", "H3-0.1"]
src = Path(__file__).resolve().parents[1] / "ledger"
dst = Path(sys.argv[1])
dst.mkdir(parents=True, exist_ok=True)
for nombre in ("resultados.csv", "apareado.csv"):
    t = pd.read_csv(src / nombre)
    t[t["brazo"].isin(FASE1)].to_csv(dst / nombre, index=False)
if not (dst / "curvas").exists():
    (dst / "curvas").symlink_to(src / "curvas")
print(dst)
