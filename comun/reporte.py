"""Genera `experimentos/<exp>/informe/reporte.html` desde los ledgers y los documentos.

    python -m comun.reporte --experimento h1 [--salida HTML] [--figuras DIR]
    python -m comun.reporte --todos

Un reporte por experimento. Para `control`: su sección de `docs/hipotesis.md` y el estado de C. Para cada `hN`: su
hipótesis, la tabla de sus variantes contra el control y las bandas de curvas. Para `sampling_1`: todas las variantes de
todas las hipótesis registradas en `comun/variantes.py`, tiempo contra ganancia, tiempo igual y enlaces a los demás.
Lee `resultados.csv`, `apareado.csv` y las curvas de los ledgers de `experimentos/*/` (los finales de C salen de
`control`). Un único HTML con las figuras embebidas (PNG en base64), sin servidor. Las variantes sin datos salen como
pendientes; ningún número se escribe a mano. Con `--figuras` además guarda cada figura como PNG (para el video).
"""

from __future__ import annotations

import argparse
import base64
import html
import io
import math
import re
import subprocess
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from comun import variantes as reg
from comun import ledger as lg
from comun import rutas
from comun.baseline import SEMILLAS_FINALES
from comun.ganancia import aporte, ganancia

N_SEMILLAS = 10
MES = 201910
SIN_REPORTE = {"C", "C-rep"}  # variantes del control: no tienen Δ, van en la fila C
PALETA = ["#2a6fb0", "#c4501b", "#2e8b57", "#8e5ea2", "#b8860b", "#c0392b"]
COLOR_C = "#555555"
A_VALE = 2.0  # hipotesis.md § Respuesta: vale la pena si no pierde y A ≥ 2


class Contexto:
    """Qué hipótesis y variantes entran en un reporte, salido del registro de `comun/variantes.py` (no de listas a mano)."""

    def __init__(self, exp: str):
        self.exp = exp
        self.agregador = exp == reg.AGREGADOR
        self.exps = [e for e in reg.duenos() if e != reg.CONTROL] if self.agregador else \
            ([] if exp == reg.CONTROL else [exp])
        self.hipotesis: dict[str, tuple[str, list[str]]] = {}  # "H1" -> (título, variantes)
        for e in self.exps:
            md = rutas.docs(e) / "hipotesis.md"
            sec = secciones(md.read_text()) if md.exists() else {}
            clave = next((k for k in sec if re.match(r"^H\d+\b", k)), e.upper())
            nombre, titulo = re.match(r"^(\S+)\s*(?:—\s*)?(.*)$", clave).groups()
            self.hipotesis[nombre] = (titulo or nombre,
                                      [b.nombre for b in reg.variantes_de(e) if b.nombre not in SIN_REPORTE])
        self.variantes = [b for _, bs in self.hipotesis.values() for b in bs]
        self.hip_de = {b: h for h, (_, bs) in self.hipotesis.items() for b in bs}
        self.color = {h: PALETA[i % len(PALETA)] for i, h in enumerate(self.hipotesis)}


# --- markdown mínimo (títulos, listas, tablas, párrafos, negrita, cursiva, código) ---

def _inline(t: str) -> str:
    t = html.escape(t, quote=False)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", t)
    return re.sub(r"(?<![\w*])\*([^*]+)\*(?![\w*])", r"<i>\1</i>", t)


