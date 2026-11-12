"""Genera `experimentos/<exp>/informe/reporte.html` desde los ledgers y los documentos.

    python -m comun.reporte --experimento h1 [--salida HTML] [--figuras DIR]
    python -m comun.reporte --todos

Un reporte por experimento. Para `control`: su sección de `docs/hipotesis.md` y el estado de C. Para cada `hN`: su
hipótesis, la tabla de sus variantes contra el control y las bandas de curvas. Para `sampling_1`: todas las variantes de
todas las hipótesis registradas en `comun/variantes.py`, tiempo contra ganancia, tiempo igual y enlaces a los demás.
Lee `resultados.csv`, `apareado.csv` y las curvas de los ledgers de `experimentos/*/` (los finales de C salen de
`control`). Una única página del sitio Jekyll (encabezado YAML y cuerpo HTML, sin `<html>`, `<head>` ni `<style>`; estilos en
`_sass/custom/custom.scss`) con las figuras embebidas como SVG en línea (texto como texto, salida determinista). Se ve con
`scripts/sitio.sh serve`. Las variantes sin datos salen como pendientes; ningún número se escribe a mano. Con `--figuras`
además guarda cada figura como PNG a 200 dpi (para el video y los `informe.md`).
"""

from __future__ import annotations

import argparse
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
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd

from comun import variantes as reg
from comun import ledger as lg
from comun import rutas
from comun import baseline as bl
from comun.baseline import SEMILLAS_FINALES
from comun.ganancia import aporte, ganancia

N_SEMILLAS = len(SEMILLAS_FINALES)  # 20 en la ronda vigente (D5)
#: Ronda que lee el reporte (`meses_final`); la vigente salvo que se pida otra.
VENTANA = bl.VENTANA_FINAL
MES = 201910
SIN_REPORTE = {"C", "C-rep"}  # variantes del control: no tienen Δ, van en la fila C
PALETA = ["#2a6fb0", "#c4501b", "#2e8b57", "#8e5ea2", "#b8860b", "#c0392b"]
COLOR_C = "#555555"
A_VALE = 2.0  # hipotesis.md § Respuesta: vale la pena si no pierde y A ≥ 2
ANCHO = 12.0  # pulgadas: las figuras ocupan el ancho de la página; más ancho que alto para que el texto no crezca
#: Marcas por veredicto: los tonos de `custom.scss` (td.pierde, td.ok, td.ind), más saturados (D3).
COLOR_VEREDICTO = {"pierde": "#c0392b", "ok": "#2e8b57", "ind": "#b8860b", "pend": "#999999", "": "#999999"}
NOMBRE_VEREDICTO = {"ok": "no pierde", "pierde": "pierde", "ind": "indeterminado", "pend": "pendiente"}


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


def _ronda(resultados: pd.DataFrame) -> pd.DataFrame:
    """Los finales de la ronda vigente (`baseline.VENTANA_FINAL`): las tablas no mezclan rondas (D9)."""
    return resultados[(resultados["etapa"] == "final") & (resultados["meses_final"] == VENTANA)]


