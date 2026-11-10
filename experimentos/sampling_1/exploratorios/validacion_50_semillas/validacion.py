"""Validación con 50 semillas del aporte de Luis (commit 9e1889e): el loop de entrenamiento final de sus nueve estrategias.

PORTADO sin cambios de lógica: el entrenamiento por semilla (`full` y fast-retrain con peso 2), los parámetros de LightGBM,
la medición del tiempo (construcción del dataset + entrenamiento + predicción de test) y los ensambles acumulados.
Cambia el entorno: los datos salen de `comun.datos` y la ganancia de `comun.ganancia`; no hay Colab, Drive ni `FACTOR_VM`.

    python -m experimentos.sampling_1.exploratorios.validacion_50_semillas.validacion --estrategia 1 --hp original
"""

from __future__ import annotations

import argparse
import base64
import json
import logging
import time
from io import BytesIO
from pathlib import Path

import duckdb
import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from comun import baseline as bl
from comun import correr
from comun import datos as dt
from comun import ganancia as gn
from comun import muestreo
from comun import rutas

from . import estrategias as es
from . import panel_luis as pl
from . import presupuesto as pr

log = logging.getLogger("validacion_50")


def _auc(y, p) -> float:
    try:
        return float(roc_auc_score(y, p))
    except ValueError:  # una sola clase (solo pasa con muestras de smoke)
        return float("nan")


def _params_dataset() -> dict:
    return {**bl.PARAMS_DATASET, "num_threads": bl.NUM_THREADS}


class Datos:
    """Train (201903-201906), validación (201908) y test (201910) como matrices float32."""

    def __init__(self, filas: int | None = None, panel: Path | None = None):
        """`panel`: otro Parquet con las mismas columnas de control (el de Luis, D7); sus predictoras en su orden."""
        if panel is None:
            dt.asegurar_panel(filas)
            cargar = lambda meses: dt.cargar_meses(meses, filas)
        else:
            cargar = lambda meses: cargar_de(panel, meses)
        train = cargar(bl.MESES_TRAIN)
        val = cargar([bl.MES_VALIDACION])
        test = cargar([bl.MES_TEST])
        cols = dt.columnas_predictoras(train)
        self.x_tr, self.y_tr = dt.matriz(train, cols), train[dt.Y].to_numpy()
        self.x_va, self.y_va, self.b2_va = dt.matriz(val, cols), val[dt.Y].to_numpy(), val[dt.BAJA2].to_numpy()
        self.x_te, self.y_te, self.b2_te = dt.matriz(test, cols), test[dt.Y].to_numpy(), test[dt.BAJA2].to_numpy()
        t0 = time.perf_counter()
        self.dtrain_full = lgb.Dataset(self.x_tr, label=self.y_tr, params=_params_dataset(), free_raw_data=False)
        self.dtrain_full.construct()
        self.t_construct_full = time.perf_counter() - t0


def cargar_de(panel: Path, meses: list[int]) -> pd.DataFrame:
    """Como `comun.datos.cargar_meses`, pero de otro Parquet (anota los meses igual)."""
    log.info("MESES_LEIDOS %s (%s)", ",".join(str(m) for m in meses), panel.name)
    dt.MESES_LEIDOS.extend(meses)
    con = duckdb.connect()
    df = con.execute(f"select * from read_parquet('{panel}') where {dt.MES} in ({', '.join(map(str, meses))})").df()
    con.close()
    return df


