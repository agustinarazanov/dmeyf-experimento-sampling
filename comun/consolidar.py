"""Consolida el ledger de un experimento (o de todos).

    python -m comun.consolidar --experimento h1     # un experimento
    python -m comun.consolidar                      # todos los dueños de variantes, en orden de dependencias
    python -m comun.consolidar --ledger DIR         # un ledger suelto que tiene todo adentro (control incluido)

Lee `<ledger>/corridas/*.csv` y escribe `resultados.csv` (corridas válidas, sin duplicados por clave),
`reemplazadas.csv`, `estudios.csv` (hiperparámetros y tiempo de cada estudio) y `apareado.csv` (Δ contra el control
por semilla, con N*, δ y veredicto). Todo sale de acá; nada se calcula a mano.

Con `--experimento X` las filas son las de X; los finales de `C` y N* salen de `control`, y el tiempo del estudio de
cada variante, del ledger del dueño del estudio (H3 lee los de h1). Por eso se consolida primero a quien se depende.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

import pandas as pd

from comun import variantes, rutas
from comun import ledger as lg


def _absolutas(finales: pd.DataFrame, base: Path) -> pd.DataFrame:
    """Rutas de curvas absolutas, para mezclar finales de dos ledgers y leerlas igual."""
    f = finales.copy()
    for col in ("curva_201908", "curva_201910"):
        f[col] = f[col].map(lambda r: str(base / r))
    return f


def _leer_estudios(ledgers: Sequence[Path]) -> pd.DataFrame:
    tablas = [lg.leer_csv(l / "estudios.csv") for l in ledgers if (l / "estudios.csv").exists()]
    return pd.concat(tablas, ignore_index=True) if tablas else pd.DataFrame(columns=lg.COLUMNAS)


def consolidar(ledger: Path, control: Path | None = None, ledgers_estudios: Sequence[Path] = ()) -> dict[str, pd.DataFrame]:
    """Consolida `ledger`. Los finales de `C` y N* salen de `control` (por defecto, del propio ledger) y los tiempos de
    estudio, de `estudios.csv` de `ledgers_estudios` además del propio."""
    corridas = lg.leer_corridas(ledger / "corridas")
    resultados, reemplazadas = lg.consolidar_corridas(corridas)
    resultados.to_csv(ledger / "resultados.csv", index=False)
    reemplazadas.to_csv(ledger / "reemplazadas.csv", index=False)
    salida = {"resultados": resultados, "reemplazadas": reemplazadas}
    finales = resultados[resultados["etapa"] == "final"]
    estudios = resultados[resultados["etapa"] == "optimizar"]
    estudios.to_csv(ledger / "estudios.csv", index=False)
    leer = lambda ruta: lg.leer_curva(ledger, ruta)
    if control is not None and control != ledger:
        res_c = control / "resultados.csv"
        if not res_c.exists():
            raise FileNotFoundError(f"falta {res_c}: consolidar primero el control")
        r = lg.leer_csv(res_c)
        fin_c = r[(r["etapa"] == "final") & (r["variante"] == lg.CONTROL)]
        finales = pd.concat([_absolutas(finales, ledger), _absolutas(fin_c, control)], ignore_index=True)
        leer = lambda ruta: pd.read_csv(ruta)
        estudios = pd.concat([estudios, _leer_estudios([control, *ledgers_estudios])], ignore_index=True)
    elif ledgers_estudios:
        estudios = pd.concat([estudios, _leer_estudios(ledgers_estudios)], ignore_index=True)
    estudios = estudios.drop_duplicates("id")
    if finales["variante"].eq(lg.CONTROL).any() and (~finales["variante"].isin(lg.SIN_DELTA)).any():
        n_estrella = lg.corte_control(finales, leer)
        con_g = lg.agregar_ganancia(finales, leer, n_estrella)
        tabla = lg.apareado(con_g, estudios)
        tabla.insert(1, "n_estrella", n_estrella)
        tabla.to_csv(ledger / "apareado.csv", index=False)
        salida["apareado"] = tabla
    return salida


def consolidar_experimento(exp: str) -> dict[str, pd.DataFrame]:
    """Consolida `experimentos/<exp>/ledger` con el control y los dueños de sus estudios según `comun/variantes.py`."""
    control = None if exp == variantes.CONTROL else rutas.ledger(variantes.CONTROL)
    estudios = {rutas.ledger(variantes.dueno_estudio(b.estudio)) for b in variantes.variantes_de(exp)} - {rutas.ledger(exp)}
    return consolidar(rutas.ledger(exp), control, sorted(estudios))


def orden() -> list[str]:
    """Dueños de variantes con las dependencias primero (el control, luego quien lee de otros)."""
    dep = variantes.implicitas()
    hecho: list[str] = []

    def visitar(e: str) -> None:
        if e in hecho or e not in variantes.duenos():
            return
        for d in sorted(dep[e]):
            visitar(d)
        hecho.append(e)

    for e in variantes.duenos():
        visitar(e)
    return hecho


def sanity(r: dict[str, pd.DataFrame]) -> list[tuple[str, bool, str]]:
    """Chequeos de la etapa corridas (tareas 5.1 a 5.4). Devuelve (chequeo, ok, detalle)."""
    res = r["resultados"]
    fin = res[res["etapa"] == "final"]
    out = []

    def chk(nombre: str, ok: bool, detalle: str) -> None:
        out.append((nombre, bool(ok), detalle))

    f1 = fin[fin["variante"].isin(["C", "H3-0.25", "H3-0.1"])]
    chk("5.1 fase 1: 30 finales, una máquina y un commit",
        len(f1) == 30 and f1["maquina"].nunique() == 1 and f1["commit"].nunique() == 1,
        f"{len(f1)} filas, {f1['maquina'].nunique()} máquinas, {f1['commit'].nunique()} commits")
    variantes = ["U0.5", "U0.25", "U0.1", "U0.05", "B0.5", "B0.25", "B0.1", "GOSS"]
    chk("5.2-5.3 los 8 variantes de H1/H2 tienen 10 finales",
        all(len(fin[fin["variante"] == b]) == 10 for b in variantes), "")
    full = fin["filas_train"].max()
    malas = [b for b, g in fin[fin["variante"].str.startswith("U")].groupby("variante")
             if not g["filas_train"].between(float(g["tasa"].iloc[0]) * full * 0.999,
                                             float(g["tasa"].iloc[0]) * full * 1.001).all()]
    chk("5.2 filas de train coinciden con la tasa (±0,1%)", not malas, f"fuera de tasa: {malas}")
    chk("5.2 sin codigo_sucio", not res["codigo_sucio"].astype(bool).any(), "")
    bg = res[res["variante"].str.startswith(("B", "GOSS"))]
    chk("5.3 bagging_fraction fijo (no está en los hp optimizados)",
        not bg["hp"].str.contains("bagging").any(), f"{len(bg)} filas")
    chk("5.4 ninguna corrida exploratoria en resultados",
        res["id"].str.startswith("exp-").sum() == 0 and set(res["etapa"]) <= {"optimizar", "final"}
        and res["valida"].astype(bool).all(), "")
    chk("5.4 tiempos: un solo tipo de máquina", res["maquina"].nunique() == 1, str(set(res["maquina"])))
    c, rep = fin[fin["variante"] == lg.CONTROL], fin[fin["variante"] == "C-rep"]
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
    p.add_argument("--experimento", help="consolidar solo este experimento (por defecto, todos los dueños de variantes)")
    p.add_argument("--ledger", type=Path, help="consolidar un ledger suelto que tiene el control adentro")
    p.add_argument("--sanity", action="store_true", help="chequeos de la etapa corridas (tareas 5.1 a 5.4)")
    a = p.parse_args()
    if a.ledger:
        resultados = {"(ledger)": consolidar(a.ledger)}
    else:
        exps = [a.experimento] if a.experimento else orden()
        resultados = {}
        for e in exps:
            if not (rutas.ledger(e) / "corridas").is_dir():
                print(f"{e}: sin ledger/corridas, se saltea")
                continue
            resultados[e] = consolidar_experimento(e)
    for e, r in resultados.items():
        print(f"{e}: {len(r['resultados'])} corridas válidas, {len(r['reemplazadas'])} reemplazadas, "
              f"{len(r['apareado']) if 'apareado' in r else 0} variantes apareados")
    if a.sanity:
        union = {"resultados": pd.concat([r["resultados"] for r in resultados.values()], ignore_index=True)}
        res = sanity(union)
        for nombre, ok, det in res:
            print("OK   " if ok else "FALLA", nombre, det)
        raise SystemExit(0 if all(ok for _, ok, _ in res) else 1)


if __name__ == "__main__":
    main()