def markdown(md: str, nivel: int = 0) -> str:
    out, lista, parrafo, tabla = [], [], [], []

    def cerrar() -> None:
        if parrafo:
            out.append(f"<p>{_inline(' '.join(parrafo))}</p>")
            parrafo.clear()
        if lista:
            out.append("<ul>" + "".join(f"<li>{_inline(i)}</li>" for i in lista) + "</ul>")
            lista.clear()
        if tabla:
            filas = [[c.strip() for c in f.strip("|").split("|")] for f in tabla if not re.match(r"^\|[-| :]+\|$", f)]
            cab = "".join(f"<th>{_inline(c)}</th>" for c in filas[0])
            cuerpo = "".join("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in f) + "</tr>" for f in filas[1:])
            out.append(f"<table><tr>{cab}</tr>{cuerpo}</table>")
            tabla.clear()

    for linea in md.splitlines():
        s = linea.strip()
        if not s:
            cerrar()
        elif m := re.match(r"^(#+)\s+(.*)", s):
            cerrar()
            n = min(len(m.group(1)) + nivel, 6)
            out.append(f"<h{n}>{_inline(m.group(2))}</h{n}>")
        elif s.startswith("|"):
            if parrafo or lista:
                cerrar()
            tabla.append(s)
        elif re.match(r"^[-*]\s", s):
            if parrafo or tabla:
                cerrar()
            lista.append(s[2:])
        elif lista and linea.startswith(" "):
            lista[-1] += " " + s
        else:
            if lista or tabla:
                cerrar()
            parrafo.append(s)
    cerrar()
    return "\n".join(out)


def secciones(md: str) -> dict[str, str]:
    """Secciones `## ...` de un markdown, por título."""
    partes = re.split(r"^## +(.*)$", md, flags=re.M)
    return {partes[i].strip(): partes[i + 1] for i in range(1, len(partes), 2)}


def seccion(sec: dict[str, str], prefijo: str) -> str:
    return next((v for k, v in sec.items() if k.startswith(prefijo)), "")


# --- datos ---

def _absolutas(fin: pd.DataFrame, base: Path) -> pd.DataFrame:
    """Rutas de curvas y predicciones absolutas, para mezclar finales de varios ledgers y leerlas igual."""
    fin = fin.copy()
    for col in [c for c in fin.columns if c.startswith(("curva_", "predicciones_"))]:
        fin[col] = fin[col].map(lambda r: str(base / r) if isinstance(r, str) else r)
    return fin


def cargar(exps: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(finales de los ledgers `exps`, apareado de todos los dueños de variantes). Las rutas de curvas y predicciones
    salen absolutas."""
    finales = []
    for e in exps:
        f = rutas.ledger(e) / "resultados.csv"
        if f.exists():
            r = lg.leer_csv(f)
            finales.append(_absolutas(r[r["etapa"] == "final"], rutas.ledger(e)))
    fin = pd.concat(finales, ignore_index=True) if finales else pd.DataFrame(columns=["variante"])
    if "replica_opt" in fin:  # lo de siempre es la réplica 0; las demás las lee `cargar_replicas`
        fin = fin[lg.con_replica(fin)["replica_opt"] == 0]
    aps =[lg.leer_csv(rutas.ledger(e) / "apareado.csv") for e in reg.duenos()
           if (rutas.ledger(e) / "apareado.csv").exists()]
    ap = pd.concat(aps, ignore_index=True).drop_duplicates("variante") if aps else pd.DataFrame()
    return fin, ap.set_index("variante") if not ap.empty else ap


def cargar_replicas(exps: list[str], n_est: int) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """(finales de todas las réplicas con `g` al corte `n_est`, tiempos de estudio, `replicas.csv` de los ledgers)."""
    finales, estudios, tablas = [], [], []
    for e in exps:
        led = rutas.ledger(e)
        if (led / "resultados.csv").exists():
            r = lg.leer_csv(led / "resultados.csv")
            finales.append(_absolutas(r[r["etapa"] == "final"], led))
        if (led / "estudios.csv").exists():
            estudios.append(lg.leer_csv(led / "estudios.csv"))
        if (led / "replicas.csv").exists():
            tablas.append(lg.leer_csv(led / "replicas.csv"))
    fin = lg.con_replica(pd.concat(finales, ignore_index=True)) if finales else pd.DataFrame(columns=["variante", "replica_opt"])
    if len(fin):
        fin = lg.agregar_ganancia(fin, pd.read_csv, n_est)
    est = pd.concat(estudios, ignore_index=True) if estudios else pd.DataFrame(columns=["estudio", "tiempo_optimizacion_s"])
    rep = pd.concat(tablas, ignore_index=True).drop_duplicates("variante") if tablas else pd.DataFrame(columns=["variante"])
    return fin, est, rep.set_index("variante")


def estado(variante: str, fin: pd.DataFrame) -> tuple[int, bool]:
    n = int((fin["variante"] == variante).sum())
    return n, n >= N_SEMILLAS


def fila(ap: pd.DataFrame, variante: str) -> pd.Series | None:
    return ap.loc[variante] if not ap.empty and variante in ap.index else None


def veredicto(ap: pd.DataFrame, fin: pd.DataFrame, variante: str) -> str:
    n, completo = estado(variante, fin)
    r = fila(ap, variante)
    if r is None:
        return "pendiente"
    return r["veredicto"] if completo else f"pendiente ({n}/{N_SEMILLAS} semillas; parcial: {r['veredicto']})"


def g_control(fin: pd.DataFrame, ap: pd.DataFrame) -> float | None:
    return float(ap["g_control"].iloc[0]) if not ap.empty else None


# --- figuras ---

def png(fig, nombre: str, figuras: Path | None) -> str:
    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", dpi=120, metadata={"Software": None})
    plt.close(fig)
    if figuras:
        figuras.mkdir(parents=True, exist_ok=True)
        (figuras / f"{nombre}.png").write_bytes(buf.getvalue())
    return f'<img alt="{nombre}" src="data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}">'


def fig_tiempo_ganancia(ctx: Contexto, ap: pd.DataFrame, figuras: Path | None) -> str:
    if ap.empty:
        return "<p class='pend'>pendiente: no hay apareado.csv (falta el control)</p>"
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    gc, tc = ap["g_control"].iloc[0], ap["tiempo_total_control_s"].iloc[0]
    ax.scatter([tc], [gc / 1e6], s=90, color=COLOR_C, marker="s", zorder=3, label="control")
    for h in ctx.hipotesis:
        sub = ap[ap.index.isin(ctx.hipotesis[h][1])]
        if sub.empty:
            continue
        g = (sub["g_control"] + sub["delta_g_media"]) / 1e6
        ax.errorbar(sub["tiempo_total_s"], g, yerr=[(sub["delta_g_media"] - sub["delta_g_ic_inf"]) / 1e6,
                                                     (sub["delta_g_ic_sup"] - sub["delta_g_media"]) / 1e6],
                    fmt="o", color=ctx.color[h], capsize=3, label=h, zorder=2)
        for b, x, y in zip(sub.index, sub["tiempo_total_s"], g):
            ax.annotate(b, (x, y), textcoords="offset points", xytext=(5, 4), fontsize=8, color=ctx.color[h])
    ax.axhline((gc - ap["delta_g_margen"].iloc[0]) / 1e6, color=COLOR_C, ls=":", lw=1, label="control − δ")
    ax.set_xscale("log")
    ax.set_xlabel("tiempo del pipeline T (s, escala log)")
    ax.set_ylabel(f"ganancia media en {MES} al corte N* (M$)")
    ax.set_title("Tiempo contra ganancia (barras: IC 95% de Δ apareado)")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, fontsize=8)
    return png(fig, "tiempo_vs_ganancia", figuras)


def banda(fin: pd.DataFrame, variante: str) -> pd.DataFrame | None:
    if f"curva_{MES}" not in fin:
        return None
    rutas = fin.loc[fin["variante"] == variante, f"curva_{MES}"]
    if rutas.empty:
        return None
    m = pd.concat([lg.leer_curva(Path(), r).set_index("envios")["ganancia"] for r in rutas], axis=1)
    return pd.DataFrame({"min": m.min(axis=1), "mediana": m.median(axis=1), "max": m.max(axis=1)})


def fig_bandas(ctx: Contexto, h: str, fin: pd.DataFrame, ap: pd.DataFrame, figuras: Path | None) -> str:
    variantes = [b for b in ctx.hipotesis[h][1] if estado(b, fin)[0]]
    bc = banda(fin, lg.CONTROL)
    if bc is None or not variantes:
        return "<p class='pend'>pendiente: faltan curvas del control o de las variantes</p>"
    n = len(variantes)
    fig, axs = plt.subplots(1, n, figsize=(3.6 * n, 3.4), sharey=True, squeeze=False)
    n_est = int(ap["n_estrella"].iloc[0]) if not ap.empty else None
    for ax, b in zip(axs[0], variantes):
        for nombre, color, bd in (("C", COLOR_C, bc), (b, ctx.color[h], banda(fin, b))):
            ax.fill_between(bd.index, bd["min"] / 1e6, bd["max"] / 1e6, color=color, alpha=0.2, lw=0)
            ax.plot(bd.index, bd["mediana"] / 1e6, color=color, lw=1.4, label=nombre)
        if n_est:
            ax.axvline(n_est, color="#999999", ls=":", lw=1)
        ax.set_xlim(0, 15000)
        ax.set_title(b, fontsize=10)
        ax.set_xlabel("envíos")
        ax.spines[["top", "right"]].set_visible(False)
        ax.legend(frameon=False, fontsize=8)
    axs[0][0].set_ylabel(f"ganancia {MES} (M$)")
    fig.suptitle(f"{h}: mediana y banda mín–máx entre semillas; punteada: N*", fontsize=10)
    return png(fig, f"bandas_{h}", figuras)


# --- tablas ---

def _m(x: float) -> str:
    return f"{x / 1e6:,.2f}"


def tabla_variantes(ctx: Contexto, fin: pd.DataFrame, ap: pd.DataFrame) -> str:
    cab = ("variante", "hipótesis", "semillas", "G media (M$)", "Δ media (M$)", "IC 95% de Δ (M$)", "semillas ganadas",
           "T (s)", "A", "veredicto", "vale la pena")
    filas = []
    if not ap.empty:
        filas.append(["C", "control", estado("C", fin)[0], _m(ap["g_control"].iloc[0]), "—", "—", "—",
                      f"{ap['tiempo_total_control_s'].iloc[0]:,.0f}", "1,00", "—", "—"])
    for b in ctx.variantes:
        r, n = fila(ap, b), estado(b, fin)[0]
        if r is None:
            filas.append([b, ctx.hip_de[b], n] + ["pendiente"] * 8)
            continue
        v = veredicto(ap, fin, b)
        vale = "sí" if v in ("no pierde", "gana") and r["aceleracion"] >= A_VALE else "no"
        filas.append([b, ctx.hip_de[b], int(r["n_semillas"]), _m(r["g_control"] + r["delta_g_media"]),
                      _m(r["delta_g_media"]), f"[{_m(r['delta_g_ic_inf'])}, {_m(r['delta_g_ic_sup'])}]",
                      f"{int(r['semillas_ganadas'])}/{int(r['n_semillas'])}", f"{r['tiempo_total_s']:,.0f}",
                      f"{r['aceleracion']:.2f}", v, vale if not v.startswith("pendiente") else "pendiente"])
    return html_tabla(cab, filas)


def html_tabla(cab, filas) -> str:
    def td(c):
        c = str(c)
        clase = {"pierde": "pierde", "no pierde": "ok", "gana": "ok", "indeterminado": "ind"}.get(c)
        clase = clase or ("pend" if c.startswith("pendiente") else "")
        return f"<td class='{clase}'>{html.escape(c)}</td>" if clase else f"<td>{html.escape(c)}</td>"
    return ("<table><tr>" + "".join(f"<th>{html.escape(c)}</th>" for c in cab) + "</tr>"
            + "".join("<tr>" + "".join(td(c) for c in f) + "</tr>" for f in filas) + "</table>")


def ensamble(fin: pd.DataFrame, variante: str, k: int, n_est: int) -> float | None:
    """Ganancia al corte N* del promedio de `prob` de las primeras k semillas (orden de `semillas_pedidas`).

    None si falta alguna de esas semillas o su parquet de predicciones.
    """
    sub = fin[fin["variante"] == variante].set_index("semilla")
    probs, es_baja2, clientes = [], None, None
    for s in SEMILLAS_FINALES[:k]:
        ruta = sub["predicciones_201910"].get(s) if "predicciones_201910" in sub else None
        if not isinstance(ruta, str) or not Path(ruta).exists():
            return None
        p = pd.read_parquet(ruta)
        if clientes is None:
            clientes, es_baja2 = p["numero_de_cliente"].to_numpy(), p["es_baja2"].to_numpy()
        elif not np.array_equal(clientes, p["numero_de_cliente"].to_numpy()):
            raise ValueError(f"{variante} semilla {s}: las predicciones no están en el mismo orden de clientes")
        probs.append(p["prob"].to_numpy(dtype="float64"))
    return ganancia(np.mean(probs, axis=0), es_baja2, n_est)


def calcular_tiempo_igual(ctx: Contexto, fin: pd.DataFrame, ap: pd.DataFrame) -> tuple[float | None, dict]:
    """(G del ensamble de las 10 semillas del control, {variante: (T_opt, T_final, K, G del ensamble de K) o None})."""
    n_est, tc = int(ap["n_estrella"].iloc[0]), ap["tiempo_total_control_s"].iloc[0]
    g_c10 = ensamble(fin, lg.CONTROL, N_SEMILLAS, n_est)
    datos = {}
    for b in ctx.variantes:
        r = fila(ap, b)
        if r is None or not estado(b, fin)[1]:
            datos[b] = None
            continue
        t_fin = fin.loc[fin["variante"] == b, "tiempo_entrenamiento_s"].mean()
        t_opt = r["tiempo_total_s"] - t_fin
        k = max(0, math.floor((tc - t_opt) / t_fin))
        g = ensamble(fin, b, min(k, N_SEMILLAS), n_est) if k >= 2 else None
        datos[b] = (t_opt, t_fin, k, g)
    return g_c10, datos


def tiempo_igual(ctx: Contexto, fin: pd.DataFrame, ap: pd.DataFrame, figuras: Path | None) -> str:
    """K = semillas de la variante que entran en T(control): (T_C − T_opt) / T_final, con T_final medio de la variante."""
    intro = ("<p>Se le da a cada variante el tiempo del control: después de su optimización, el sobrante se gasta en K "
             "modelos finales con semillas distintas, K = ⌊(T(C) − T_opt) / T_final⌋, acotado a las "
             f"{N_SEMILLAS} semillas que hay. T_final es la media de <code>tiempo_entrenamiento_s</code> de la variante y "
             "T_opt = T − T_final. Para K ≥ 2 se promedia fila a fila <code>prob</code> de las primeras K semillas "
             f"(en el orden de <code>semillas_pedidas</code>) y se mide la ganancia en {MES} al corte N*. Se compara "
             "con Ḡ_C (un modelo del control, media de sus 10 semillas) y, como referencia, con el ensamble de las "
             f"{N_SEMILLAS} semillas del control.</p>")
    if ap.empty or not estado(lg.CONTROL, fin)[1]:
        return intro + "<p class='pend'>pendiente: el control no tiene sus 10 semillas</p>"
    g_c1 = g_control(fin, ap)
    g_c10, datos = calcular_tiempo_igual(ctx, fin, ap)
    ref = f"Ḡ_C = {_m(g_c1)} M$; ensamble de {N_SEMILLAS} semillas del control = " + (
        f"{_m(g_c10)} M$" if g_c10 is not None else "pendiente (faltan predicciones del control)")
    filas = []
    for b in ctx.variantes:
        d = datos[b]
        if d is None:
            filas.append([b] + ["pendiente"] * 6)
            continue
        t_opt, t_fin, k, g = d
        k_txt = f"{k:,}" + (f" (se usan {N_SEMILLAS})" if k > N_SEMILLAS else "")
        if k < 2:
            filas.append([b, f"{t_opt:,.0f}", f"{t_fin:,.1f}", k_txt] + ["no aplica (K < 2)"] * 3)
        elif g is None:
            filas.append([b, f"{t_opt:,.0f}", f"{t_fin:,.1f}", k_txt] + ["pendiente: faltan predicciones"] * 3)
        else:
            filas.append([b, f"{t_opt:,.0f}", f"{t_fin:,.1f}", k_txt, _m(g), _m(g - g_c1),
                          _m(g - g_c10) if g_c10 is not None else "pendiente"])
    return (intro + f"<p>{html.escape(ref)}.</p>"
            + html_tabla(("variante", "T_opt (s)", "T_final (s)", "K", f"G del ensamble en {MES} (M$)",
                          "G − Ḡ_C (M$)", f"G − ensamble {N_SEMILLAS} de C (M$)"), filas)
            + fig_tiempo_igual(ctx, g_c1, g_c10, datos, figuras))


def fig_tiempo_igual(ctx: Contexto, g_c1: float, g_c10: float | None, datos: dict, figuras: Path | None) -> str:
    pts = [(b, d[3]) for b, d in datos.items() if d is not None and d[3] is not None]
    if not pts:
        return "<p class='pend'>pendiente: ninguna variante tiene su ensamble</p>"
    fig, ax = plt.subplots(figsize=(7.5, 0.35 * len(pts) + 1.6))
    for i, (b, g) in enumerate(pts):
        ax.scatter([g / 1e6], [i], color=ctx.color[ctx.hip_de[b]], zorder=3)
        ax.annotate(f"K={min(datos[b][2], N_SEMILLAS)}", (g / 1e6, i), textcoords="offset points", xytext=(6, -3),
                    fontsize=7, color=ctx.color[ctx.hip_de[b]])
    ax.axvline(g_c1 / 1e6, color=COLOR_C, ls=":", lw=1, label="Ḡ_C (un modelo)")
    if g_c10 is not None:
        ax.axvline(g_c10 / 1e6, color=COLOR_C, ls="--", lw=1, label=f"ensamble de {N_SEMILLAS} de C")
    ax.set_yticks(range(len(pts)), [b for b, _ in pts], fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel(f"ganancia en {MES} al corte N* (M$)")
    ax.set_title("A tiempo igual: ensamble de K semillas de cada variante", fontsize=10)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, fontsize=8)
    return png(fig, "tiempo_igual", figuras)


# --- comparación limpia: tiempo igual con intervalo, bloque A y bloque B (`h3-semillas-optuna` D6, D7) ---

N_BOOT = 1000
SEMILLA_BOOT = 20261108
GRADOS = 0.95


def _tiempos(estudios: pd.DataFrame) -> pd.Series:
    return estudios.groupby("estudio")["tiempo_optimizacion_s"].last()


def tiempo_replica(fin_k: pd.DataFrame, t_estudio: pd.Series) -> tuple[float, float] | None:
    """(tiempo de optimización del estudio, media del tiempo de entrenamiento final) de una variante en una réplica."""
    if fin_k.empty or fin_k["estudio"].iloc[0] not in t_estudio.index:
        return None
    return float(t_estudio[fin_k["estudio"].iloc[0]]), float(fin_k["tiempo_entrenamiento_s"].mean())


def tiempo_igual_replicas(variante: str, finr: pd.DataFrame, estudios: pd.DataFrame, n_est: int) -> dict | None:
    """Por réplica k, el ensamble de K_k semillas de la variante en el presupuesto del control de esa réplica contra Ḡ_C,k.

    Devuelve las listas por réplica y la media con IC t entre réplicas (None si la variante tiene menos de dos réplicas)."""
    t_est = _tiempos(estudios)
    v, c = finr[finr["variante"] == variante], finr[finr["variante"] == lg.CONTROL]
    ks = sorted(set(v["replica_opt"]) & set(c["replica_opt"]))
    if len(set(v["replica_opt"])) < 2:
        return None
    filas = []
    for k in ks:
        vk, ck = v[v["replica_opt"] == k], c[c["replica_opt"] == k]
        tv, tc = tiempo_replica(vk, t_est), tiempo_replica(ck, t_est)
        if tv is None or tc is None:
            continue
        t_c, t_v = tc[0] + tc[1], tv[0] + tv[1]
        kk = max(0, math.floor((t_c - tv[0]) / tv[1]))
        g = ensamble(vk, variante, min(kk, N_SEMILLAS), n_est) if kk >= 2 else None
        filas.append({"replica": k, "T_v": t_v, "T_c": t_c, "K": kk, "g_ens": g, "g_c": float(ck["g"].mean())})
    d = np.array([f["g_ens"] - f["g_c"] for f in filas if f["g_ens"] is not None], dtype=float)
    media, _, lo, hi = lg._ic(d) if len(d) else (float("nan"),) * 4
    return {"filas": filas, "n": len(d), "media": media, "inf": lo, "sup": hi,
            "T": float(np.median([f["T_v"] for f in filas])) if filas else float("nan"),
            "T_c": float(np.median([f["T_c"] for f in filas])) if filas else float("nan")}


def _probs(fin: pd.DataFrame, variante: str, k: int) -> tuple[np.ndarray, np.ndarray, list[np.ndarray]] | None:
    """(clientes, es_baja2, `prob` de las primeras k semillas) de la réplica 0 de una variante; None si falta alguna."""
    sub = fin[fin["variante"] == variante].set_index("semilla")
    probs, clientes, baja2 = [], None, None
    for s in SEMILLAS_FINALES[:k]:
        ruta = sub["predicciones_201910"].get(s) if "predicciones_201910" in sub else None
        if not isinstance(ruta, str) or not Path(ruta).exists():
            return None
        p = pd.read_parquet(ruta)
        if clientes is None:
            clientes, baja2 = p["numero_de_cliente"].to_numpy(), p["es_baja2"].to_numpy()
        elif not np.array_equal(clientes, p["numero_de_cliente"].to_numpy()):
            raise ValueError(f"{variante} semilla {s}: las predicciones no están en el mismo orden de clientes")
        probs.append(p["prob"].to_numpy(dtype="float64"))
    return (clientes, baja2, probs) if probs else None


def bootstrap_tiempo_igual(fin: pd.DataFrame, datos: dict, n_est: int, n_boot: int = N_BOOT) -> dict:
    """IC por bootstrap de clientes de `G(ensamble de K) − Ḡ_C` en la réplica 0 (`datos` sale de `calcular_tiempo_igual`).

    Cada remuestreo toma los n clientes de 201910 con reposición (`default_rng(SEMILLA_BOOT)`) y mide todas las variantes
    en el mismo remuestreo. El corte es N* · n_b / n, redondeado, con n_b el tamaño del remuestreo; como solo cuenta el
    principio del orden por score, se ordena una vez y se recorre un prefijo."""
    ctrl = _probs(fin, lg.CONTROL, N_SEMILLAS)
    if ctrl is None:
        return {}
    clientes, baja2, p_c = ctrl
    n = len(clientes)
    contrib = aporte(baja2)
    ordenes: dict[str, np.ndarray] = {}
    vectores: dict[str, np.ndarray] = {f"__c{i}": p for i, p in enumerate(p_c)}
    for b, d in datos.items():
        if d is None or d[3] is None:
            continue
        pr = _probs(fin, b, min(d[2], N_SEMILLAS))
        if pr is not None and np.array_equal(pr[0], clientes):
            vectores[b] = np.mean(pr[2], axis=0)
    for nombre, p in vectores.items():
        ordenes[nombre] = np.argsort(-p, kind="stable")[: 2 * n_est + 1000]
    rng = np.random.default_rng(SEMILLA_BOOT)
    difs = {b: np.empty(n_boot) for b in vectores if not b.startswith("__c")}
    for i in range(n_boot):
        cuenta = np.bincount(rng.integers(0, n, n), minlength=n)
        corte = round(n_est * cuenta.sum() / n)

        def g_corte(nombre: str) -> float:
            o = ordenes[nombre]
            c, a = cuenta[o], contrib[o]
            acum = np.cumsum(c)
            j = int(np.searchsorted(acum, corte, side="left"))
            previo = acum[j - 1] if j else 0
            return float((c[:j] * a[:j]).sum() + (corte - previo) * a[j])

        g_c = np.mean([g_corte(f"__c{s}") for s in range(len(p_c))])
        for b in difs:
            difs[b][i] = g_corte(b) - g_c
    alfa = (1 - GRADOS) / 2 * 100
    return {b: (float(np.mean(d)), float(np.percentile(d, alfa)), float(np.percentile(d, 100 - alfa)))
            for b, d in difs.items()}


def fila_bloque_a(ctx: Contexto, b: str, fin: pd.DataFrame, ap: pd.DataFrame, rep: pd.DataFrame,
                  ti_rep: dict | None, ti_boot: tuple | None, k0: tuple | None) -> dict:
    """Una fila del bloque A, con todo lo que muestran la tabla HTML y `tabla_resultados.md`."""
    r, rr = fila(ap, b), (rep.loc[b] if b in rep.index else None)
    con_rep = rr is not None and pd.notna(rr.get("delta_g_media"))
    out = {"variante": b, "hipotesis": ctx.hip_de[b], "d0": None, "dR": None, "G": None, "T": None, "A": None,
           "ti_rep": ti_rep, "ti_boot": ti_boot, "k0": k0, "nota": ""}
    if r is not None:
        out.update(G=float(r["g_control"] + r["delta_g_media"]), T=float(r["tiempo_total_s"]), A=float(r["aceleracion"]),
                   d0=(float(r["delta_g_media"]), float(r["delta_g_ic_inf"]), float(r["delta_g_ic_sup"])))
    if con_rep:
        out["dR"] = (float(rr["delta_g_media"]), float(rr["delta_g_ic_inf"]), float(rr["delta_g_ic_sup"]), int(rr["n_replicas"]))
        out["G"] = float(rr["g_media_replicas"])
        if ti_rep and ti_rep["T"] == ti_rep["T"] and ti_rep["T"] > 0:
            out["T"], out["A"] = ti_rep["T"], ti_rep["T_c"] / ti_rep["T"]
        out["veredicto"], out["fuente"] = str(rr["veredicto"]), f"con réplicas ({int(rr['n_replicas'])})"
    else:
        out["veredicto"], out["fuente"] = veredicto(ap, fin, b), "réplica 0"
        out["nota"] = "sin réplicas"
    return out


def calcular_bloque_a(ctx: Contexto, fin: pd.DataFrame, ap: pd.DataFrame, n_boot: int = N_BOOT) -> dict:
    """Todo el bloque A y las tablas de réplicas, calculado una vez desde el ledger."""
    vacio = {"filas": [], "rep": pd.DataFrame(), "g_c1": None, "g_c10": None, "ti": {}}
    if ap.empty or not estado(lg.CONTROL, fin)[1]:
        return vacio
    n_est = int(ap["n_estrella"].iloc[0])
    finr, estudios, rep = cargar_replicas([reg.CONTROL, *ctx.exps], n_est)
    g_c1 = g_control(fin, ap)
    g_c10, datos = calcular_tiempo_igual(ctx, fin, ap)
    boot = bootstrap_tiempo_igual(fin, datos, n_est, n_boot)
    filas = []
    for b in ctx.variantes:
        ti = tiempo_igual_replicas(b, finr, estudios, n_est) if len(finr) else None
        filas.append(fila_bloque_a(ctx, b, fin, ap, rep, ti, boot.get(b), datos.get(b)))
    filas.sort(key=lambda f: (list(ctx.hipotesis).index(f["hipotesis"]), -(f["A"] if f["A"] is not None else -1.0)))
    return {"filas": filas, "rep": rep, "g_c1": g_c1, "g_c10": g_c10, "n_est": n_est}


def _ic_txt(t: tuple | None) -> str:
    return "pendiente" if t is None else f"{_m(t[0])} [{_m(t[1])}; {_m(t[2])}]"


def celdas_bloque_a(f: dict) -> list[str]:
    tr, tb, k0 = f["ti_rep"], f["ti_boot"], f["k0"]
    if tr and tr["n"] >= 2:
        ti_rep = f"{_ic_txt((tr['media'], tr['inf'], tr['sup']))} (R={tr['n']})"
    else:
        ti_rep = "sin réplicas" if not tr else f"no aplica (K<2 en {len(tr['filas']) - tr['n']} de {len(tr['filas'])} réplicas)"
    ti_boot = _ic_txt(tb) if tb else ("no aplica (K<2)" if k0 and k0[2] < 2 else "pendiente")
    dR = f"{_ic_txt(f['dR'][:3])} (R={f['dR'][3]})" if f["dR"] else "—"
    return [f["variante"], f["hipotesis"], _m(f["G"]) if f["G"] is not None else "pendiente", _ic_txt(f["d0"]), dR,
            f"{f['T']:,.0f}" if f["T"] is not None else "pendiente", f"{f['A']:.2f}" if f["A"] is not None else "pendiente",
            ti_rep, ti_boot, f"{f['veredicto']} ({f['fuente']})"]


CAB_A = ("variante", "hipótesis", "Ḡ (M$)", "Δ réplica 0 [IC] (M$)", "Δ con réplicas [IC] (M$)", "T mediana (s)", "A",
         "tiempo igual, réplicas [IC t] (M$)", "tiempo igual, bootstrap de clientes [IC] (M$)", "veredicto (fuente)")


def pares_replicas(rep: pd.DataFrame) -> list[list[str]]:
    """Filas `a - b` de `replicas.csv` (diferencia apareada por réplica y semilla)."""
    return [[v, _ic_txt((r["delta_g_media"], r["delta_g_ic_inf"], r["delta_g_ic_sup"])), f"{int(r['n_replicas'])}",
             str(r["veredicto"])] for v, r in rep.iterrows() if " - " in v]


def varianza(rep: pd.DataFrame, ctx: Contexto) -> list[list[str]]:
    filas = []
    for v, r in rep.iterrows():
        if " - " in v:
            continue
        filas.append([v, f"{int(r['n_replicas'])}", f"{int(r['n_semillas'])}", f"{r['sd_entre_replicas'] / 1e6:.2f}",
                      f"{r['sd_dentro_medio'] / 1e6:.2f}", f"{100 * r['frac_entre']:.0f} %"])
    return filas


CAB_VAR = ("variante", "réplicas", "corridas", "sd entre réplicas (M$)", "sd entre semillas (M$)", "varianza entre réplicas")
CAB_PARES = ("diferencia", "Δ [IC t entre réplicas] (M$)", "réplicas", "veredicto")
AVISO_B = "Las cifras del bloque B no se comparan una a una con las del bloque A: otro protocolo, otra muestra o otro entorno."


def _resumen_columna(s: pd.Series) -> str:
    x = pd.to_numeric(s, errors="coerce").dropna()
    if x.empty:
        return "sin datos numéricos"
    f = (lambda v: f"{v:,.0f}") if x.abs().max() >= 1000 else (lambda v: f"{v:.4g}")
    return f"mediana {f(x.median())} [{f(x.min())}; {f(x.max())}], n = {len(x)}"


def bloque_b(raiz: Path = rutas.RAIZ) -> list[dict]:
    """Una fila por `exploratorio.json`. Un CSV que falta deja la tabla como pendiente con el nombre del archivo."""
    import json
    filas = []
    for m in reg.manifiestos(raiz):
        d = json.loads(m.read_text())
        cifras = []
        for t in d.get("tablas", []):
            ruta = m.parent / t["csv"]
            if not ruta.is_file():
                cifras.append(f"pendiente: falta {t['csv']}")
                continue
            df = pd.read_csv(ruta)
            for c in t["columnas"]:
                cifras.append(f"{ruta.name}, {c}: " + (_resumen_columna(df[c]) if c in df else f"pendiente: falta la columna {c}"))
        filas.append({"carpeta": str(m.parent.relative_to(raiz)), "autor": d.get("autor", ""), "pregunta": d.get("pregunta", ""),
                      "protocolo": d.get("protocolo", ""), "cifras": cifras, "advertencia": d.get("advertencia", "")})
    return filas


def tabla_md(cab, filas) -> str:
    esc = lambda c: str(c).replace("|", "\\|").replace("\n", " ")
    return ("| " + " | ".join(cab) + " |\n|" + "---|" * len(cab) + "\n"
            + "".join("| " + " | ".join(esc(c) for c in f) + " |\n" for f in filas))


def filas_b(b: list[dict]) -> list[list[str]]:
    return [[f["carpeta"], f["autor"], f["pregunta"], f["protocolo"], "; ".join(f["cifras"]), f["advertencia"]] for f in b]


CAB_B = ("carpeta", "autor", "pregunta", "protocolo", "cifras principales", "advertencia")


def markdown_resultados(ctx: Contexto, a: dict, b: list[dict]) -> str:
    """`informe/tabla_resultados.md`: las tablas que copia el informe, sin fecha ni cifras escritas a mano."""
    if not a["filas"]:
        return "# Resultados\n\npendiente: el control no tiene sus 10 semillas.\n"
    partes = ["# Resultados de sampling_1\n",
              "Generado por `python -m comun.reporte --experimento sampling_1`; no editar a mano.\n",
              f"N* = {a['n_est']:,} envíos; Ḡ_C (réplica 0) = {_m(a['g_c1'])} M$"
              + (f"; ensamble de {N_SEMILLAS} semillas del control = {_m(a['g_c10'])} M$" if a["g_c10"] is not None else "") + ".\n",
              "## Bloque A: mismo protocolo\n", tabla_md(CAB_A, [celdas_bloque_a(f) for f in a["filas"]])]
    notas = [f"- `{f['variante']}`: {f['nota']}" for f in a["filas"] if f["nota"]]
    if notas:
        partes += ["Notas:\n", "\n".join(notas) + "\n"]
    if len(a["rep"]):
        partes += ["### Varianza entre réplicas y entre semillas\n", tabla_md(CAB_VAR, varianza(a["rep"], ctx))]
        pares = pares_replicas(a["rep"])
        if pares:
            partes += ["### Diferencia apareada por réplica y semilla\n", tabla_md(CAB_PARES, pares)]
    partes += ["## Bloque B: exploratorios\n", AVISO_B + "\n", tabla_md(CAB_B, filas_b(b)) if b else "No hay exploratorios declarados.\n"]
    return "\n".join(partes)


def fig_tiempo_ganancia_replicas(ctx: Contexto, a: dict, ap: pd.DataFrame, figuras: Path | None) -> str:
    if not a["filas"]:
        return "<p class='pend'>pendiente: no hay apareado.csv (falta el control)</p>"
    rep = a["rep"]
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    gc, tc = ap["g_control"].iloc[0], ap["tiempo_total_control_s"].iloc[0]
    ax.scatter([tc], [gc / 1e6], s=90, color=COLOR_C, marker="s", zorder=3, label="control (réplica 0)")
    for h in ctx.hipotesis:
        for f in [f for f in a["filas"] if f["hipotesis"] == h and f["G"] is not None and f["T"] is not None]:
            y = f["G"] / 1e6
            if f["variante"] in rep.index and f["dR"]:
                r = rep.loc[f["variante"]]
                ax.errorbar([f["T"]], [y], yerr=[[y - r["g_min_replicas"] / 1e6], [r["g_max_replicas"] / 1e6 - y]],
                            fmt="o", color=ctx.color[h], capsize=3, zorder=2)
            else:
                ax.scatter([f["T"]], [y], color=ctx.color[h], zorder=2)
            ax.annotate(f["variante"], (f["T"], y), textcoords="offset points", xytext=(5, 4), fontsize=8, color=ctx.color[h])
    for h in ctx.hipotesis:
        ax.scatter([], [], color=ctx.color[h], label=h)
    ax.axhline((gc - ap["delta_g_margen"].iloc[0]) / 1e6, color=COLOR_C, ls=":", lw=1, label="control − δ")
    ax.set_xscale("log")
    ax.set_xlabel("tiempo del pipeline T (s, escala log; mediana entre réplicas)")
    ax.set_ylabel(f"ganancia media en {MES} al corte N* (M$)")
    ax.set_title("Tiempo contra ganancia (barras: rango entre réplicas; sin barra: una sola réplica)", fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, fontsize=8)
    return png(fig, "tiempo_vs_ganancia", figuras)


def fig_varianza(ctx: Contexto, a: dict, figuras: Path | None) -> str:
    rep = a["rep"]
    r = rep[[" - " not in v for v in rep.index]] if len(rep) else rep
    if r.empty:
        return "<p class='pend'>pendiente: ninguna variante tiene réplicas</p>"
    fig, ax = plt.subplots(figsize=(7.5, 0.4 * len(r) + 1.6))
    entre, dentro = r["var_entre"] / r["var_total"], r["var_dentro"] / r["var_total"]
    y = np.arange(len(r))
    ax.barh(y, entre, color=PALETA[0], label="entre réplicas (suerte de Optuna)")
    ax.barh(y, dentro, left=entre, color=PALETA[1], label="entre semillas")
    ax.set_yticks(y, list(r.index), fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("fracción de la varianza de G")
    ax.set_title("Descomposición de la varianza de la ganancia", fontsize=10)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    return png(fig, "varianza", figuras)


def html_resultados(ctx: Contexto, a: dict, b: list[dict], ap: pd.DataFrame, figuras: Path | None) -> str:
    if not a["filas"]:
        return "<p class='pend'>pendiente: el control no tiene sus 10 semillas</p>"
    out = ["<h3>Bloque A: mismo protocolo</h3>", html_tabla(CAB_A, [celdas_bloque_a(f) for f in a["filas"]]),
           fig_tiempo_ganancia_replicas(ctx, a, ap, figuras)]
    notas = [f"{f['variante']}: {f['nota']}" for f in a["filas"] if f["nota"]]
    if notas:
        out.append(f"<p>Notas: {html.escape('; '.join(notas))}.</p>")
    if len(a["rep"]):
        out += ["<h3>Varianza entre réplicas y entre semillas</h3>", html_tabla(CAB_VAR, varianza(a["rep"], ctx)),
                fig_varianza(ctx, a, figuras)]
        pares = pares_replicas(a["rep"])
        if pares:
            out += ["<h3>Diferencia apareada por réplica y semilla</h3>", html_tabla(CAB_PARES, pares)]
    out += ["<h3>Bloque B: exploratorios</h3>", f"<p>{html.escape(AVISO_B)}</p>",
            html_tabla(CAB_B, filas_b(b)) if b else "<p>No hay exploratorios declarados.</p>"]
    return "".join(out)


def seccion_hipotesis(ctx: Contexto, h: str, md_h: str, fin: pd.DataFrame, ap: pd.DataFrame,
                      figuras: Path | None) -> str:
    titulo, variantes = ctx.hipotesis[h]
    filas = []
    for b in variantes:
        r = fila(ap, b)
        filas.append([b, veredicto(ap, fin, b)] + ([f"{_m(r['delta_g_media'])}",
                      f"[{_m(r['delta_g_ic_inf'])}, {_m(r['delta_g_ic_sup'])}]", f"{r['aceleracion']:.2f}"]
                                                  if r is not None else ["pendiente"] * 3))
    return (f"<section><h2>{h} — {html.escape(titulo)}</h2>"
            f"<details open><summary>Predicción y regla (de <code>docs/hipotesis.md</code>)</summary>"
            f"{markdown(md_h, 1)}</details>"
            + html_tabla(("variante", "veredicto", "Δ media (M$)", "IC 95% (M$)", "A"), filas)
            + fig_bandas(ctx, h, fin, ap, figuras) + "</section>")


def commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                              cwd=rutas.RAIZ, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "desconocido"


CSS = """body{font-family:system-ui,sans-serif;max-width:1100px;margin:2em auto;padding:0 1em;color:#222;line-height:1.45}
table{border-collapse:collapse;margin:1em 0;font-size:.9em}th,td{border:1px solid #ccc;padding:.25em .5em;text-align:left}
th{background:#f3f3f3}td.pierde{background:#f8d7d0}td.ok{background:#d6ecd9}td.ind{background:#fbefc8}
.pend{color:#888;font-style:italic}img{max-width:100%}code{background:#f3f3f3;padding:0 .2em}
details{margin:.5em 0}summary{cursor:pointer;font-weight:600}footer{margin-top:3em;color:#666;font-size:.85em}"""


def _leer(exp: str, nombre: str) -> dict[str, str]:
    f = rutas.docs(exp) / f"{nombre}.md"
    return secciones(f.read_text()) if f.exists() else {}


def enlaces(exp: str, exps: list[str]) -> str:
    """Enlaces relativos a los reportes de los demás experimentos del registro."""
    otros = [e for e in dict.fromkeys([reg.AGREGADOR, reg.CONTROL, *exps]) if e != exp]
    items = "".join(f"<li><a href='../../{e}/informe/reporte.html'>{e}</a></li>" for e in otros)
    return f"<section><h2>Otros reportes</h2><ul>{items}</ul></section>"


def generar_con_tabla(exp: str, figuras: Path | None = None) -> tuple[str, str | None]:
    """(HTML del reporte, `tabla_resultados.md` del agregador o None para los demás experimentos)."""
    ctx = Contexto(exp)
    fin, ap = cargar([reg.CONTROL, *ctx.exps])
    hip, dis = _leer(exp, "hipotesis"), _leer(exp, "diseno")
    if exp == reg.CONTROL:
        intro = (markdown("## Control\n" + seccion(hip, "Control"))
                 + markdown("## Métricas y reglas comunes\n" + seccion(hip, "Métricas")))
    elif ctx.agregador:
        intro = markdown("## Pregunta\n" + seccion(hip, "Pregunta"))
    else:
        intro = (markdown("## Variantes\n" + seccion(dis, "Variantes"))
                 + "<p>Las reglas, G, Δ, δ, T, A y N* están en <code>control/docs/hipotesis.md</code> "
                   "(<a href='../../control/informe/reporte.html'>reporte del control</a>).</p>")
    n_est = f"N* = {int(ap['n_estrella'].iloc[0]):,} envíos (de 201908); δ = {_m(ap['delta_g_margen'].iloc[0])} M$" \
        if not ap.empty else "N* pendiente"
    completos = sum(estado(b, fin)[1] for b in ["C", *ctx.variantes])
    titulo = {reg.CONTROL: "Control", reg.AGREGADOR: "Sampling_1 — velocidad contra ganancia"}.get(exp, exp)
    md = None
    cuerpo = f"<h1>{html.escape(titulo)}</h1><section>{intro}</section>"
    if ctx.agregador:
        a, b = calcular_bloque_a(ctx, fin, ap), bloque_b()
        md = markdown_resultados(ctx, a, b)
        cuerpo += (f"<section><h2>Todas las variantes contra el control</h2><p>{html.escape(n_est)}. "
                   f"Vale la pena: no pierde y A ≥ {A_VALE:g}.</p>{html_resultados(ctx, a, b, ap, figuras)}</section>")
        cuerpo += f"<section><h2>Comparación a tiempo igual</h2>{tiempo_igual(ctx, fin, ap, figuras)}</section>"
    else:
        cuerpo += (f"<section><h2>Variantes contra el control</h2><p>{html.escape(n_est)}. "
                   f"Vale la pena: no pierde y A ≥ {A_VALE:g}.</p>{tabla_variantes(ctx, fin, ap)}</section>")
        for h in ctx.hipotesis:
            cuerpo += seccion_hipotesis(ctx, h, seccion(hip, h + " "), fin, ap, figuras)
    cuerpo += markdown("## Limitaciones previstas\n" + seccion(hip, "Limitaciones"))
    cuerpo += enlaces(exp, [e for e in reg.duenos() if e != reg.CONTROL])
    cuerpo += (f"<footer>Generado {datetime.now():%Y-%m-%d %H:%M} · commit {commit()} · ledger: {len(fin)} corridas "
               f"finales (réplica 0), {completos}/{len(ctx.variantes) + 1} variantes con {N_SEMILLAS} semillas</footer>")
    return (f"<!doctype html><html lang='es'><head><meta charset='utf-8'><title>{html.escape(titulo)} — reporte"
            f"</title><style>{CSS}</style></head><body>{cuerpo}</body></html>\n"), md


def generar(exp: str, figuras: Path | None = None) -> str:
    return generar_con_tabla(exp, figuras)[0]


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--experimento", help="carpeta de experimentos/ (control, h1, ..., sampling_1)")
    g.add_argument("--todos", action="store_true", help="un reporte por cada experimento del registro")
    p.add_argument("--salida", type=Path, help="HTML de salida (solo con --experimento)")
    p.add_argument("--figuras", type=Path, help="además guarda las figuras como PNG en este directorio")
    a = p.parse_args()
    exps = [reg.CONTROL, *[e for e in reg.duenos() if e != reg.CONTROL], reg.AGREGADOR] if a.todos else [a.experimento]
    for exp in exps:
        salida = a.salida or rutas.informe(exp) / "reporte.html"
        salida.parent.mkdir(parents=True, exist_ok=True)
        pagina, md = generar_con_tabla(exp, a.figuras)
        salida.write_text(pagina)
        print(salida)
        if md is not None and not a.salida:
            (salida.parent / "tabla_resultados.md").write_text(md)
            print(salida.parent / "tabla_resultados.md")


if __name__ == "__main__":
    main()