def entrenar_semilla(e: es.Estrategia, hp: dict, semilla: int, d: Datos) -> tuple[np.ndarray, np.ndarray, float]:
    """(predicción en 201908, predicción en 201910, segundos). Los segundos no incluyen la predicción de 201908."""
    params = {**bl.PARAMS_FIJOS, "bagging_freq": 1, **hp, "seed": semilla}
    if e.modo == "full":
        t1 = time.perf_counter()
        modelo = lgb.train(params, d.dtrain_full)
        p_te = modelo.predict(d.x_te)
        t_raw = d.t_construct_full + (time.perf_counter() - t1)
    elif e.modo == "h4_50_pesos":
        t0 = time.perf_counter()
        idx = muestreo.indices_por_clase(d.y_tr, es.FRACCION_FAST, semilla)   # todas las bajas + 50 % de CONTINUA
        y_s = d.y_tr[idx]
        w_s = muestreo.peso_inverso(y_s, es.FRACCION_FAST).astype(np.float32)  # peso 2 en las CONTINUA
        d_sub = lgb.Dataset(d.x_tr[idx], label=y_s, weight=w_s, params=_params_dataset(), free_raw_data=False)
        d_sub.construct()
        modelo = lgb.train(params, d_sub)
        p_te = modelo.predict(d.x_te)
        t_raw = time.perf_counter() - t0
    else:
        raise ValueError(f"modo inválido: {e.modo!r}")
    return modelo.predict(d.x_va), p_te, t_raw


#: Tope de semillas cuando el presupuesto pide más que las 50 (el control a 900 s da K ≈ 4; el fast-retrain más de 60).
TOPE_SEMILLAS = 300


def correr_estrategia(e: es.Estrategia, hp: dict, t_opt: float, n: int, d: Datos, modo_hp: str = "original",
                      presupuesto_s: float | None = None) -> tuple[list[dict], list[dict]]:
    """Entrena `n` semillas (`es.semillas(n)`), una tras otra. Devuelve (una fila por semilla, una fila por K del ensamble de
    las primeras K).

    Por semilla: G al corte `N_ESTRELLA`, ganancia máxima de la curva y AUC en 201908, y G y AUC en 201910. En 201910 no se
    calcula el máximo de la curva (sería elegir el corte en test; `design.md` D9).

    RECONSTRUIDO (D2): con `presupuesto_s`, al llegar a la última semilla se calcula K = ⌊(P − T_opt)/T_final medio⌋ y, si es
    mayor, se siguen corriendo semillas (misma fórmula, hasta `TOPE_SEMILLAS`) hasta alcanzarlo.
    """
    filas, ensambles = [], []
    suma_va = np.zeros(len(d.x_va), dtype=np.float64)
    suma_te = np.zeros(len(d.x_te), dtype=np.float64)
    total, orden = n, 0
    while orden < total:
        orden += 1
        semilla = es.semillas(orden)[-1]
        p_va, p_te, t_raw = entrenar_semilla(e, hp, semilla, d)
        curva_va = gn.curva_de_corte(p_va, d.b2_va)
        filas.append({
            "estrategia": e.id, "nombre": e.nombre, "hp": modo_hp, "t_opt_s": t_opt, "orden": orden, "semilla": semilla,
            "tiempo_s": t_raw,
            "g_201908": gn.ganancia(p_va, d.b2_va, es.N_ESTRELLA), "gmax_201908": gn.ganancia_maxima(curva_va)[1],
            "auc_201908": _auc(d.y_va, p_va),
            "g_201910": gn.ganancia(p_te, d.b2_te, es.N_ESTRELLA), "auc_201910": _auc(d.y_te, p_te),
        })
        suma_va += p_va.astype(np.float32)
        suma_te += p_te.astype(np.float32)
        ensambles.append({"estrategia": e.id, "k": orden,
                          "g_201908": gn.ganancia(suma_va / orden, d.b2_va, es.N_ESTRELLA),
                          "g_201910": gn.ganancia(suma_te / orden, d.b2_te, es.N_ESTRELLA)})
        if presupuesto_s and orden == total:
            k = pr.k_presupuesto(t_opt, float(np.mean([f["tiempo_s"] for f in filas])), presupuesto_s)
            total = max(total, min(TOPE_SEMILLAS, k))
        log.info("estrategia %d semilla %d (%d/%d): G201908=%.2fM %.1fs", e.id, semilla, orden, total,
                 filas[-1]["g_201908"] / 1e6, t_raw)
    return filas, ensambles