def cargar(exps: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(finales de los ledgers `exps`, apareado de todos los dueños de variantes). Las rutas de curvas y predicciones
    salen absolutas."""
    finales = []
    for e in exps:
        f = rutas.ledger(e) / "resultados.csv"
        if f.exists():
            r = lg.leer_csv(f)
            finales.append(_absolutas(_ronda(r), rutas.ledger(e)))
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
            finales.append(_absolutas(_ronda(r), led))
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

plt.rcParams.update({"svg.hashsalt": "sampling_1", "svg.fonttype": "none"})


def figura(fig, nombre: str, figuras: Path | None, ajustar: bool = True) -> str:
    """SVG en línea (sin declaración XML ni `<style>`, que el sitio no admite) y, con `figuras`, PNG a 200 dpi.
    `ajustar=False` deja el layout que ya fijó la figura (p. ej. con lugar para una leyenda abajo)."""
    if ajustar:
        fig.tight_layout()
    if figuras:
        figuras.mkdir(parents=True, exist_ok=True)
        fig.savefig(figuras / f"{nombre}.png", dpi=200, metadata={"Software": None})
    buf = io.StringIO()
    fig.savefig(buf, format="svg", metadata={"Date": None, "Creator": None})
    plt.close(fig)
    svg = re.sub(r"<style[^>]*>.*?</style>", "", buf.getvalue()[buf.getvalue().index("<svg"):], flags=re.S)
    return f'<figure class="fig" id="fig-{nombre}" aria-label="{nombre}">{svg}</figure>'


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
    return figura(fig, "tiempo_vs_ganancia", figuras)


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
    return figura(fig, f"bandas_{h}", figuras)


# --- tablas ---

def _m(x: float) -> str:
    return f"{x / 1e6:,.2f}"


def _a(x: float) -> str:
    return f"{x:+.4f}"


def _auc_ic(r) -> str:
    """ΔAUC en 201910 con su IC 95%; `pendiente` si la tabla no lo trae (ledger de una ronda anterior)."""
    if r is None or pd.isna(r.get("delta_auc_media", float("nan"))) or pd.isna(r.get("delta_auc_ic_inf", float("nan"))):
        return "pendiente"
    return f"{_a(r['delta_auc_media'])} [{_a(r['delta_auc_ic_inf'])}; {_a(r['delta_auc_ic_sup'])}]"


def _auc(r) -> tuple[float, float, float] | None:
    """ΔAUC con su IC como números (lo mismo que `_auc_ic`), o None."""
    if _auc_ic(r) == "pendiente":
        return None
    return float(r["delta_auc_media"]), float(r["delta_auc_ic_inf"]), float(r["delta_auc_ic_sup"])


def tabla_variantes(ctx: Contexto, fin: pd.DataFrame, ap: pd.DataFrame) -> str:
    cab = ("variante", "hipótesis", "semillas", "G media (M$)", "Δ [IC 95%] (M$)", "semillas ganadas",
           "ΔAUC [IC 95%]", "T (s)", "A", "veredicto", "vale la pena")
    filas, veredictos, deltas, aes = [], [], [], []
    if not ap.empty:
        filas.append(["C", "control", estado("C", fin)[0], _m(ap["g_control"].iloc[0]), "—", "—", "—",
                      f"{ap['tiempo_total_control_s'].iloc[0]:,.0f}", "1,00", "—", "—"])
        veredictos, deltas, aes = [""], [None], [None]
    for b in ctx.variantes:
        r, n = fila(ap, b), estado(b, fin)[0]
        if r is None:
            filas.append([b, ctx.hip_de[b], n] + ["pendiente"] * 8)
            veredictos, deltas, aes = veredictos + ["pendiente"], deltas + [None], aes + [None]
            continue
        v = veredicto(ap, fin, b)
        vale = "sí" if v in ("no pierde", "gana") and r["aceleracion"] >= A_VALE else "no"
        filas.append([b, ctx.hip_de[b], int(r["n_semillas"]), _m(r["g_control"] + r["delta_g_media"]),
                      celda_ic((r["delta_g_media"], r["delta_g_ic_inf"], r["delta_g_ic_sup"])),
                      f"{int(r['semillas_ganadas'])}/{int(r['n_semillas'])}", celda_ic(_auc(r), _a),
                      f"{r['tiempo_total_s']:,.0f}", celda(f"{r['aceleracion']:.2f}"), celda_veredicto(v),
                      vale if not v.startswith("pendiente") else "pendiente"])
        veredictos, deltas, aes = veredictos + [v], deltas + [r["delta_g_media"]], aes + [r["aceleracion"]]
    marcar_mejores(filas, veredictos, {4: deltas, 8: aes})
    return html_tabla(cab, filas)


# --- celdas de las tablas del HTML (D5, D8): las reglas acá, los colores en `_sass/custom/custom.scss` ---

def clase_veredicto(v) -> str:
    """`ok`, `pierde`, `ind`, `pend` o "" (no es un veredicto, o es «no cambia» de una diferencia entre variantes)."""
    v = str(v)
    return {"pierde": "pierde", "no pierde": "ok", "gana": "ok", "indeterminado": "ind", "mejora": "ok",
            "empeora": "pierde"}.get(
        v, "pend" if v.startswith("pendiente") else "")


def celda(v: str, ic: str | None = None, clases: str = "", barra: tuple | None = None, nota: str | None = None,
          pill: bool = False) -> dict:
    """Celda estructurada de `html_tabla`: valor, IC debajo, clases del `td`, barra del IC, nota al pie, etiqueta."""
    return {"v": v, "ic": ic, "clases": clases, "barra": barra, "nota": nota, "pill": pill}


def celda_ic(t: tuple | None, fmt=_m) -> dict | str:
    """Cifra con su IC debajo y la barra del IC; `sig-pos`/`sig-neg` si el IC excluye 0."""
    if t is None:
        return "pendiente"
    m, lo, hi = (float(x) for x in t[:3])
    return celda(fmt(m), f"[{fmt(lo)}; {fmt(hi)}]", "sig-pos" if lo > 0 else "sig-neg" if hi < 0 else "", (lo, hi))


def celda_veredicto(v) -> dict:
    return celda(str(v), clases=clase_veredicto(v), pill=True)


def marcar_mejores(filas: list[list], veredictos: list, columnas: dict[int, list]) -> None:
    """`mejor` en la celda de mayor valor de cada columna entre las filas que no pierden; una sola (la primera si empatan)."""
    for j, valores in columnas.items():
        cands = [(v, -i) for i, v in enumerate(valores) if v is not None and clase_veredicto(veredictos[i]) == "ok"]
        if cands:
            c = filas[-max(cands)[1]][j]
            if isinstance(c, dict):
                c["clases"] = (c["clases"] + " mejor").strip()


def html_tabla(cab, filas, notas: dict[str, str] | None = None) -> str:
    """Tabla envuelta en `.table-wrapper` (se desplaza sola en pantallas angostas). Cada celda es texto (si es un
    veredicto lleva td.pierde/ok/ind/pend) o un dict de `celda()`. Las barras de IC de una columna comparten escala, que
    siempre incluye el 0. Debajo, las `notas` al pie que alguna celda usa."""
    escala = {}
    for j in range(len(cab)):
        bs = [f[j]["barra"] for f in filas if isinstance(f[j], dict) and f[j]["barra"]]
        if bs:
            lo, hi = min(0.0, *(b[0] for b in bs)), max(0.0, *(b[1] for b in bs))
            escala[j] = (lo, (hi - lo) or 1.0)
    usadas = set()

    def td(c, j):
        if not isinstance(c, dict):
            c = str(c)
            clase = clase_veredicto(c)
            return f"<td class='{clase}'>{html.escape(c)}</td>" if clase else f"<td>{html.escape(c)}</td>"
        v = html.escape(c["v"])
        if c["nota"]:
            usadas.add(c["nota"])
            v += f"<sup>{c['nota']}</sup>"
        if c["pill"]:
            return f"<td><span class='pill {c['clases']}'>{v}</span></td>"
        partes = [f"<span class='v'>{v}</span>"]
        if c["ic"]:
            partes.append(f"<span class='ic'>{html.escape(c['ic'])}</span>")
        if c["barra"]:
            lo, ancho = escala[j]
            pct = lambda x: f"{100 * (x - lo) / ancho:.1f}%"
            partes.append(f"<span class='icbar' style='--l:{pct(c['barra'][0])};--r:{pct(c['barra'][1])};--z:{pct(0.0)}'>"
                          "</span>")
        return (f"<td class='{c['clases']}'>" if c["clases"] else "<td>") + "".join(partes) + "</td>"

    cuerpo = "".join("<tr>" + "".join(td(c, j) for j, c in enumerate(f)) + "</tr>" for f in filas)
    pie = "".join(f"<p class='nota'><sup>{k}</sup> {html.escape(notas[k])}</p>" for k in sorted(usadas)) if notas else ""
    return ("<div class='table-wrapper'><table><tr>" + "".join(f"<th>{html.escape(c)}</th>" for c in cab) + "</tr>"
            + cuerpo + "</table></div>" + pie)


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


def tiempo_igual(ctx: Contexto, fin: pd.DataFrame, ap: pd.DataFrame) -> str:
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
            + "<p>El gráfico de tiempo igual, con los intervalos de réplicas y de bootstrap, está en el bloque A.</p>")


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
    out = {"variante": b, "hipotesis": ctx.hip_de[b], "d0": None, "dR": None, "G": None, "T": None, "A": None, "dauc": "pendiente",
           "auc": None, "ti_rep": ti_rep, "ti_boot": ti_boot, "k0": k0, "nota": ""}
    if r is not None:
        out.update(G=float(r["g_control"] + r["delta_g_media"]), T=float(r["tiempo_total_s"]), A=float(r["aceleracion"]),
                   d0=(float(r["delta_g_media"]), float(r["delta_g_ic_inf"]), float(r["delta_g_ic_sup"])))
    if r is not None:
        out["dauc"], out["auc"] = _auc_ic(r) + " (réplica 0)", _auc(r)
    if con_rep:
        if pd.notna(rr.get("delta_auc_media", float("nan"))):
            out["dauc"], out["auc"] = _auc_ic(rr) + f" (R={int(rr['n_replicas'])})", _auc(rr)
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
    vacio = {"filas": [], "rep": pd.DataFrame(), "g_c1": None, "g_c10": None, "ti": {}, "g_rep": {}}
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
    # referencia de las filas con réplicas: Ḡ_C media entre réplicas y T_C mediana (la misma que usa su A)
    c_rep = rep.loc[lg.CONTROL] if lg.CONTROL in rep.index and pd.notna(rep.loc[lg.CONTROL].get("g_media_replicas")) else None
    t_cr = next((f["ti_rep"]["T_c"] for f in filas if f["dR"] and f["ti_rep"]), None)
    # G media de cada réplica (la que promedia `replicas.csv`), para el gráfico de réplicas
    g_rep = {}
    if len(finr) and "g" in finr:
        for v, s in finr.groupby(["variante", "replica_opt"])["g"].mean().groupby(level=0):
            if len(s) >= 2:
                g_rep[v] = [float(x) for x in s.to_numpy()]
    return {"filas": filas, "rep": rep, "g_c1": g_c1, "g_c10": g_c10, "n_est": n_est,
            "g_cR": None if c_rep is None else float(c_rep["g_media_replicas"]),
            "n_cR": None if c_rep is None else int(c_rep["n_replicas"]), "t_cR": t_cr,
            "delta": float(ap["delta_g_margen"].iloc[0]), "g_c0": float(ap["g_control"].iloc[0]),
            "t_c0": float(ap["tiempo_total_control_s"].iloc[0]), "g_rep": g_rep}


AVISO_A = ("Ḡ, T y A salen de la réplica 0 en las variantes sin réplicas; en las marcadas (R=n), Ḡ es la media entre "
           "réplicas, T la mediana entre réplicas y A = T_C / T con T_C también mediana entre réplicas, así que se comparan "
           "con Ḡ_C con réplicas y no con Ḡ_C de la réplica 0.")


def referencia_control(a: dict) -> str:
    txt = (f"Final entrenado con {VENTANA}, {N_SEMILLAS} semillas por réplica; N* = {a['n_est']:,} envíos; "
           f"Ḡ_C (réplica 0) = {_m(a['g_c1'])} M$")
    if a.get("g_cR") is not None:
        txt += f"; Ḡ_C con réplicas = {_m(a['g_cR'])} M$ (R={a['n_cR']})"
    if a["g_c10"] is not None:
        txt += f"; ensamble de {N_SEMILLAS} semillas del control = {_m(a['g_c10'])} M$"
    return txt + "."


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
    g = (_m(f["G"]) + (f" (R={f['dR'][3]})" if f["dR"] else "")) if f["G"] is not None else "pendiente"
    return [f["variante"], f["hipotesis"], g, _ic_txt(f["d0"]), dR, f["dauc"],
            f"{f['T']:,.0f}" if f["T"] is not None else "pendiente", f"{f['A']:.2f}" if f["A"] is not None else "pendiente",
            ti_rep, ti_boot, f"{f['veredicto']} ({f['fuente']})"]


CAB_A = ("variante", "hipótesis", "Ḡ (M$)", "Δ réplica 0 [IC] (M$)", "Δ con réplicas [IC] (M$)", "ΔAUC en 201910 [IC]", "T mediana (s)", "A",
         "tiempo igual, réplicas [IC t] (M$)", "tiempo igual, bootstrap de clientes [IC] (M$)", "veredicto (fuente)")


def pares_replicas(rep: pd.DataFrame) -> list[list[str]]:
    """Filas `a - b` de `replicas.csv`: apareadas por réplica y semilla (IC t) o sin aparear (IC de Welch)."""
    return [[v, _ic_txt((r["delta_g_media"], r["delta_g_ic_inf"], r["delta_g_ic_sup"])), f"{int(r['n_replicas'])}",
             "Welch, sin aparear" if str(r.get("nota", "")).startswith("sin aparear") else "t, apareado",
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
CAB_PARES = ("diferencia", "Δ [IC entre réplicas] (M$)", "réplicas", "IC", "veredicto")
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


def lista_b(b: list[dict]) -> str:
    """Bloque B de `tabla_resultados.md`: un `### carpeta` por exploratorio con sus campos en viñetas."""
    if not b:
        return "No hay exploratorios declarados.\n"
    out = []
    for f in b:
        out += [f"### {f['carpeta']}\n", f"- **Autor:** {f['autor']}", f"- **Pregunta:** {f['pregunta']}",
                f"- **Protocolo:** {f['protocolo']}", "- **Cifras principales:**", *[f"  - {c}" for c in f["cifras"]],
                f"- **Advertencia:** {f['advertencia']}\n"]
    return "\n".join(out)


def markdown_resultados(ctx: Contexto, a: dict, b: list[dict]) -> str:
    """`informe/tabla_resultados.md`: las tablas que copia el informe, sin fecha ni cifras escritas a mano."""
    if not a["filas"]:
        return "# Resultados\n\npendiente: el control no tiene sus 10 semillas.\n"
    partes = ["# Resultados de sampling_1\n",
              "Generado por `python -m comun.reporte --experimento sampling_1`; no editar a mano.\n",
              referencia_control(a) + "\n",
              "## Bloque A: mismo protocolo\n", AVISO_A + "\n", tabla_md(CAB_A, [celdas_bloque_a(f) for f in a["filas"]])]
    notas = [f"- `{f['variante']}`: {f['nota']}" for f in a["filas"] if f["nota"]]
    if notas:
        partes += ["Notas:\n", "\n".join(notas) + "\n"]
    if len(a["rep"]):
        partes += ["### Varianza entre réplicas y entre semillas\n", tabla_md(CAB_VAR, varianza(a["rep"], ctx))]
        pares = pares_replicas(a["rep"])
        if pares:
            partes += ["### Diferencias entre variantes\n", tabla_md(CAB_PARES, pares)]
    partes += ["## Bloque B: exploratorios\n", AVISO_B + "\n", lista_b(b)]
    return "\n".join(partes)


# --- figuras del reporte conjunto (`reporte-graficos-y-ancho` D2–D4): todas leen `a` de `calcular_bloque_a` ---

def delta(f: dict) -> tuple[float, float, float] | None:
    """Δ con su IC que decide el veredicto de la fila: el de réplicas si existe, si no el de la réplica 0."""
    return f["dR"][:3] if f["dR"] else f["d0"]


def _etiqueta(f: dict) -> str:
    return f"{f['variante']} ({f['hipotesis']})"


def _ejes(*axs) -> None:
    for ax in axs:
        ax.spines[["top", "right"]].set_visible(False)


def _filas_por_variante(ax, filas: list[dict], etiquetas: list[str], *otros) -> None:
    """Una fila por variante, de arriba hacia abajo, con una línea fina entre hipótesis."""
    ax.set_yticks(range(len(filas)), etiquetas, fontsize=8)
    ax.invert_yaxis()
    for i in range(1, len(filas)):
        if filas[i]["hipotesis"] != filas[i - 1]["hipotesis"]:
            for x in (ax, *otros):
                x.axhline(i - 0.5, color="#dddddd", lw=0.8)


def _marcas_veredicto(clases: list[str]) -> tuple[list, list[str]]:
    usadas = [c for c in ("ok", "ind", "pierde", "pend") if c in clases]
    return ([Line2D([], [], color=COLOR_VEREDICTO[c], marker="o", ls="") for c in usadas],
            [NOMBRE_VEREDICTO[c] for c in usadas])


def fig_tradeoff(ctx: Contexto, a: dict, figuras: Path | None, nombre: str = "tradeoff") -> str:
    """A: Δ con su IC por veredicto a la izquierda y la aceleración A a la derecha, una fila por variante (D3)."""
    filas = [f for f in a["filas"] if f["variante"] in ctx.variantes and delta(f) is not None]
    if not filas:
        return "<p class='pend'>pendiente: ninguna variante tiene Δ contra el control</p>"
    fig, (izq, der) = plt.subplots(1, 2, figsize=(ANCHO, 0.3 * len(filas) + 1.8), sharey=True,
                                   gridspec_kw={"width_ratios": [3, 2]})
    clases = [clase_veredicto(f["veredicto"]) for f in filas]
    for i, (f, c) in enumerate(zip(filas, clases)):
        d, lo, hi = (x / 1e6 for x in delta(f))
        izq.errorbar([d], [i], xerr=[[d - lo], [hi - d]], fmt="o", ms=4, capsize=2, color=COLOR_VEREDICTO[c])
        if f["A"] is not None:
            der.barh([i], [f["A"]], height=0.6, color=COLOR_VEREDICTO[c])
    izq.axvline(0, color=COLOR_C, lw=0.8)
    izq.axvline(-a["delta"] / 1e6, color=COLOR_C, ls=":", lw=1)
    der.axvline(A_VALE, color=COLOR_C, ls="--", lw=1)
    der.text(A_VALE, 1.0, f" A = {A_VALE:g}", transform=der.get_xaxis_transform(), fontsize=8, color=COLOR_C, va="bottom")
    _filas_por_variante(izq, filas, [_etiqueta(f) for f in filas], der)
    marcas, nombres = _marcas_veredicto(clases)
    izq.legend(marcas + [Line2D([], [], color=COLOR_C, ls=":", lw=1)], nombres + ["−δ"], frameon=False, fontsize=8,
               loc="lower left")
    izq.set_xlabel("Δ contra el control (M$), con su IC 95%")
    der.set_xlabel("aceleración A = T(C) / T")
    fig.suptitle("Tradeoff por variante: Δ con réplicas si las hay, si no de la réplica 0", fontsize=10)
    _ejes(izq, der)
    return figura(fig, nombre, figuras)


MARCAS = "osD^v<>p"


def fig_fraccion(ctx: Contexto, a: dict, figuras: Path | None) -> str:
    """B: Δ contra la fracción de muestra (`Variante.tasa`), una línea por `Variante.metodo` con dos tasas o más."""
    por: dict[str, list[tuple]] = {}
    for f in a["filas"]:
        v, d = reg.VARIANTES.get(f["variante"]), delta(f)
        if v is not None and d is not None:
            por.setdefault(v.metodo, []).append((v.tasa, *d))
    familias = {m: sorted(p) for m, p in por.items() if len({t for t, *_ in p}) >= 2}
    if not familias:
        return "<p class='pend'>pendiente: ninguna familia de variantes tiene dos fracciones con datos</p>"
    fig, ax = plt.subplots(figsize=(ANCHO, 4.5))
    k = len(familias)
    for j, (m, p) in enumerate(familias.items()):
        t = np.array([x[0] for x in p]) * (1 + 0.04 * (j - (k - 1) / 2))  # corrimiento para que no se pisen los IC
        d, lo, hi = (np.array([x[i] for x in p]) / 1e6 for i in (1, 2, 3))
        ax.errorbar(t, d, yerr=[d - lo, hi - d], fmt="-" + MARCAS[j % len(MARCAS)], ms=5, capsize=2, lw=1.2,
                    color=PALETA[j % len(PALETA)], label=m)
    ax.axhline(0, color=COLOR_C, lw=0.8)
    ax.axhline(-a["delta"] / 1e6, color=COLOR_C, ls=":", lw=1, label="−δ")
    ax.set_xscale("log")
    tasas = sorted({x[0] for p in familias.values() for x in p})
    ax.set_xticks(tasas, [f"{t:g}" for t in tasas])
    ax.minorticks_off()
    ax.set_xlabel("fracción de la muestra (escala log; cada familia corrida un poco para que no se pisen los IC)")
    ax.set_ylabel("Δ contra el control (M$)")
    ax.set_title("Δ contra fracción de muestra, por familia de variantes", fontsize=10)
    ax.legend(frameon=False, fontsize=8, ncol=min(k + 1, 4))
    _ejes(ax)
    return figura(fig, "fraccion", figuras)


def desplazar(puntos: list[tuple[float, float]], alto: float, ancho: float) -> list[tuple[float, float]]:
    """Posición de la etiqueta de cada punto (en fracción de los ejes): empieza en su punto y, en orden de y, sube
    mientras choque con una ya puesta (a menos de `ancho` en x y de `alto` en y). Determinista (D4)."""
    pos: list = [None] * len(puntos)
    puestas: list[tuple[float, float]] = []
    for i in sorted(range(len(puntos)), key=lambda i: (puntos[i][1], puntos[i][0])):
        x, y = puntos[i]
        # el margen evita que una etiqueta corrida justo `alto` vuelva a chocar por redondeo y no avance
        while choques := [py for px, py in puestas if abs(x - px) < ancho and abs(y - py) < alto - 1e-9]:
            y = max(choques) + alto
        pos[i] = (x, y)
        puestas.append((x, y))
    return pos


def desplazar_dentro(puntos: list[tuple[float, float]], alto: float, ancho: float, tope: float = 0.97):
    """`desplazar` hacia arriba; si alguna etiqueta se sale del panel, apiladas hacia abajo (en espejo)."""
    pos = desplazar(puntos, alto, ancho)
    if max(y for _, y in pos) <= tope:
        return pos
    return [(x, 1 - y) for x, y in desplazar([(x, 1 - y) for x, y in puntos], alto, ancho)]


def fig_tiempo_ganancia_paneles(ctx: Contexto, a: dict, figuras: Path | None) -> str:
    """C: tiempo contra ganancia, un panel por hipótesis con el control en cada uno y etiquetas que no se pisan (D4)."""
    hips = {h: [f for f in a["filas"] if f["hipotesis"] == h and f["G"] is not None and f["T"] is not None]
            for h in ctx.hipotesis}
    hips = {h: fs for h, fs in hips.items() if fs}
    if not hips:
        return "<p class='pend'>pendiente: no hay apareado.csv (falta el control)</p>"
    rep, cols = a["rep"], min(len(hips), 2)
    nf = math.ceil(len(hips) / cols)
    fig, axs = plt.subplots(nf, cols, figsize=(ANCHO, 3.8 * nf + 0.6), sharex=True, sharey=True, squeeze=False)
    rango = lambda r, y: [[y - r["g_min_replicas"] / 1e6], [r["g_max_replicas"] / 1e6 - y]]
    for ax, (h, fs) in zip(axs.flat, hips.items()):
        ax.scatter([a["t_c0"]], [a["g_c0"] / 1e6], s=50, color=COLOR_C, marker="s", zorder=3)
        if a.get("g_cR") is not None and a.get("t_cR") is not None:
            y = a["g_cR"] / 1e6
            ax.errorbar([a["t_cR"]], [y], yerr=rango(rep.loc[lg.CONTROL], y), fmt="D", ms=6, mfc="white",
                        color=COLOR_C, capsize=3, zorder=3)
        ax.axhline((a["g_c0"] - a["delta"]) / 1e6, color=COLOR_C, ls=":", lw=1)
        for f in fs:
            y, c = f["G"] / 1e6, COLOR_VEREDICTO[clase_veredicto(f["veredicto"])]
            if f["dR"] and f["variante"] in rep.index:
                ax.errorbar([f["T"]], [y], yerr=rango(rep.loc[f["variante"]], y), fmt="o", ms=5, color=c, capsize=3)
            else:
                ax.scatter([f["T"]], [y], s=25, color=c, zorder=2)
        ax.set_xscale("log")
        ax.set_title(f"{h} — {ctx.hipotesis[h][0]}", fontsize=9)
        _ejes(ax)
    for ax in axs.flat[len(hips):]:
        ax.set_visible(False)
    for ax, fs in zip(axs.flat, hips.values()):
        ax.autoscale_view()
        a_fraccion = ax.transScale + ax.transLimits  # datos -> fracción de los ejes, sin depender del layout
        pts = [tuple(a_fraccion.transform((f["T"], f["G"] / 1e6))) for f in fs]
        for f, (px, py), (lx, ly) in zip(fs, pts, desplazar_dentro(pts, 0.075, 0.2)):
            der = lx > 0.8
            ax.annotate(f["variante"], (f["T"], f["G"] / 1e6), xytext=(lx - 0.02 if der else lx + 0.02, ly),
                        textcoords="axes fraction", fontsize=8, va="center", ha="right" if der else "left",
                        arrowprops=dict(arrowstyle="-", color="#aaaaaa", lw=0.6) if ly != py else None)
    for ax in axs[-1]:
        ax.set_xlabel("T del pipeline (s, escala log; mediana entre réplicas)")
    for ax in axs[:, 0]:
        ax.set_ylabel(f"Ḡ en {MES} al corte N* (M$)")
    marcas, nombres = _marcas_veredicto([clase_veredicto(f["veredicto"]) for fs in hips.values() for f in fs])
    fig.legend([Line2D([], [], color=COLOR_C, marker="s", ls=""),
                Line2D([], [], color=COLOR_C, marker="D", mfc="white", ls=""),
                Line2D([], [], color=COLOR_C, ls=":", lw=1)] + marcas,
               ["control (réplica 0)",
                f"control (media de {a['n_cR']} réplicas)" if a.get("n_cR") else "control (sin réplicas)",
                "control − δ"] + nombres,
               frameon=False, fontsize=8, loc="lower center", ncol=4 + len(marcas))
    fig.suptitle("Tiempo contra ganancia por hipótesis (barras: rango entre réplicas; sin barra: una sola réplica)",
                 fontsize=10)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    return figura(fig, "tiempo_vs_ganancia", figuras, ajustar=False)


def fig_tiempo_igual_ic(ctx: Contexto, a: dict, figuras: Path | None) -> str:
    """D: G del ensamble de K semillas − Ḡ_C, con el IC entre réplicas y el de bootstrap de clientes."""
    filas = []
    for f in a["filas"]:
        tr = f["ti_rep"]
        r = (tr["media"], tr["inf"], tr["sup"]) if tr and tr["n"] >= 2 else None
        if r or f["ti_boot"]:
            filas.append((f, r, f["ti_boot"]))
    if not filas:
        return "<p class='pend'>pendiente: ninguna variante tiene su ensamble a tiempo igual</p>"
    fig, ax = plt.subplots(figsize=(ANCHO, 0.32 * len(filas) + 1.8))
    for i, (_, r, b) in enumerate(filas):
        for t, dy, marca, color, relleno in ((r, -0.15, "o", PALETA[0], PALETA[0]), (b, 0.15, "s", PALETA[1], "white")):
            if t:
                m, lo, hi = (x / 1e6 for x in t[:3])
                ax.errorbar([m], [i + dy], xerr=[[m - lo], [hi - m]], fmt=marca, ms=4, mfc=relleno, capsize=2, color=color)
    ax.axvline(0, color=COLOR_C, lw=0.8)
    _filas_por_variante(ax, [f for f, _, _ in filas], [_etiqueta(f) for f, _, _ in filas])
    ax.legend([Line2D([], [], color=PALETA[0], marker="o", ls=""),
               Line2D([], [], color=PALETA[1], marker="s", mfc="white", ls="")],
              ["réplicas (IC t; cada réplica contra Ḡ_C de su réplica)", "bootstrap de clientes (réplica 0)"],
              frameon=False, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.06 - 1.2 / (0.32 * len(filas) + 1.8)),
              ncol=2)
    ax.set_xlabel(f"G del ensamble de K semillas en {MES} − Ḡ_C (M$)")
    ax.set_title("A tiempo igual: ensamble de K semillas de cada variante contra el control", fontsize=10)
    _ejes(ax)
    return figura(fig, "tiempo_igual", figuras)


def fig_replicas(ctx: Contexto, a: dict, figuras: Path | None) -> str:
    """E: la Ḡ de cada réplica como un punto, junto a las del control."""
    g = a.get("g_rep", {})
    filas = [f for f in a["filas"] if f["variante"] in g]
    if not len(a["rep"]) or not filas or lg.CONTROL not in g:
        return "<p class='pend'>pendiente: ninguna variante tiene réplicas</p>"
    filas = [{"variante": lg.CONTROL, "hipotesis": "control", "veredicto": ""}] + filas
    fig, ax = plt.subplots(figsize=(ANCHO, 0.32 * len(filas) + 1.8))
    for i, f in enumerate(filas):
        v = np.array(g[f["variante"]]) / 1e6
        c = COLOR_C if i == 0 else COLOR_VEREDICTO[clase_veredicto(f["veredicto"])]
        ax.scatter(v, [i] * len(v), s=16, color=c, alpha=0.6, lw=0)
        ax.scatter([v.mean()], [i], s=180, marker="|", color=c)
    ax.axvline(np.mean(g[lg.CONTROL]) / 1e6, color=COLOR_C, ls="--", lw=0.8)
    _filas_por_variante(ax, filas, [_etiqueta(f) for f in filas])
    ax.set_xlabel(f"Ḡ de cada réplica en {MES} al corte N* (M$; media de sus semillas)")
    ax.set_title("Réplicas de optimización: un punto por réplica; raya: media entre réplicas; punteada: la del control",
                 fontsize=10)
    _ejes(ax)
    return figura(fig, "replicas", figuras)


def fig_varianza(ctx: Contexto, a: dict, figuras: Path | None) -> str:
    """F: sd entre réplicas y sd entre semillas de cada variante, en barras."""
    rep = a["rep"]
    r = rep[[" - " not in v for v in rep.index]] if len(rep) else rep
    if r.empty:
        return "<p class='pend'>pendiente: ninguna variante tiene réplicas</p>"
    fig, ax = plt.subplots(figsize=(ANCHO, 0.45 * len(r) + 1.6))
    y, h = np.arange(len(r)), 0.38
    ax.barh(y - h / 2, r["sd_entre_replicas"] / 1e6, height=h, color=PALETA[0], label="sd entre réplicas (suerte de Optuna)")
    ax.barh(y + h / 2, r["sd_dentro_medio"] / 1e6, height=h, color=PALETA[1], label="sd entre semillas (media por réplica)")
    ax.set_yticks(y, list(r.index), fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("desvío estándar de G (M$)")
    ax.set_title("Varianza de la ganancia: entre réplicas y entre semillas", fontsize=10)
    ax.legend(frameon=False, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.06 - 1.2 / (0.45 * len(r) + 1.6)),
              ncol=2)
    _ejes(ax)
    return figura(fig, "varianza", figuras)


def fig_diferencias(ctx: Contexto, a: dict, figuras: Path | None) -> str:
    """G: cada diferencia entre variantes de `replicas.csv` con su IC, por veredicto."""
    rep = a["rep"]
    r = rep[[" - " in v for v in rep.index]] if len(rep) else rep
    if r.empty:
        return "<p class='pend'>pendiente: no hay diferencias entre variantes con réplicas</p>"
    fig, ax = plt.subplots(figsize=(ANCHO, 0.4 * len(r) + 1.6))
    clases = [clase_veredicto(v) for v in r["veredicto"]]
    textos = dict(zip(clases, r["veredicto"].astype(str)))  # leyenda con el veredicto de los pares (mejora, no cambia…)
    for i, ((_, f), c) in enumerate(zip(r.iterrows(), clases)):
        m, lo, hi = (f[k] / 1e6 for k in ("delta_g_media", "delta_g_ic_inf", "delta_g_ic_sup"))
        ax.errorbar([m], [i], xerr=[[m - lo], [hi - m]], fmt="o", ms=5, capsize=3, color=COLOR_VEREDICTO[c])
    ax.axvline(0, color=COLOR_C, lw=0.8)
    margen = "delta_g_margen" in r and r["delta_g_margen"].notna().any()
    if margen:
        ax.axvline(-r["delta_g_margen"].dropna().iloc[0] / 1e6, color=COLOR_C, ls=":", lw=1)
    ax.set_yticks(range(len(r)), list(r.index), fontsize=8)
    ax.invert_yaxis()
    ax.legend([Line2D([], [], color=COLOR_VEREDICTO[c], marker="o", ls="") for c in textos], list(textos.values()),
              frameon=False, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.06 - 1.2 / (0.4 * len(r) + 1.6)),
              ncol=len(textos))
    ax.set_xlabel("Δ entre variantes (M$), IC entre réplicas" + ("; punteada: −δ" if margen else ""))
    ax.set_title("Diferencias entre variantes", fontsize=10)
    _ejes(ax)
    return figura(fig, "diferencias", figuras)


# --- tablas del HTML: resumen y detalle del bloque A, pares y tarjetas del bloque B (D5, D8) ---

#: Notas al pie de las celdas `—` (ninguna celda repite una nota que vale para toda la columna).
NOTAS = {"a": "sin réplicas de optimización: Δ, A y el veredicto salen de la réplica 0 (Δ apareado por semilla).",
         "b": "no aplica: K < 2, en el tiempo del control no entra un segundo modelo final de la variante.",
         "c": "con menos réplicas que Δ: en alguna réplica K < 2."}
CAB_RESUMEN = ("variante", "hipótesis", "R", "Δ [IC 95%] (M$)", "A", "veredicto")
CAB_DETALLE = ("variante", "Ḡ (M$)", "Δ réplica 0 [IC] (M$)", "Δ con réplicas [IC] (M$)", "ΔAUC en 201910 [IC]",
               "T mediana (s)", "tiempo igual, réplicas [IC t] (M$)", "tiempo igual, bootstrap de clientes [IC] (M$)")
AVISO_A_HTML = AVISO_A.replace("en las marcadas (R=n)", "en las que tienen réplicas (columna R)")


def celdas_resumen(f: dict) -> list:
    """Fila del resumen del bloque A: variante, hipótesis, R, Δ con su IC, A y el veredicto como etiqueta."""
    return [f["variante"], f["hipotesis"], celda(str(f["dR"][3])) if f["dR"] else celda("—", nota="a"),
            celda_ic(delta(f)), celda(f"{f['A']:.2f}") if f["A"] is not None else "pendiente",
            celda_veredicto(f["veredicto"])]


def celdas_detalle(f: dict) -> list:
    """Fila del detalle plegable: lo que no está en el resumen, con `—` y nota al pie donde no aplica."""
    tr, tb, k0 = f["ti_rep"], f["ti_boot"], f["k0"]
    if tr and tr["n"] >= 2:
        ti_rep = celda_ic((tr["media"], tr["inf"], tr["sup"]))
        if tr["n"] < len(tr["filas"]):
            ti_rep["nota"] = "c"
    else:
        ti_rep = celda("—", nota="b" if tr else "a")
    ti_boot = celda_ic(tb) if tb else (celda("—", nota="b") if k0 and k0[2] < 2 else "pendiente")
    return [f["variante"], _m(f["G"]) if f["G"] is not None else "pendiente", celda_ic(f["d0"]),
            celda_ic(f["dR"][:3]) if f["dR"] else celda("—", nota="a"), celda_ic(f["auc"], _a),
            f"{f['T']:,.0f}" if f["T"] is not None else "pendiente", ti_rep, ti_boot]


def tabla_resumen(filas_a: list[dict]) -> str:
    filas = [celdas_resumen(f) for f in filas_a]
    marcar_mejores(filas, [f["veredicto"] for f in filas_a],
                   {3: [delta(f)[0] if delta(f) else None for f in filas_a], 4: [f["A"] for f in filas_a]})
    return html_tabla(CAB_RESUMEN, filas, NOTAS)


def tabla_pares(rep: pd.DataFrame) -> str:
    """Las filas de `pares_replicas` con Δ resaltado y el veredicto como etiqueta."""
    filas = [[v, celda_ic((r["delta_g_media"], r["delta_g_ic_inf"], r["delta_g_ic_sup"])), f"{int(r['n_replicas'])}",
              "Welch, sin aparear" if str(r.get("nota", "")).startswith("sin aparear") else "t, apareado",
              celda_veredicto(r["veredicto"])] for v, r in rep.iterrows() if " - " in v]
    return html_tabla(CAB_PARES, filas)


def tarjetas_b(b: list[dict]) -> str:
    """Bloque B del HTML: una tarjeta por exploratorio."""
    if not b:
        return "<p>No hay exploratorios declarados.</p>"
    e = html.escape
    tarjetas = []
    for f in b:
        cifras = "".join(f"<li class='pend'>{e(c)}</li>" if c.startswith("pendiente") else f"<li>{e(c)}</li>"
                         for c in f["cifras"])
        tarjetas.append(f"<article><h4>{e(f['carpeta'])}</h4><p class='autor'>{e(f['autor'])}</p>"
                        f"<dl><dt>Pregunta</dt><dd>{e(f['pregunta'])}</dd><dt>Protocolo</dt><dd>{e(f['protocolo'])}</dd>"
                        f"<dt>Cifras principales</dt><dd><ul>{cifras}</ul></dd>"
                        f"<dt>Advertencia</dt><dd class='advertencia'>{e(f['advertencia'])}</dd></dl></article>")
    return f"<div class='tarjetas'>{''.join(tarjetas)}</div>"


def html_resultados(ctx: Contexto, a: dict, b: list[dict], figuras: Path | None) -> str:
    """Gráficos de tradeoff, fracción, tiempo contra ganancia y tiempo igual arriba; el resumen del bloque A, su detalle
    plegado y debajo de cada tabla el gráfico que la explica."""
    if not a["filas"]:
        return "<p class='pend'>pendiente: el control no tiene sus 10 semillas</p>"
    out = ["<h3>Bloque A: mismo protocolo</h3>", f"<p>{html.escape(referencia_control(a))}</p>",
           fig_tradeoff(ctx, a, figuras), fig_tiempo_ganancia_paneles(ctx, a, figuras), fig_tiempo_igual_ic(ctx, a, figuras),
           fig_fraccion(ctx, a, figuras), f"<p>{html.escape(AVISO_A_HTML)}</p>", tabla_resumen(a["filas"]),
           "<details><summary>Detalle del bloque A</summary>"
           + html_tabla(CAB_DETALLE, [celdas_detalle(f) for f in a["filas"]], NOTAS) + "</details>",
           fig_replicas(ctx, a, figuras)]
    if len(a["rep"]):
        out += ["<h3>Varianza entre réplicas y entre semillas</h3>", html_tabla(CAB_VAR, varianza(a["rep"], ctx)),
                fig_varianza(ctx, a, figuras)]
        if pares_replicas(a["rep"]):
            out += ["<h3>Diferencias entre variantes</h3>", tabla_pares(a["rep"]), fig_diferencias(ctx, a, figuras)]
    out += ["<h3>Bloque B: exploratorios</h3>", f"<p>{html.escape(AVISO_B)}</p>", tarjetas_b(b)]
    return "".join(out)


def seccion_hipotesis(ctx: Contexto, h: str, md_h: str, fin: pd.DataFrame, ap: pd.DataFrame,
                      figuras: Path | None) -> str:
    titulo, variantes = ctx.hipotesis[h]
    filas, veredictos, deltas, aes = [], [], [], []
    for b in variantes:
        r, v = fila(ap, b), veredicto(ap, fin, b)
        d0 = None if r is None else (r["delta_g_media"], r["delta_g_ic_inf"], r["delta_g_ic_sup"])
        filas.append([b, celda_veredicto(v), celda_ic(d0), celda_ic(_auc(r), _a) if r is not None else "pendiente",
                      celda(f"{r['aceleracion']:.2f}") if r is not None else "pendiente"])
        veredictos.append(v)
        deltas.append(None if r is None else d0[0])
        aes.append(None if r is None else r["aceleracion"])
    marcar_mejores(filas, veredictos, {2: deltas, 4: aes})
    return (f"<section><h2>{h} — {html.escape(titulo)}</h2>"
            f"<details open><summary>Predicción y regla (de <code>docs/hipotesis.md</code>)</summary>"
            f"{markdown(md_h, 1)}</details>"
            + html_tabla(("variante", "veredicto", "Δ [IC 95%] (M$)", "ΔAUC [IC 95%]", "A"), filas)
            + fig_bandas(ctx, h, fin, ap, figuras) + "</section>")


def commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                              cwd=rutas.RAIZ, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "desconocido"


# Encabezado YAML mínimo: el título y la navegación los pone `_config.yml` (defaults); las reglas de veredicto
# (td.pierde, td.ok, td.ind), .pend, .pill, .ic, .icbar, .sig-*, .mejor, .tarjetas y .fig están en `_sass/custom/custom.scss`.
ENCABEZADO = "---\nrender_with_liquid: false\n---\n"


def _leer(exp: str, nombre: str) -> dict[str, str]:
    f = rutas.docs(exp) / f"{nombre}.md"
    return secciones(f.read_text()) if f.exists() else {}


def enlaces(exp: str, exps: list[str]) -> str:
    """Enlaces relativos a los reportes de los demás experimentos del registro."""
    otros = [e for e in dict.fromkeys([reg.AGREGADOR, reg.CONTROL, *exps]) if e != exp]
    items = "".join(f"<li><a href='../../{e}/informe/reporte.html'>{e}</a></li>" for e in otros)
    return f"<section><h2>Otros reportes</h2><ul>{items}</ul></section>"


def generar_con_tabla(exp: str, figuras: Path | None = None) -> tuple[str, str | None]:
    """(página Jekyll del reporte: encabezado YAML + cuerpo HTML, sin <html>, <head> ni <style>; `tabla_resultados.md` del agregador o None para los demás experimentos)."""
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
    n_est = f"Final entrenado con {VENTANA}, {N_SEMILLAS} semillas; N* = {int(ap['n_estrella'].iloc[0]):,} envíos (fijo, de la ronda anterior); δ = {_m(ap['delta_g_margen'].iloc[0])} M$" \
        if not ap.empty else "N* pendiente"
    completos = sum(estado(b, fin)[1] for b in ["C", *ctx.variantes])
    titulo = {reg.CONTROL: "Control", reg.AGREGADOR: "Sampling_1 — velocidad contra ganancia"}.get(exp, exp)
    md = None
    cuerpo = f"<h1>{html.escape(titulo)}</h1><section>{intro}</section>"
    if ctx.agregador:
        a, b = calcular_bloque_a(ctx, fin, ap), bloque_b()
        md = markdown_resultados(ctx, a, b)
        cuerpo += (f"<section><h2>Todas las variantes contra el control</h2><p>{html.escape(n_est)}. "
                   f"Vale la pena: no pierde y A ≥ {A_VALE:g}.</p>{html_resultados(ctx, a, b, figuras)}</section>")
        cuerpo += f"<section><h2>Comparación a tiempo igual</h2>{tiempo_igual(ctx, fin, ap)}</section>"
    else:
        trade = ""
        if ctx.variantes:  # el bloque A del agregador (réplicas y tiempos de todos los ledgers), filtrado a las variantes de exp
            ctx_s = Contexto(reg.AGREGADOR)
            trade = fig_tradeoff(ctx, calcular_bloque_a(ctx_s, cargar([reg.CONTROL, *ctx_s.exps])[0], ap), figuras,
                                 f"tradeoff_{exp}")
        cuerpo += (f"<section><h2>Variantes contra el control</h2><p>{html.escape(n_est)}. "
                   f"Vale la pena: no pierde y A ≥ {A_VALE:g}.</p>{trade}{tabla_variantes(ctx, fin, ap)}</section>")
        for h in ctx.hipotesis:
            cuerpo += seccion_hipotesis(ctx, h, seccion(hip, h + " "), fin, ap, figuras)
    cuerpo += markdown("## Limitaciones previstas\n" + seccion(hip, "Limitaciones"))
    cuerpo += enlaces(exp, [e for e in reg.duenos() if e != reg.CONTROL])
    cuerpo += (f"<footer>Generado {datetime.now():%Y-%m-%d %H:%M} · commit {commit()} · ledger: {len(fin)} corridas "
               f"finales (réplica 0), {completos}/{len(ctx.variantes) + 1} variantes con {N_SEMILLAS} semillas</footer>")
    return f"{ENCABEZADO}{cuerpo}\n", md


def generar(exp: str, figuras: Path | None = None) -> str:
    return generar_con_tabla(exp, figuras)[0]


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--experimento", help="carpeta de experimentos/ (control, h1, ..., sampling_1)")
    g.add_argument("--todos", action="store_true", help="un reporte por cada experimento del registro")
    p.add_argument("--salida", type=Path, help="página de salida (solo con --experimento)")
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
