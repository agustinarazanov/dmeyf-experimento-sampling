"""Genera `experimentos/<exp>/informe/reporte.html` desde los ledgers y los documentos.

    python -m comun.reporte --experimento h1 [--salida HTML] [--figuras DIR]
    python -m comun.reporte --todos

Un reporte por experimento. Para `control`: su sección de `docs/hipotesis.md` y el estado de C. Para cada `hN`: su
hipótesis, la tabla de sus variantes contra el control y las bandas de curvas. Para `sampling_1`: todos las variantes de
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
from comun.ganancia import ganancia

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
    aps = [lg.leer_csv(rutas.ledger(e) / "apareado.csv") for e in reg.duenos()
           if (rutas.ledger(e) / "apareado.csv").exists()]
    ap = pd.concat(aps, ignore_index=True).drop_duplicates("variante") if aps else pd.DataFrame()
    return fin, ap.set_index("variante") if not ap.empty else ap


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
        return "<p class='pend'>pendiente: ningún variante tiene su ensamble</p>"
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


def generar(exp: str, figuras: Path | None = None) -> str:
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
    cuerpo = (f"<h1>{html.escape(titulo)}</h1><section>{intro}</section>"
              f"<section><h2>{'Todos las variantes' if ctx.agregador else 'Variantes'} contra el control</h2><p>"
              f"{html.escape(n_est)}. Vale la pena: no pierde y A ≥ {A_VALE:g}.</p>{tabla_variantes(ctx, fin, ap)}"
              + (fig_tiempo_ganancia(ctx, ap, figuras) if ctx.agregador else "") + "</section>")
    if ctx.agregador:
        cuerpo += f"<section><h2>Comparación a tiempo igual</h2>{tiempo_igual(ctx, fin, ap, figuras)}</section>"
    else:
        for h in ctx.hipotesis:
            cuerpo += seccion_hipotesis(ctx, h, seccion(hip, h + " "), fin, ap, figuras)
    cuerpo += markdown("## Limitaciones previstas\n" + seccion(hip, "Limitaciones"))
    cuerpo += enlaces(exp, [e for e in reg.duenos() if e != reg.CONTROL])
    cuerpo += (f"<footer>Generado {datetime.now():%Y-%m-%d %H:%M} · commit {commit()} · ledger: {len(fin)} corridas "
               f"finales, {completos}/{len(ctx.variantes) + 1} variantes con {N_SEMILLAS} semillas</footer>")
    return (f"<!doctype html><html lang='es'><head><meta charset='utf-8'><title>{html.escape(titulo)} — reporte"
            f"</title><style>{CSS}</style></head><body>{cuerpo}</body></html>\n")


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
        salida.write_text(generar(exp, a.figuras))
        print(salida)


if __name__ == "__main__":
    main()