# --- RECONSTRUIDO: salidas por estrategia y semilla, agregados (design.md D1, D2, D9) --------------------------------------
# El script original anuncia un `resumen_50_semillas.csv` que nunca escribe; lo de abajo es nuestra interpretación.

#: Dónde escribe cada VM (se sincroniza con el bucket como parte del ledger de `sampling_1`) y de dónde agrega `--agregar`.
SALIDA = rutas.ledger("sampling_1") / "luis"
REFERENCIA_CALIBRACION_S = 16.2448   # un final de U0.1 en la VM de Luis; con él calculaba su FACTOR_VM


def calibracion(d: Datos) -> dict:
    """Lo que Luis usaba como `FACTOR_VM`: no se aplica a ningún tiempo, se registra aparte para explicar diferencias."""
    hp = es.hp_original()["U0.1"]["hp"]
    t0 = time.perf_counter()
    lgb.train({**bl.PARAMS_FIJOS, "bagging_freq": 1, **hp, "seed": 100003}, d.dtrain_full)
    t = d.t_construct_full + (time.perf_counter() - t0)
    return {"referencia_s": REFERENCIA_CALIBRACION_S, "medido_s": t, "factor_vm": REFERENCIA_CALIBRACION_S / t}


def escribir_estrategia(salida: Path, modo_hp: str, e: es.Estrategia, filas: list[dict], ensambles: list[dict],
                        calib: dict) -> None:
    salida.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(filas).to_csv(salida / f"semillas_{modo_hp}_e{e.id}.csv", index=False)
    pd.DataFrame(ensambles).to_csv(salida / f"ensambles_{modo_hp}_e{e.id}.csv", index=False)
    (salida / f"calibracion_{modo_hp}_e{e.id}.json").write_text(json.dumps(calib, indent=2))


# todo lo que ordena o decide sale de 201908 (D9)

def ranking_201908(resumen: pd.DataFrame) -> pd.DataFrame:
    """Una fila por estrategia, ordenada por G media al corte N* en 201908. Solo mira columnas de 201908."""
    v = resumen[["estrategia", "nombre", "g_201908", "gmax_201908", "auc_201908", "tiempo_s"]]
    r = v.groupby(["estrategia", "nombre"], as_index=False).agg(
        n=("g_201908", "size"), g_201908=("g_201908", "mean"), g_201908_sd=("g_201908", "std"),
        gmax_201908=("gmax_201908", "mean"), auc_201908=("auc_201908", "mean"), tiempo_s=("tiempo_s", "mean"))
    r = r.sort_values(["g_201908", "estrategia"], ascending=[False, True]).reset_index(drop=True)
    r.insert(0, "puesto_201908", range(1, len(r) + 1))
    return r


def _ens(ensambles: pd.DataFrame, estrategia: int, k: int, mes: str) -> float:
    e = ensambles[ensambles["estrategia"] == estrategia].sort_values("k")
    return float(e[mes].iloc[min(k, len(e)) - 1])


def curva_k_201908(ensambles: pd.DataFrame) -> pd.DataFrame:
    """Ganancia en 201908 del ensamble de las primeras K semillas, K = 1…n (la curva según K de Luis, pero en 201908)."""
    return ensambles[["estrategia", "k", "g_201908"]].copy()


def ensambles_201908(ranking: pd.DataFrame, ensambles: pd.DataFrame) -> pd.DataFrame:
    """Ensambles de 10 y de 50 semillas (los del script de Luis) en 201908, en el orden del ranking."""
    out = ranking[["puesto_201908", "estrategia", "nombre"]].copy()
    for k in (10, 50):
        out[f"ens{k}_201908"] = [_ens(ensambles, int(s), k, "g_201908") for s in out["estrategia"]]
    return out


