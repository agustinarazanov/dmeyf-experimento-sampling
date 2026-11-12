"""Tabla reportado / reproducido del README (tarea 5.2): cada número sale de `resultados/`, de `panel_d7.json`, de
`hp_original.json`, de `estrategias.py` o de los `replicas.csv`, `estudios.csv` y `apareado.csv` de los experimentos;
nada se escribe a mano.

    python -m experimentos.sampling_1.exploratorios.validacion_50_semillas.tabla_reproduccion            # imprime
    python -m experimentos.sampling_1.exploratorios.validacion_50_semillas.tabla_reproduccion --escribir  # README
    python -m experimentos.sampling_1.exploratorios.validacion_50_semillas.tabla_reproduccion --verificar # README == fuentes
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics as st
import sys
from pathlib import Path

from comun import rutas

from . import estrategias as es

AQUI = Path(__file__).resolve().parent
RES = AQUI / "resultados"
LUIS = rutas.ledger("sampling_1") / "luis"
README = AQUI / "README.md"
MARCAS = {"tabla": ("<!-- tabla:inicio -->", "<!-- tabla:fin -->"), "ranking": ("<!-- ranking:inicio -->", "<!-- ranking:fin -->")}


def leer(ruta: Path) -> list[dict]:
    with ruta.open(newline="") as f:
        return list(csv.DictReader(f))


def m(x: float, signo: bool = False) -> str:
    """Millones de pesos con coma decimal."""
    s = f"{x / 1e6:+,.2f}" if signo else f"{x / 1e6:,.2f}"
    return s.replace(",", "_").replace(".", ",").replace("_", ".")


def n(x: float, d: int = 1) -> str:
    return f"{x:.{d}f}".replace(".", ",")


def media(filas: list[dict], estrategia: int, col: str, archivo: str = "semillas_original_e{}.csv") -> float:
    return st.mean(float(r[col]) for r in leer(RES / archivo.format(estrategia)))


def replicas(exp: str) -> dict[str, dict]:
    return {r["variante"]: r for r in leer(rutas.ledger(exp) / "replicas.csv")}


def tiempos_opt(exp_estudios: list[tuple[str, str]], prefijo: str) -> float:
    """Mediana entre réplicas del tiempo de optimización de los estudios `prefijo` y `prefijo@k`."""
    vistos = {}
    for exp, _ in exp_estudios:
        for r in leer(rutas.ledger(exp) / "estudios.csv"):
            if r["valida"] == "True" and (r["estudio"] == prefijo or r["estudio"].startswith(prefijo + "@")):
                vistos[r["estudio"]] = float(r["tiempo_optimizacion_s"])
    assert len(vistos) == 8, (prefijo, sorted(vistos))
    return st.median(vistos.values())


def tiempo_final(exp: str, variante: str) -> float:
    return st.median(float(r["tiempo_entrenamiento_s"]) for r in leer(rutas.ledger(exp) / "resultados.csv")
                     if r["variante"] == variante and r["etapa"] == "final" and r["valida"] == "True")


def delta_pareado(e: int, ref: int = 1) -> tuple[float, float, float]:
    """Δ de G en 201910 de la estrategia `e` contra `ref`, apareado por semilla: media e IC 95% normal."""
    a = {r["semilla"]: float(r["g_201910"]) for r in leer(RES / f"semillas_original_e{ref}.csv")}
    d = [float(r["g_201910"]) - a[r["semilla"]] for r in leer(RES / f"semillas_original_e{e}.csv") if r["semilla"] in a]
    se = st.stdev(d) / len(d) ** 0.5
    return st.mean(d), st.mean(d) - 1.96 * se, st.mean(d) + 1.96 * se


def sd_201910(e: int, primeras: int | None = None) -> float:
    filas = sorted(leer(RES / f"semillas_original_e{e}.csv"), key=lambda r: int(r["orden"]))[:primeras]
    return st.stdev(float(r["g_201910"]) for r in filas)


def hp_estudios(exp: str, prefijo: str, clave: str) -> float:
    """Mediana entre réplicas de un hiperparámetro elegido por los estudios `prefijo` y `prefijo@k`."""
    vistos = {r["estudio"]: json.loads(r["hp"])[clave] for r in leer(rutas.ledger(exp) / "estudios.csv")
              if r["valida"] == "True" and (r["estudio"] == prefijo or r["estudio"].startswith(prefijo + "@"))}
    assert len(vistos) == 8, (prefijo, sorted(vistos))
    return st.median(vistos.values())


def fila(nombre, reportado, reproducido, dif, expl):
    return f"| {nombre} | {reportado} | {reproducido} | {dif} | {expl} |"


def tabla() -> str:
    h3, h4 = replicas("h3"), replicas("h4")
    pres = {int(r["estrategia"]): r for r in leer(RES / "presupuesto_original.csv")}
    t_c = tiempos_opt([("control", "")], "C")
    t_005 = tiempos_opt([("h1", ""), ("h3", "")], "U0.05")
    t_c_final, t_f_final = tiempo_final("control", "C"), tiempo_final("h4", "H4F-0.05")
    g10 = {e: media(None, e, "g_201910") for e in range(1, 10)}
    g10_led = st.mean(float(r["g_201910"]) for r in leer(RES / "semillas_ledger_e7.csv"))
    d3 = lambda v, tab: float(tab[v]["delta_g_media"])
    g_rep = lambda v, tab: float(tab[v]["g_media_replicas"])
    t_s = {e: media(None, e, "tiempo_s") for e in (1, 8, 9)}
    K = {e: int(pres[e]["k_presupuesto"]) for e in (8, 9)}
    ens = {e: float(pres[e]["ens_k_201910"]) for e in (1, 2, 3, 5, 6, 8, 9)}
    hp_o = json.loads((AQUI / "hp_original.json").read_text())
    h1 = {r["variante"]: r for r in leer(rutas.ledger("h1") / "apareado.csv")}
    d_h3 = {e: delta_pareado(e) for e in (2, 3, 4, 5, 6)}
    se10, se50 = sd_201910(1, 10) / 10 ** 0.5, sd_201910(1) / 50 ** 0.5
    filas = [
        fila("Optuna del control", "~13 minutos",
             f"{n(hp_o['C']['t_opt'] / 60)} min (`t_opt` de `hp_original.json`, el de Luis); {n(t_c / 60)} min (mediana de 8 réplicas en la VM)",
             f"{n(hp_o['C']['t_opt'] / 60 - 13)} min (el de Luis)", "el de Luis coincide; el de la VM es otra máquina, sin `FACTOR_VM`"),
        fila("Error estándar de 10 a 50 semillas", "cayó a la mitad",
             f"{m(se10)} M$ con las primeras 10 semillas y {m(se50)} M$ con 50 (estrategia 1, G en 201910): cociente {n(se50 / se10, 2)}",
             f"{n(se50 / se10 - 0.5, 2)}", "consistente: con el mismo desvío el cociente es √(10/50) ≈ 0,45"),
        fila("Todas las variantes de H3 le ganan al control (50 semillas)", "\"todas GANAN\"",
             "; ".join(f"estrategia {e}: {m(d[0], True)} M$ [{m(d[1], True)}; {m(d[2], True)}]" for e, d in d_h3.items())
             + " (Δ apareado por semilla en 201910, IC 95%)",
             f"{sum(d[1] > 0 for d in d_h3.values())} de {len(d_h3)} con IC sobre cero",
             "una sola búsqueda por estrategia: el IC no incluye la variabilidad de Optuna; veredictos con 8 réplicas (`h3`): "
             + ", ".join(f"`{v}` {h3[v]['veredicto']}" for v in ("H3-0.05", "H3-0.1", "H3-0.25", "H3R-0.1", "H3R-0.25"))),
        fila("Hiperparámetros de H3-0.05", "`feature_fraction = 0.34`, `min_data_in_leaf = 985`",
             f"`feature_fraction = {n(hp_o['U0.05']['hp']['feature_fraction'], 2)}`, `min_data_in_leaf = {hp_o['U0.05']['hp']['min_data_in_leaf']}` (`hp_original.json`)",
             "idéntico", "son los hiperparámetros fijados en su script, portados sin cambios"),
        fila("`feature_fraction` del control", "0.985", f"{n(hp_o['C']['hp']['feature_fraction'], 3)} (`hp_original.json`)", "idéntico", "ídem"),
        fila("H3-0.05 sobre el control (ganancia media)", "+6,47 M$",
             f"{m(g10[4] - g10[1], True)} M$ (50 semillas, estrategia 4 contra 1, hiperparámetros de Luis); "
             f"{m(d3('H3-0.05', h3), True)} M$ (8 réplicas × 20 semillas, `h3`)", f"{m(g10[4] - g10[1] - 6.47e6, True)} M$ (50 semillas)",
             "mismo sentido, menor magnitud; con réplicas el IC de Δ incluye el cero (veredicto \"no pierde\", no \"gana\")"),
        fila("Optuna de H3-0.05 contra el control", "8,89 veces más rápido",
             f"{n(t_c / t_005, 2)} veces (mediana de {n(t_c, 0)} s contra {n(t_005, 0)} s, 8 réplicas, solo la optimización)",
             f"{n(t_c / t_005 - 8.89, 2)}", "tiempos medidos en la VM, sin `FACTOR_VM`; no es una diferencia de ganancia, depende de la máquina"),
        fila("H4 hard (reconstruido: `NH0.1`) sobre el control", "+7,19 M$",
             f"{m(g10[7] - g10[1], True)} M$ (50 semillas, estrategia 7 con los hiperparámetros de Luis); "
             f"{m(g10_led - g10[1], True)} M$ (`--hp ledger`, `NH0.1`); {m(d3('H4H-0.1', h4), True)} M$ (8 réplicas, `H4H-0.1`)",
             f"{m(g10[7] - g10[1] - 7.19e6, True)} M$ (50 semillas, `original`)",
             "RECONSTRUIDO: con los hiperparámetros de Luis da positivo; con la búsqueda reconstruida (`NH0.1`) da negativo, "
             "en 50 semillas y con réplicas; la ventaja no se sostiene al repetir la búsqueda"),
        fila("H4 con negativos uniformes (reconstruido: `NU0.1`) sobre el control", "−2,31 M$",
             f"{m(d3('H4U-0.1', h4), True)} M$ (8 réplicas, `H4U-0.1`)", f"{m(d3('H4U-0.1', h4) + 2.31e6, True)} M$",
             "RECONSTRUIDO: mismo signo, mayor magnitud; con réplicas el IC queda por debajo del cero"),
        fila("Hiperparámetros de H4 uniforme (reconstruido: `NU0.1`)", "`num_leaves = 226`, `feature_fraction > 0.70`",
             f"`num_leaves = {n(hp_estudios('h4', 'NU0.1', 'num_leaves'), 0)}`, `feature_fraction = {n(hp_estudios('h4', 'NU0.1', 'feature_fraction'), 2)}` "
             f"(medianas de 8 réplicas); `NH0.1`: `num_leaves = {n(hp_estudios('h4', 'NH0.1', 'num_leaves'), 0)}`, "
             f"`feature_fraction = {n(hp_estudios('h4', 'NH0.1', 'feature_fraction'), 2)}`", "—",
             "RECONSTRUIDO: la búsqueda no es la suya; se informa para ver si la uniforme elige árboles más complejos que la difícil"),
        fila("Fast-retrain: tiempo por semilla", "12,3 s",
             f"{n(t_s[8])} s y {n(t_s[9])} s (estrategias 8 y 9, medidos en la VM); {n(t_f_final)} s (mediana de `H4F-0.05`, solo entrenamiento)",
             f"{n(t_s[8] - 12.3)} s (estrategia 8)", "tiempo de máquina, sin `FACTOR_VM`; del mismo orden"),
        fila("Fast-retrain: semillas que entran en 900 s (reconstruido)", "más de 60",
             f"{K[8]} (estrategia 8) y {K[9]} (estrategia 9)", "consistente", "RECONSTRUIDO: K = ⌊(900 − T_opt) / T_final medio⌋"),
        fila("Fast-retrain: ensamble a 900 s", "283,25 M$",
             f"{m(ens[8])} M$ y {m(ens[9])} M$ (201910, ensamble de las primeras K semillas)", f"{m(ens[8] - 283.25e6, True)} M$ y {m(ens[9] - 283.25e6, True)} M$",
             "RECONSTRUIDO: el ensamble depende de las semillas elegidas y de K; un solo ensamble por estrategia, sin IC"),
        fila("Control: ensamble a 900 s", "276,65 M$", f"{m(ens[1])} M$ (K = {pres[1]['k_presupuesto']})", f"{m(ens[1] - 276.65e6, True)} M$",
             "RECONSTRUIDO: ídem; el ensamble de pocas semillas es muy variable"),
        fila("Control: tiempo por semilla", "35 s", f"{n(t_s[1])} s (estrategia 1); {n(t_c_final)} s (mediana de `C` en `control`, solo entrenamiento)",
             f"{n(t_s[1] - 35)} s", "tiempo de máquina, sin `FACTOR_VM`"),
        fila("Control: semillas que entran en 15 minutos", "4", f"{pres[1]['k_presupuesto']} (estrategia 1)",
             "idéntico" if int(pres[1]["k_presupuesto"]) == 4 else "distinto", "RECONSTRUIDO: misma fórmula que el fast-retrain"),
        fila("Fast-retrain: fracción de CONTINUA y peso", "50 %, `w = 2`", f"{n(es.FRACCION_FAST * 100, 0)} %, `w = {n(1 / es.FRACCION_FAST, 0)}` (`estrategias.py`)",
             "idéntico", "parámetro portado sin cambios"),
        fila("Reescalado √(1/r): menos varianza entre semillas y mejor ensamble", "sin número",
             f"desvío de G en 201910: {m(sd_201910(5))} contra {m(sd_201910(2))} M$ (0,25: estrategia 5 contra 2) y {m(sd_201910(6))} contra "
             f"{m(sd_201910(3))} M$ (0,10: 6 contra 3); ensamble a 900 s: {m(ens[5])} contra {m(ens[2])} M$ y {m(ens[6])} contra {m(ens[3])} M$", "—",
             "un solo ensamble y una sola búsqueda por estrategia; con réplicas, los contrastes `H3R` contra `H3` están en `h3`"),
        fila("H1: muestreo uniforme también en el final (descarte)", "\"se desploma\" por debajo del 50 %",
             "; ".join(f"`{v}`: {m(float(h1[v]['delta_g_media']), True)} M$, {h1[v]['veredicto']}" for v in ("U0.25", "U0.1", "U0.05"))
             + " (`h1/ledger/apareado.csv`, 20 semillas)", "—", "mismo sentido; es la H1 de la ronda vigente (final 201903–201908), sin réplicas de la búsqueda"),
        fila("Reescalado lineal peor que √(1/r) (reconstruido: `H3L-*`)", "\"cae drásticamente\"",
             f"`H3L-0.1` contra `H3R-0.1`: {m(g_rep('H3L-0.1', h3) - g_rep('H3R-0.1', h3), True)} M$; `H3L-0.25` contra `H3R-0.25`: "
             f"{m(g_rep('H3L-0.25', h3) - g_rep('H3R-0.25', h3), True)} M$ (diferencia de medias de réplicas)", "—",
             "RECONSTRUIDO: el lineal queda por debajo del de raíz en ambas tasas; son diferencias de medias, no un contraste con IC"),
        fila("Muestreo por cliente peor que por filas (reconstruido: `H3K-0.1`)", "\"peor rendimiento\"",
             f"`H3K-0.1` contra `H3-0.1`: {m(g_rep('H3K-0.1', h3) - g_rep('H3-0.1', h3), True)} M$ (diferencia de medias de réplicas)", "—",
             "RECONSTRUIDO: mismo sentido, diferencia chica; no es un contraste con IC"),
    ]
    d7 = json.loads((LUIS / "panel_d7.json").read_text())
    pl = leer(LUIS / "panel_luis" / "semillas_original_e1.csv")
    g_pl = st.mean(float(r["g_201910"]) for r in pl)
    dc = d7["columnas"]
    filas.append(fila(
        "Panel de Luis contra `comun.datos` (D7)", "—",
        f"{dc['n_nuestro']} columnas contra {dc['n_luis']} (nuestro panel suma {len(dc['solo_nuestro'])}: `tmobile_app` y `cmobile_app_trx` con sus lags y deltas); "
        f"filas por mes {'iguales' if d7['filas_por_mes']['iguales'] else 'distintas'}; huellas de las {d7['huellas']['comparadas']} columnas comunes: "
        f"{len(d7['huellas']['distintas'])} distintas; estrategia 1 con `--panel-luis`: {m(g_pl)} M$ contra {m(g10[1])} M$ en 201910",
        f"{m(g_pl - g10[1], True)} M$", "veredicto \"distintos\" por las columnas extra; el efecto sobre la ganancia es chico frente a la desviación entre semillas"))
    return "\n".join(filas)


def ranking() -> str:
    cab = "| puesto | estrategia | n | G 201908 (M$) | desvío (M$) | G máx. 201908 (M$) | AUC 201908 | tiempo (s) |\n|---|---|---|---|---|---|---|---|\n"
    return cab + "\n".join(
        f"| {r['puesto_201908']} | {r['estrategia']} {r['nombre']} | {r['n']} | {m(float(r['g_201908']))} | {m(float(r['g_201908_sd']))} | "
        f"{m(float(r['gmax_201908']))} | {n(float(r['auc_201908']), 4)} | {n(float(r['tiempo_s']))} |"
        for r in leer(RES / "ranking_201908_original.csv"))


GENERADORES = {"tabla": tabla, "ranking": ranking}


def bloque(texto: str, clave: str) -> tuple[int, int]:
    ini, fin = (texto.index(x) for x in MARCAS[clave])
    return ini + len(MARCAS[clave][0]), fin


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--escribir", action="store_true")
    ap.add_argument("--verificar", action="store_true")
    a = ap.parse_args()
    if not (a.escribir or a.verificar):
        for k, f in GENERADORES.items():
            print(f())
            print()
        return 0
    texto = README.read_text()
    ok = True
    for clave, f in GENERADORES.items():
        i, j = bloque(texto, clave)
        nuevo = "\n" + f() + "\n"
        if a.escribir:
            texto = texto[:i] + nuevo + texto[j:]
        elif texto[i:j] != nuevo:
            print(f"README desactualizado respecto de las fuentes: bloque {clave}")
            ok = False
    if a.escribir:
        README.write_text(texto)
    elif ok:
        print("README coincide con las fuentes")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
