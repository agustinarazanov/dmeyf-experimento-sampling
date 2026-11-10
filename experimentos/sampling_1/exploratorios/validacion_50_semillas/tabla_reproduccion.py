"""Tabla reportado / reproducido del README (tarea 5.2): cada número sale de `resultados/`, de `panel_d7.json` o de los
`replicas.csv` y `estudios.csv` de los experimentos; nada se escribe a mano.

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
    ens = {e: float(pres[e]["ens_k_201910"]) for e in (1, 8, 9)}
    filas = [
        fila("H3-0.05 sobre el control (ganancia media)", "+6,47 M$",
             f"{m(g10[4] - g10[1], True)} M$ (50 semillas, estrategia 4 contra 1, hiperparámetros de Luis); "
             f"{m(d3('H3-0.05', h3), True)} M$ (8 réplicas × 10 semillas, `h3`)", f"{m(g10[4] - g10[1] - 6.47e6, True)} M$ (50 semillas)",
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
