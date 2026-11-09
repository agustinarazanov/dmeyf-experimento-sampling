"""RECONSTRUIDO: análisis del presupuesto de 900 s (`design.md` D2). El script de Luis no lo calcula; su resumen reporta
"más de 60 semillas" en 900 s para el fast-retrain.

    K = ⌊(900 − T_opt) / T_final medio⌋ semillas; ensamble de las primeras K (el que escribe `validacion.py`).

Si K > 50, `validacion.py --presupuesto 900` corre semillas extra con la fórmula de Luis (`110017 + i·19937`, i ≥ 40).
Nada acá elige nada con 201910: K sale de tiempos y los dos meses se informan lado a lado (D9).

    python -m experimentos.sampling_1.exploratorios.validacion_50_semillas.presupuesto [--hp original] [--salida DIR]
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import pandas as pd

PRESUPUESTO_S = 900.0


def k_presupuesto(t_opt: float, t_final_medio: float, presupuesto: float = PRESUPUESTO_S) -> int:
    """Semillas finales que entran en `presupuesto` después de optimizar `t_opt` segundos (0 si ni la optimización entra)."""
    if t_final_medio <= 0:
        raise ValueError(f"tiempo final medio inválido: {t_final_medio}")
    return max(0, math.floor((presupuesto - t_opt) / t_final_medio))


def tabla_presupuesto(resumen: pd.DataFrame, ensambles: pd.DataFrame, presupuesto: float = PRESUPUESTO_S) -> pd.DataFrame:
    """Una fila por estrategia: T_opt, T_final medio, K, semillas disponibles y el ensamble de las primeras K en los dos meses.

    Si K es mayor que las semillas corridas, el ensamble se informa con las disponibles y `k_alcanzado` es False.
    """
    filas = []
    for s, g in resumen.groupby("estrategia"):
        t_opt, t_fin = float(g["t_opt_s"].iloc[0]), float(g["tiempo_s"].mean())
        k = k_presupuesto(t_opt, t_fin, presupuesto)
        e = ensambles[ensambles["estrategia"] == s].sort_values("k")
        usado = min(k, len(e))
        filas.append({
            "estrategia": int(s), "nombre": g["nombre"].iloc[0], "t_opt_s": t_opt, "t_final_medio_s": t_fin,
            "k_presupuesto": k, "semillas_corridas": len(e), "k_alcanzado": k <= len(e),
            "ens_k_201908": float(e["g_201908"].iloc[usado - 1]) if usado else float("nan"),
            "ens_k_201910": float(e["g_201910"].iloc[usado - 1]) if usado else float("nan"),
        })
    return pd.DataFrame(filas).sort_values("estrategia").reset_index(drop=True)


def main(argv: list[str] | None = None) -> None:
    from . import validacion as va   # acá y no arriba: `validacion` importa este módulo
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--hp", choices=["original", "ledger"], default="original")
    p.add_argument("--salida", type=Path, default=va.SALIDA)
    p.add_argument("--presupuesto", type=float, default=PRESUPUESTO_S)
    a = p.parse_args(argv)
    resumen, ensambles = va.leer(a.salida, a.hp)
    tabla = tabla_presupuesto(resumen, ensambles, a.presupuesto)
    destino = a.salida / f"presupuesto_{a.hp}.csv"
    tabla.to_csv(destino, index=False)
    print(tabla.to_string(index=False))
    print(destino)


if __name__ == "__main__":
    main()
