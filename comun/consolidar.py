"""Consolida el ledger de un experimento (o de todos).

    python -m comun.consolidar --experimento h1     # un experimento
    python -m comun.consolidar                      # todos los dueños de variantes, en orden de dependencias
    python -m comun.consolidar --ledger DIR         # un ledger suelto que tiene todo adentro (control incluido)
    python -m comun.consolidar --meses-final 201903-201906   # la ronda anterior (por defecto, la vigente 201903-201908)

Lee `<ledger>/corridas/*.csv` y escribe `resultados.csv` (corridas válidas, sin duplicados por clave),
`reemplazadas.csv`, `estudios.csv` (hiperparámetros y tiempo de cada estudio), `apareado.csv` (Δ contra el control
por semilla de la réplica 0, con N*, δ y veredicto) y, si hay variantes con al menos dos réplicas de optimización,
`replicas.csv` (Δ con réplicas, IC de Welch, descomposición de la varianza). Todo sale de acá; nada se calcula a mano.

`--meses-final` elige la ronda de finales (la ventana de train, columna `meses_final`). La vigente escribe `apareado.csv` y
`replicas.csv` en el ledger; las otras, en `<ledger>/ronda_<ventana>/`. N* es `corte_control` (media de las curvas de 201908 de
los `C`) en la ronda `201903-201906` y `baseline.N_ESTRELLA` en la nueva, cuyos finales no predicen 201908. Falla si la ronda
no tiene finales de `C`.

Con `--experimento X` las filas son las de X; los finales de `C` y N* salen de `control`, y el tiempo del estudio de
cada variante, del ledger del dueño del estudio (H3 lee los de h1). Por eso se consolida primero a quien se depende.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

import pandas as pd

from comun import baseline as bl
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


def corte_de_ronda(finales_c: pd.DataFrame, leer, meses_final: str) -> int:
    """N* de la ronda: fijo (`baseline.N_ESTRELLA`) en la nueva; la media de las curvas de 201908 de `C` en la anterior."""
    if meses_final == lg.MESES_FINAL_VIEJA:
        return lg.corte_control(finales_c, leer)
    return bl.N_ESTRELLA


def consolidar(ledger: Path, control: Path | None = None, ledgers_estudios: Sequence[Path] = (),
               meses_final: str = bl.VENTANA_FINAL) -> dict[str, pd.DataFrame]:
    """Consolida `ledger`. Los finales de `C` y N* salen de `control` (por defecto, del propio ledger) y los tiempos de
    estudio, de `estudios.csv` de `ledgers_estudios` además del propio. Solo cuentan los finales de la ronda `meses_final`."""
    corridas = lg.leer_corridas(ledger / "corridas")
    resultados, reemplazadas = lg.consolidar_corridas(corridas)
    resultados.to_csv(ledger / "resultados.csv", index=False)
    reemplazadas.to_csv(ledger / "reemplazadas.csv", index=False)
    salida = {"resultados": resultados, "reemplazadas": reemplazadas}
    finales = resultados[(resultados["etapa"] == "final") & (resultados["meses_final"] == meses_final)]
    estudios = resultados[resultados["etapa"] == "optimizar"]
    salida_tablas = ledger if meses_final == bl.VENTANA_FINAL else ledger / f"ronda_{meses_final}"
    estudios.to_csv(ledger / "estudios.csv", index=False)
    leer = lambda ruta: lg.leer_curva(ledger, ruta)
    propias = set(finales["variante"])  # `replicas.csv` solo tiene las variantes de este experimento
    if control is not None and control != ledger:
        res_c = control / "resultados.csv"
        if not res_c.exists():
            raise FileNotFoundError(f"falta {res_c}: consolidar primero el control")
        r = lg.leer_csv(res_c)
        fin_c = r[(r["etapa"] == "final") & (r["variante"] == lg.CONTROL) & (r["meses_final"] == meses_final)]
        finales = pd.concat([_absolutas(finales, ledger), _absolutas(fin_c, control)], ignore_index=True)
        leer = lambda ruta: pd.read_csv(ruta)
        estudios = pd.concat([estudios, _leer_estudios([control, *ledgers_estudios])], ignore_index=True)
    elif ledgers_estudios:
        estudios = pd.concat([estudios, _leer_estudios(ledgers_estudios)], ignore_index=True)
    estudios = estudios.drop_duplicates("id")
    finales = lg.con_replica(finales)
    f0 = finales[finales["replica_opt"] == 0]  # N*, δ y el apareado por semilla salen de la réplica 0, como antes
    if not finales["variante"].eq(lg.CONTROL).any():
        raise ValueError(f"la ronda {meses_final} no tiene finales del control (variante C): no se puede consolidar")
    if f0["variante"].eq(lg.CONTROL).any():
        salida_tablas.mkdir(parents=True, exist_ok=True)
        n_estrella = corte_de_ronda(f0, leer, meses_final)
        con_g = lg.agregar_ganancia(finales, leer, n_estrella)
        g0 = con_g[con_g["replica_opt"] == 0]
        if (~g0["variante"].isin(lg.SIN_DELTA)).any():
            tabla = lg.apareado(g0, estudios)
            tabla.insert(1, "n_estrella", n_estrella)
            tabla.to_csv(salida_tablas / "apareado.csv", index=False)
            salida["apareado"] = tabla
        delta = lg.DELTA_REL * float(g0.loc[g0["variante"] == lg.CONTROL, "g"].mean())
        tabla_r = lg.replicas(con_g, delta, propias, variantes.PARES_APAREADOS, pares_welch=variantes.PARES_WELCH)
        if len(tabla_r):
            tabla_r.insert(1, "n_estrella", n_estrella)
            tabla_r.to_csv(salida_tablas / "replicas.csv", index=False)
            salida["replicas"] = tabla_r
    return salida


def consolidar_experimento(exp: str, meses_final: str = bl.VENTANA_FINAL) -> dict[str, pd.DataFrame]:
    """Consolida `experimentos/<exp>/ledger` con el control y los dueños de sus estudios según `comun/variantes.py`."""
    control = None if exp == variantes.CONTROL else rutas.ledger(variantes.CONTROL)
    estudios = {rutas.ledger(variantes.dueno_estudio(b.estudio)) for b in variantes.variantes_de(exp)} - {rutas.ledger(exp)}
    return consolidar(rutas.ledger(exp), control, sorted(estudios), meses_final)


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


def sanity(r: dict[str, pd.DataFrame], meses_final: str = bl.VENTANA_FINAL) -> list[tuple[str, bool, str]]:
    """Chequeos de la etapa corridas (tareas 5.1 a 5.4) sobre la ronda `meses_final`. Devuelve (chequeo, ok, detalle)."""
    res = r["resultados"]
    res = res[(res["etapa"] == "optimizar") | (res["meses_final"] == meses_final)]
    n = len(bl.SEMILLAS_FINALES) if meses_final == bl.VENTANA_FINAL else len(bl.SEMILLAS_OFICIALES)
    fin = lg.con_replica(res[res["etapa"] == "final"])
    fin = fin[fin["replica_opt"] == 0]  # los chequeos de las fases 1 a 4 son de la réplica 0
    out = []

    def chk(nombre: str, ok: bool, detalle: str) -> None:
        out.append((nombre, bool(ok), detalle))

    f1 = fin[fin["variante"].isin(["C", "H3-0.25", "H3-0.1"])]
    chk(f"5.1 fase 1: {3 * n} finales, una máquina y un commit",
        len(f1) == 3 * n and f1["maquina"].nunique() == 1 and f1["commit"].nunique() == 1,
        f"{len(f1)} filas, {f1['maquina'].nunique()} máquinas, {f1['commit'].nunique()} commits")
    variantes = ["U0.5", "U0.25", "U0.1", "U0.05", "B0.5", "B0.25", "B0.1", "GOSS"]
    chk(f"5.2-5.3 las 8 variantes de H1/H2 tienen {n} finales",
        all(len(fin[fin["variante"] == b]) == n for b in variantes), "")
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
    p.add_argument("--meses-final", default=bl.VENTANA_FINAL,
                   help="ronda de finales (ventana de train): 201903-201908 (vigente) o 201903-201906 (anterior)")
    p.add_argument("--sanity", action="store_true", help="chequeos de la etapa corridas (tareas 5.1 a 5.4)")
    a = p.parse_args()
    if a.ledger:
        resultados = {"(ledger)": consolidar(a.ledger, meses_final=a.meses_final)}
    else:
        exps = [a.experimento] if a.experimento else orden()
        resultados = {}
        for e in exps:
            if not (rutas.ledger(e) / "corridas").is_dir():
                print(f"{e}: sin ledger/corridas, se saltea")
                continue
            resultados[e] = consolidar_experimento(e, a.meses_final)
    for e, r in resultados.items():
        print(f"{e}: {len(r['resultados'])} corridas válidas, {len(r['reemplazadas'])} reemplazadas, "
              f"{len(r['apareado']) if 'apareado' in r else 0} variantes apareadas")
    if a.sanity:
        union = {"resultados": pd.concat([r["resultados"] for r in resultados.values()], ignore_index=True)}
        res = sanity(union, a.meses_final)
        for nombre, ok, det in res:
            print("OK   " if ok else "FALLA", nombre, det)
        raise SystemExit(0 if all(ok for _, ok, _ in res) else 1)


if __name__ == "__main__":
    main()
