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


def sanity(r: dict[str, pd.DataFrame]) -> list[tuple[str, bool, str]]:
    """Chequeos de la etapa corridas (tareas 5.1 a 5.4). Devuelve (chequeo, ok, detalle)."""
    res = r["resultados"]
    fin = res[res["etapa"] == "final"]
    out = []

    def chk(nombre: str, ok: bool, detalle: str) -> None:
        out.append((nombre, bool(ok), detalle))

    f1 = fin[fin["brazo"].isin(["C", "H3-0.25", "H3-0.1"])]
    chk("5.1 fase 1: 30 finales, una máquina y un commit",
        len(f1) == 30 and f1["maquina"].nunique() == 1 and f1["commit"].nunique() == 1,
        f"{len(f1)} filas, {f1['maquina'].nunique()} máquinas, {f1['commit'].nunique()} commits")
    brazos = ["U0.5", "U0.25", "U0.1", "U0.05", "B0.5", "B0.25", "B0.1", "GOSS"]
    chk("5.2-5.3 los 8 brazos de H1/H2 tienen 10 finales",
        all(len(fin[fin["brazo"] == b]) == 10 for b in brazos), "")
    full = fin["filas_train"].max()
    malas = [b for b, g in fin[fin["brazo"].str.startswith("U")].groupby("brazo")
             if not g["filas_train"].between(float(g["tasa"].iloc[0]) * full * 0.999,
                                             float(g["tasa"].iloc[0]) * full * 1.001).all()]
    chk("5.2 filas de train coinciden con la tasa (±0,1%)", not malas, f"fuera de tasa: {malas}")
    chk("5.2 sin codigo_sucio", not res["codigo_sucio"].astype(bool).any(), "")
    bg = res[res["brazo"].str.startswith(("B", "GOSS"))]
    chk("5.3 bagging_fraction fijo (no está en los hp optimizados)",
        not bg["hp"].str.contains("bagging").any(), f"{len(bg)} filas")
    chk("5.4 ninguna corrida exploratoria en resultados",
        res["id"].str.startswith("exp-").sum() == 0 and set(res["etapa"]) <= {"optimizar", "final"}
        and res["valida"].astype(bool).all(), "")
    chk("5.4 tiempos: un solo tipo de máquina", res["maquina"].nunique() == 1, str(set(res["maquina"])))
    c, rep = fin[fin["brazo"] == lg.CONTROL], fin[fin["brazo"] == "C-rep"]
    if rep.empty:
        chk("5.4 el control se reproduce (C-rep)", False, "faltan las corridas C-rep")
    else:
        dauc = abs(c["auc_val"].mean() - rep["auc_val"].mean())
        dg = abs(c["ganancia_max_201910"].mean() - rep["ganancia_max_201910"].mean())
        ee_g = c["ganancia_max_201910"].std(ddof=1) * (2 / len(c)) ** 0.5
        ee_a = c["auc_val"].std(ddof=1) * (2 / len(c)) ** 0.5
        chk("5.4 el control se reproduce (C-rep, ≤ 2 errores estándar)", dg <= 2 * ee_g and dauc <= 2 * ee_a,
            f"|ΔAUC|={dauc:.5f} (2 EE = {2 * ee_a:.5f}) |Δganancia|={dg:,.0f} (2 EE = {2 * ee_g:,.0f})")
    return out


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--ledger", type=Path, default=LEDGER)
    p.add_argument("--sanity", action="store_true", help="chequeos de la etapa corridas (tareas 5.1 a 5.4)")
    a = p.parse_args()
    r = consolidar(a.ledger)
    if a.sanity:
        res = sanity(r)
        for nombre, ok, det in res:
            print("OK   " if ok else "FALLA", nombre, det)
        raise SystemExit(0 if all(ok for _, ok, _ in res) else 1)
    print(f"{len(r['resultados'])} corridas válidas, {len(r['reemplazadas'])} reemplazadas, "
          f"{len(r['apareado']) if 'apareado' in r else 0} brazos apareados")


if __name__ == "__main__":
    main()
