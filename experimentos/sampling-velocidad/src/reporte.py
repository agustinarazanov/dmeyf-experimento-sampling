"""Genera `informe/reporte.html` desde el ledger y los documentos del experimento.

    python -m experimentos.sampling-velocidad.src.reporte [--ledger DIR] [--salida HTML] [--figuras DIR]

Lee `ledger/resultados.csv`, `ledger/apareado.csv`, las curvas y `docs/hipotesis.md` / `docs/diseno.md`. Un único HTML
con las figuras embebidas (PNG en base64), sin servidor. Los brazos sin datos salen como pendientes; ningún número se
escribe a mano. Con `--figuras` además guarda cada figura como PNG (para el video).
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
import pandas as pd

from comun import ledger as lg

EXPERIMENTO = Path(__file__).resolve().parents[1]
LEDGER = EXPERIMENTO / "ledger"
DOCS = EXPERIMENTO / "docs"
N_SEMILLAS = 10
MES = 201910

# Brazos de docs/diseno.md § Brazos, en orden de lectura; el control primero.
HIPOTESIS = {
    "H1": ("Submuestreo uniforme del train", ["U0.5", "U0.25", "U0.1", "U0.05"]),
    "H2": ("Muestrear dentro de LightGBM", ["B0.5", "B0.25", "B0.1", "GOSS"]),
    "H3": ("Optimizar sobre una muestra, entrenar con todo", ["H3-0.25", "H3-0.1"]),
}
BRAZOS = [b for _, bs in HIPOTESIS.values() for b in bs]
COLOR = {"C": "#555555", "H1": "#2a6fb0", "H2": "#c4501b", "H3": "#2e8b57"}
HIP_DE = {b: h for h, (_, bs) in HIPOTESIS.items() for b in bs}
A_VALE = 2.0  # hipotesis.md § Respuesta: vale la pena si no pierde y A ≥ 2


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

def cargar(ledger: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    res = pd.read_csv(ledger / "resultados.csv") if (ledger / "resultados.csv").exists() else pd.DataFrame()
    ap = pd.read_csv(ledger / "apareado.csv") if (ledger / "apareado.csv").exists() else pd.DataFrame()
    fin = res[res["etapa"] == "final"] if not res.empty else pd.DataFrame(columns=["brazo"])
    return fin, ap.set_index("brazo") if not ap.empty else ap


def estado(brazo: str, fin: pd.DataFrame) -> tuple[int, bool]:
    n = int((fin["brazo"] == brazo).sum())
    return n, n >= N_SEMILLAS


def fila(ap: pd.DataFrame, brazo: str) -> pd.Series | None:
    return ap.loc[brazo] if not ap.empty and brazo in ap.index else None


def veredicto(ap: pd.DataFrame, fin: pd.DataFrame, brazo: str) -> str:
    n, completo = estado(brazo, fin)
    r = fila(ap, brazo)
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


def fig_tiempo_ganancia(ap: pd.DataFrame, figuras: Path | None) -> str:
    if ap.empty:
        return "<p class='pend'>pendiente: no hay apareado.csv (falta el control)</p>"
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    gc, tc = ap["g_control"].iloc[0], ap["tiempo_total_control_s"].iloc[0]
    ax.scatter([tc], [gc / 1e6], s=90, color=COLOR["C"], marker="s", zorder=3, label="control")
    for h in HIPOTESIS:
        sub = ap[ap.index.isin(HIPOTESIS[h][1])]
        if sub.empty:
            continue
        g = (sub["g_control"] + sub["delta_g_media"]) / 1e6
        ax.errorbar(sub["tiempo_total_s"], g, yerr=[(sub["delta_g_media"] - sub["delta_g_ic_inf"]) / 1e6,
                                                     (sub["delta_g_ic_sup"] - sub["delta_g_media"]) / 1e6],
                    fmt="o", color=COLOR[h], capsize=3, label=h, zorder=2)
        for b, x, y in zip(sub.index, sub["tiempo_total_s"], g):
            ax.annotate(b, (x, y), textcoords="offset points", xytext=(5, 4), fontsize=8, color=COLOR[h])
    ax.axhline((gc - ap["delta_g_margen"].iloc[0]) / 1e6, color=COLOR["C"], ls=":", lw=1, label="control − δ")
    ax.set_xscale("log")
    ax.set_xlabel("tiempo del pipeline T (s, escala log)")
    ax.set_ylabel(f"ganancia media en {MES} al corte N* (M$)")
    ax.set_title("Tiempo contra ganancia (barras: IC 95% de Δ apareado)")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, fontsize=8)
    return png(fig, "tiempo_vs_ganancia", figuras)


def banda(fin: pd.DataFrame, brazo: str, ledger: Path) -> pd.DataFrame | None:
    rutas = fin.loc[fin["brazo"] == brazo, f"curva_{MES}"]
    if rutas.empty:
        return None
    m = pd.concat([lg.leer_curva(ledger, r).set_index("envios")["ganancia"] for r in rutas], axis=1)
    return pd.DataFrame({"min": m.min(axis=1), "mediana": m.median(axis=1), "max": m.max(axis=1)})


def fig_bandas(h: str, fin: pd.DataFrame, ap: pd.DataFrame, ledger: Path, figuras: Path | None) -> str:
    brazos = [b for b in HIPOTESIS[h][1] if estado(b, fin)[0]]
    bc = banda(fin, lg.CONTROL, ledger)
    if bc is None or not brazos:
        return "<p class='pend'>pendiente: faltan curvas del control o de los brazos</p>"
    n = len(brazos)
    fig, axs = plt.subplots(1, n, figsize=(3.6 * n, 3.4), sharey=True, squeeze=False)
    n_est = int(ap["n_estrella"].iloc[0]) if not ap.empty else None
    for ax, b in zip(axs[0], brazos):
        for nombre, color, bd in (("C", COLOR["C"], bc), (b, COLOR[h], banda(fin, b, ledger))):
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


def tabla_brazos(fin: pd.DataFrame, ap: pd.DataFrame) -> str:
    cab = ("brazo", "hipótesis", "semillas", "G media (M$)", "Δ media (M$)", "IC 95% de Δ (M$)", "semillas ganadas",
           "T (s)", "A", "veredicto", "vale la pena")
    filas = []
    if not ap.empty:
        filas.append(["C", "control", estado("C", fin)[0], _m(ap["g_control"].iloc[0]), "—", "—", "—",
                      f"{ap['tiempo_total_control_s'].iloc[0]:,.0f}", "1,00", "—", "—"])
    for b in BRAZOS:
        r, n = fila(ap, b), estado(b, fin)[0]
        if r is None:
            filas.append([b, HIP_DE[b], n] + ["pendiente"] * 8)
            continue
        v = veredicto(ap, fin, b)
        vale = "sí" if v in ("no pierde", "gana") and r["aceleracion"] >= A_VALE else "no"
        filas.append([b, HIP_DE[b], int(r["n_semillas"]), _m(r["g_control"] + r["delta_g_media"]),
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


def tiempo_igual(fin: pd.DataFrame, ap: pd.DataFrame) -> str:
    """K = semillas del brazo que entran en T(control): (T_C − T_opt) / T_final, con T_final medio del brazo."""
    intro = ("<p>Se le da a cada brazo el tiempo del control: después de su optimización, el sobrante se gasta en K "
             "modelos finales con semillas distintas, K = ⌊(T(C) − T_opt) / T_final⌋, acotado a las "
             f"{N_SEMILLAS} semillas que hay. T_final es la media de <code>tiempo_entrenamiento_s</code> del brazo y "
             "T_opt = T − T_final.</p>")
    if ap.empty or not estado(lg.CONTROL, fin)[1]:
        return intro + "<p class='pend'>pendiente: el control no tiene sus 10 semillas</p>"
    tc = ap["tiempo_total_control_s"].iloc[0]
    filas = []
    for b in BRAZOS:
        r = fila(ap, b)
        if r is None or not estado(b, fin)[1]:
            filas.append([b, "pendiente", "pendiente", "pendiente", "pendiente"])
            continue
        t_fin = fin.loc[fin["brazo"] == b, "tiempo_entrenamiento_s"].mean()
        t_opt = r["tiempo_total_s"] - t_fin
        k = max(0, math.floor((tc - t_opt) / t_fin))
        filas.append([b, f"{t_opt:,.0f}", f"{t_fin:,.1f}", f"{k:,}" + (f" (se usan {N_SEMILLAS})" if k > N_SEMILLAS
                                                                       else ""),
                      "pendiente: el ledger guarda curvas, no predicciones; el ensamble no se puede armar"])
    return intro + html_tabla(("brazo", "T_opt (s)", "T_final (s)", "K", f"G del ensamble en {MES}"), filas)


def seccion_hipotesis(h: str, md_h: str, fin: pd.DataFrame, ap: pd.DataFrame, ledger: Path,
                      figuras: Path | None) -> str:
    titulo, brazos = HIPOTESIS[h]
    filas = []
    for b in brazos:
        r = fila(ap, b)
        filas.append([b, veredicto(ap, fin, b)] + ([f"{_m(r['delta_g_media'])}",
                      f"[{_m(r['delta_g_ic_inf'])}, {_m(r['delta_g_ic_sup'])}]", f"{r['aceleracion']:.2f}"]
                                                  if r is not None else ["pendiente"] * 3))
    return (f"<section><h2>{h} — {html.escape(titulo)}</h2>"
            f"<details open><summary>Predicción y regla (de <code>docs/hipotesis.md</code>)</summary>"
            f"{markdown(md_h, 1)}</details>"
            + html_tabla(("brazo", "veredicto", "Δ media (M$)", "IC 95% (M$)", "A"), filas)
            + fig_bandas(h, fin, ap, ledger, figuras) + "</section>")


def commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                              cwd=EXPERIMENTO, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "desconocido"


CSS = """body{font-family:system-ui,sans-serif;max-width:1100px;margin:2em auto;padding:0 1em;color:#222;line-height:1.45}
table{border-collapse:collapse;margin:1em 0;font-size:.9em}th,td{border:1px solid #ccc;padding:.25em .5em;text-align:left}
th{background:#f3f3f3}td.pierde{background:#f8d7d0}td.ok{background:#d6ecd9}td.ind{background:#fbefc8}
.pend{color:#888;font-style:italic}img{max-width:100%}code{background:#f3f3f3;padding:0 .2em}
details{margin:.5em 0}summary{cursor:pointer;font-weight:600}footer{margin-top:3em;color:#666;font-size:.85em}"""


def generar(ledger: Path = LEDGER, figuras: Path | None = None) -> str:
    fin, ap = cargar(ledger)
    hip = secciones((DOCS / "hipotesis.md").read_text())
    dis = secciones((DOCS / "diseno.md").read_text())
    intro = (markdown("## Pregunta\n" + seccion(hip, "Pregunta"))
             + markdown("## Control\n" + seccion(hip, "Control"))
             + markdown("## Brazos\n" + seccion(dis, "Brazos"))
             + markdown("## Métricas y regla de decisión\n" + seccion(hip, "Métricas")))
    n_est = f"N* = {int(ap['n_estrella'].iloc[0]):,} envíos (de 201908); δ = {_m(ap['delta_g_margen'].iloc[0])} M$" \
        if not ap.empty else "N* pendiente"
    completos = sum(estado(b, fin)[1] for b in ["C", *BRAZOS])
    cuerpo = (
        "<h1>Sampling_1 — velocidad contra ganancia</h1>"
        f"<section>{intro}</section>"
        f"<section><h2>Todos los brazos contra el control</h2><p>{html.escape(n_est)}. Vale la pena: no pierde y "
        f"A ≥ {A_VALE:g}.</p>{tabla_brazos(fin, ap)}{fig_tiempo_ganancia(ap, figuras)}</section>"
        + "".join(seccion_hipotesis(h, seccion(hip, h + " "), fin, ap, ledger, figuras) for h in HIPOTESIS)
        + f"<section><h2>Comparación a tiempo igual</h2>{tiempo_igual(fin, ap)}</section>"
        + markdown("## Limitaciones previstas\n" + seccion(hip, "Limitaciones"))
        + f"<footer>Generado {datetime.now():%Y-%m-%d %H:%M} · commit {commit()} · ledger: {len(fin)} corridas "
          f"finales, {completos}/{len(BRAZOS) + 1} brazos con {N_SEMILLAS} semillas</footer>"
    )
    return (f"<!doctype html><html lang='es'><head><meta charset='utf-8'><title>Sampling_1 — reporte</title>"
            f"<style>{CSS}</style></head><body>{cuerpo}</body></html>\n")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--ledger", type=Path, default=LEDGER)
    p.add_argument("--salida", type=Path, default=EXPERIMENTO / "informe" / "reporte.html")
    p.add_argument("--figuras", type=Path, help="además guarda las figuras como PNG en este directorio")
    a = p.parse_args()
    a.salida.parent.mkdir(parents=True, exist_ok=True)
    a.salida.write_text(generar(a.ledger, a.figuras))
    print(a.salida)


if __name__ == "__main__":
    main()