def tabla_201910(ranking: pd.DataFrame, resumen: pd.DataFrame, ensambles: pd.DataFrame, ks: dict[int, int]) -> pd.DataFrame:
    """Todas las estrategias en 201910, en el orden del ranking de 201908 y sin elegir ninguna. `ks[estrategia]` es el K del
    presupuesto (D2); también se informan los ensambles de 10 y 50 del script de Luis."""
    t = resumen[["estrategia", "g_201910", "auc_201910"]].groupby("estrategia", as_index=False).mean()
    out = ranking[["puesto_201908", "estrategia", "nombre"]].merge(t, on="estrategia")
    for k in (10, 50):
        out[f"ens{k}_201910"] = [_ens(ensambles, int(s), k, "g_201910") for s in out["estrategia"]]
    out["k_presupuesto"] = [ks[int(s)] for s in out["estrategia"]]
    out["ens_k_201910"] = [_ens(ensambles, int(s), ks[int(s)], "g_201910") if ks[int(s)] > 0 else float("nan")
                           for s in out["estrategia"]]
    return out


def leer(salida: Path, modo_hp: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    sem = sorted(salida.glob(f"semillas_{modo_hp}_e*.csv"))
    if not sem:
        raise FileNotFoundError(f"no hay semillas_{modo_hp}_e*.csv en {salida}")
    resumen = pd.concat([pd.read_csv(p) for p in sem], ignore_index=True)
    ensambles = pd.concat([pd.read_csv(p) for p in sorted(salida.glob(f"ensambles_{modo_hp}_e*.csv"))], ignore_index=True)
    return resumen, ensambles


def _png(fig) -> str:
    import matplotlib.pyplot as plt
    buf = BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", dpi=120)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode()


def html_reporte(ranking: pd.DataFrame, resumen: pd.DataFrame, curva: pd.DataFrame, ens: pd.DataFrame,
                 pres: pd.DataFrame, t910: pd.DataFrame) -> str:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    orden = list(ranking["estrategia"])
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.boxplot([resumen.loc[resumen["estrategia"] == s, "g_201908"] / 1e6 for s in orden], orientation="horizontal",
               tick_labels=[f"{s}_{n}" for s, n in zip(ranking["estrategia"], ranking["nombre"])], showmeans=True)
    ax.invert_yaxis()
    ax.set_xlabel("G al corte N* = 3.300 en 201908 (M$)")
    img1 = _png(fig)
    fig, ax = plt.subplots(figsize=(10, 5))
    for s in orden:
        c = curva[curva["estrategia"] == s]
        ax.plot(c["k"], c["g_201908"] / 1e6, label=str(s))
    ax.set_xlabel("K (semillas del ensamble)")
    ax.set_ylabel("G en 201908 (M$)")
    ax.legend(title="estrategia", ncol=3)
    img2 = _png(fig)
    fmt = {"float_format": lambda x: f"{x:,.2f}", "index": False}
    return (
        "<!DOCTYPE html>\n<html><head><meta charset='utf-8'><title>Validación con 50 semillas (aporte de Luis)</title></head><body>\n"
        "<h1>Validación con 50 semillas (aporte de Luis)</h1>\n"
        "<p>RECONSTRUIDO (design.md D2 y D9): todo lo que ordena o elige sale de 201908; 201910 va al final, sin elegir.</p>\n"
        f"<h2>Ranking en 201908</h2>{ranking.to_html(**fmt)}\n"
        f"<img src='data:image/png;base64,{img1}' alt='G en 201908 por estrategia'>\n"
        f"<h2>Ganancia en 201908 según K</h2><img src='data:image/png;base64,{img2}' alt='G según K'>\n"
        f"<h2>Ensambles de 10 y 50 semillas en 201908</h2>{ens.to_html(**fmt)}\n"
        f"<h2>Presupuesto</h2>{pres.to_html(**fmt)}\n"
        f"<h2>201910, todas las estrategias, sin elegir</h2>{t910.to_html(**fmt)}\n</body></html>"
    )


def agregar(salida: Path, modo_hp: str = "original", presupuesto_s: float = pr.PRESUPUESTO_S) -> dict[str, Path]:
    """Junta los CSV de las VMs: resumen por semilla, ranking y curva según K en 201908, presupuesto, 201910 y el HTML."""
    resumen, ensambles = leer(salida, modo_hp)
    ranking = ranking_201908(resumen)
    curva = curva_k_201908(ensambles)
    ens = ensambles_201908(ranking, ensambles)
    pres = pr.tabla_presupuesto(resumen, ensambles, presupuesto_s)
    ks = {int(r.estrategia): int(r.k_presupuesto) for r in pres.itertuples()}
    t910 = tabla_201910(ranking, resumen, ensambles, ks)
    destinos = {n: salida / f"{n}_{modo_hp}.csv" for n in
                ("resumen_50_semillas", "ranking_201908", "curva_k_201908", "ensambles_201908", "presupuesto", "tabla_201910")}
    for tabla, nombre in ((resumen, "resumen_50_semillas"), (ranking, "ranking_201908"), (curva, "curva_k_201908"),
                          (ens, "ensambles_201908"), (pres, "presupuesto"), (t910, "tabla_201910")):
        tabla.to_csv(destinos[nombre], index=False)
    destinos["html"] = salida / f"reporte_50_semillas_{modo_hp}.html"
    destinos["html"].write_text(html_reporte(ranking, resumen, curva, ens, pres, t910), encoding="utf-8")
    return destinos


def parsear(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--estrategia", type=int, help="1…9; una VM por estrategia")
    p.add_argument("--hp", choices=["original", "ledger"], default="original",
                   help="original: hp_original.json (réplica fiel); ledger: nuestros hp/*.json (H4_Hard sale de NH0.1)")
    p.add_argument("--semillas", type=int, default=es.N_SEMILLAS, help="cantidad de semillas (50 = las de Luis)")
    p.add_argument("--presupuesto", type=float, default=None,
                   help="segundos; si K = ⌊(P − T_opt)/T_final⌋ > --semillas, corre semillas extra hasta K")
    p.add_argument("--filas", type=int, default=None, help="smoke test: panel de ~N filas")
    p.add_argument("--salida", type=Path, default=SALIDA)
    p.add_argument("--agregar", action="store_true", help="junta los CSV de --salida y arma agregados y HTML (sin datos)")
    p.add_argument("--panel-luis", action="store_true",
                   help="D7: entrena con el panel de Luis (panel_luis.py) en vez de comun.datos; salida en <salida>/panel_luis")
    a = p.parse_args(argv)
    if not a.agregar and a.estrategia is None:
        p.error("falta --estrategia (o --agregar)")
    return a


def main(argv: list[str] | None = None) -> None:
    a = parsear(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    if a.agregar:
        for k, v in agregar(a.salida, a.hp, a.presupuesto or pr.PRESUPUESTO_S).items():
            print(f"{k}: {v}")
        return
    e = es.estrategia(a.estrategia)
    hp, t_opt = es.hp_de(e, a.hp)
    panel, salida = None, a.salida
    if a.panel_luis:   # D7 dio "distintos": se mide cuánto pesa el panel, aparte de las salidas con comun.datos
        panel = pl.ruta_panel_luis()
        if not panel.exists():
            pl.construir_panel_luis(dt.asegurar_crudo(), panel)
        salida = a.salida / "panel_luis"
    d = Datos(a.filas, panel)
    calib = calibracion(d)
    commit, sucio = correr.commit_y_sucio()   # procedencia: estas salidas no van al ledger de corridas
    calib.update(commit=commit, codigo_sucio=sucio, maquina=correr.tipo_de_maquina(),
                 panel="luis" if a.panel_luis else "comun.datos")
    filas, ensambles = correr_estrategia(e, hp, t_opt, a.semillas, d, a.hp, a.presupuesto)
    escribir_estrategia(salida, a.hp, e, filas, ensambles, calib)
    print(f"estrategia {e.id}: {len(filas)} semillas en {salida}")


if __name__ == "__main__":
    main()
