"""Genera las tablas y figuras de los README de `experimentos/` desde los ledgers, en bloques entre marcadores.

    python -m comun.reporte --exp h1 [--figuras DIR]
    python -m comun.reporte --todos

En cada README, `<!-- generado:NOMBRE -->` … `<!-- /generado:NOMBRE -->` delimita un bloque que se reemplaza; el resto
del archivo no se toca (sitio-legible D4). Si falta un marcador, falla nombrando archivo y marcador antes de escribir
nada. Bloques: `hN/README.md` → `resultado`; `control/README.md` → `estado`; `sampling_1/README.md` → `mapa`, `grilla`,
`desglose`, `bloque-a`, `fraccion`, `tiempo-igual`, `semillas`; `sampling_1/anexo.md` → `bloque-a-completo`, `varianza`,
`diferencias`, `ic-rondas` (y `rondas`, de `scripts/comparar_rondas.py`); `sampling_1/exploratorios/README.md` → `bloque-b`;
`index.md` → `hallazgo-tradeoff`, `hallazgo-tiempo`, `hallazgo-ensamble` y `tarjetas`; `sitio/hipotesis/README.md` → `tarjetas`. Las figuras salen como
SVG en `experimentos/<exp>/figuras/` (con `--figuras` también PNG a 200 dpi para el video).

Un archivo sin ningún marcador se omite y `main` lo avisa. Las variantes sin datos salen como pendientes; ningún número
se escribe a mano.
"""

from __future__ import annotations

import argparse
import html
import io
import json
import math
import re
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
#: Categórica de la skill `dataviz` (references/palette.md), en su orden fijo; los colores de veredicto van aparte.
PALETA = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
COLOR_C = "#555555"
# Un color por hipótesis, el mismo en todas las figuras (D16): no depende de qué hipótesis tenga el reporte.
COLOR_HIPOTESIS = {"H1": PALETA[0], "H2": PALETA[1], "H3": PALETA[2], "H4": PALETA[3]}
A_VALE = 2.0  # hipotesis.md § Respuesta: vale la pena si no pierde y A ≥ 2
ANCHO = 9.0  # pulgadas: la figura se muestra al ancho de la columna (D6); más chico que 12 para que la letra no quede menor que la del texto al escalar
#: Marcas por veredicto: los tonos de `custom.scss` (td.pierde, td.ok, td.ind), más saturados (D3).
COLOR_VEREDICTO = {"pierde": "#c0392b", "ok": "#2e8b57", "ind": "#b8860b", "pend": "#999999", "": "#999999"}
NOMBRE_VEREDICTO = {"ok": "no pierde", "pierde": "pierde", "ind": "indeterminado", "pend": "pendiente"}


def _idea_hipotesis(e: str) -> str:
    """La línea «qué se prueba» del README de `e` (el primer párrafo después del título), o "" si no migró."""
    readme = rutas.experimento(e) / "README.md"
    m = re.search(r"\A# H\d+[^\n]*\n\n(.+?)(?:\n\n|\Z)", readme.read_text(), re.S) if readme.exists() else None
    return " ".join(m.group(1).split()) if m else ""


def _titulo_hipotesis(e: str) -> tuple[str, str]:
    """(`H1`, título) del experimento `e`, del `# H1 · título` de su README."""
    readme = rutas.experimento(e) / "README.md"
    if readme.exists() and (m := re.search(r"^# (H\d+)\s*[·—-]\s*(.*)$", readme.read_text(), re.M)):
        return m.group(1), m.group(2).strip()
    return e.upper(), e.upper()


class Contexto:
    """Qué hipótesis y variantes entran en un reporte, salido del registro de `comun/variantes.py` (no de listas a mano)."""

    def __init__(self, exp: str):
        self.exp = exp
        self.agregador = exp == reg.AGREGADOR
        self.exps = [e for e in reg.duenos() if e != reg.CONTROL] if self.agregador else \
            ([] if exp == reg.CONTROL else [exp])
        self.hipotesis: dict[str, tuple[str, list[str]]] = {}  # "H1" -> (título, variantes)
        for e in self.exps:
            nombre, titulo = _titulo_hipotesis(e)
            self.hipotesis[nombre] = (titulo or nombre,
                                      [b.nombre for b in reg.variantes_de(e) if b.nombre not in SIN_REPORTE])
        self.variantes = [b for _, bs in self.hipotesis.values() for b in bs]
        self.hip_de = {b: h for h, (_, bs) in self.hipotesis.items() for b in bs}
        self.color = {h: COLOR_HIPOTESIS.get(h, PALETA[i % len(PALETA)]) for i, h in enumerate(self.hipotesis)}


# --- datos ---

def _absolutas(fin: pd.DataFrame, exp: str) -> pd.DataFrame:
    """Rutas de curvas y predicciones absolutas, para mezclar finales de varios ledgers y leerlas igual. Las predicciones
    se buscan en `DATOS_DIR` y, si no están, en el repo (D18)."""
    fin = fin.copy()
    for col in [c for c in fin.columns if c.startswith(("curva_", "predicciones_"))]:
        ruta = rutas.prediccion if col.startswith("predicciones_") else lambda e, r: rutas.ledger(e) / r
        fin[col] = fin[col].map(lambda r: str(ruta(exp, r)) if isinstance(r, str) else r)
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
            finales.append(_absolutas(_ronda(r), e))
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
            finales.append(_absolutas(_ronda(r), e))
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

# Las figuras miden ANCHO = 12 pulgadas y se muestran a ~750 px: el texto va en 11 a 14 pt para leerse a ~10 px.
plt.rcParams.update({"svg.hashsalt": "sampling_1", "svg.fonttype": "none", "font.family": "sans-serif", "font.size": 12})


class Destino:
    """Dónde van las figuras de un README (D5): `svg_dir` junto al README y, con `png_dir`, también PNG. Los archivos se
    juntan en `archivos` y se escriben después de validar los marcadores de todos los README (nada a medias)."""

    def __init__(self, svg_dir: Path):
        self.svg_dir = svg_dir
        self.archivos: dict[Path, bytes] = {}


#: Mientras `generar_bloques` arma un README, las figuras van a archivos SVG; sin destino van en línea (hoy nadie lo usa).
DESTINO: Destino | None = None


def _titulo_figura(fig) -> str:
    if fig._suptitle is not None:
        return fig._suptitle.get_text()
    return next((ax.get_title() for ax in fig.axes if ax.get_title()), "")


def figura(fig, nombre: str, figuras: Path | None, ajustar: bool = True) -> str:
    """Con `DESTINO`: SVG como archivo (texto con fuente genérica, sin CSS de la página) y `![título](figuras/x.svg)`;
    con `figuras`, además PNG a 200 dpi. Sin `DESTINO` (no lo usa ningún llamador desde que se borró la salida vieja): SVG en línea sin declaración XML ni `<style>`.
    `ajustar=False` deja el layout que ya fijó la figura (p. ej. con lugar para una leyenda abajo)."""
    if ajustar:
        fig.tight_layout()
    titulo = _titulo_figura(fig)
    if DESTINO is not None:
        if figuras:
            png = io.BytesIO()
            fig.savefig(png, format="png", dpi=200, metadata={"Software": None})
            DESTINO.archivos[figuras / f"{nombre}.png"] = png.getvalue()
        buf = io.StringIO()
        fig.savefig(buf, format="svg", metadata={"Date": None, "Creator": None})
        plt.close(fig)
        DESTINO.archivos[DESTINO.svg_dir / f"{nombre}.svg"] = buf.getvalue().encode()
        alt = titulo.replace(chr(10), " ").replace("\\$", "$")  # en el título, «\$» evita el modo matemático
        return f"\n![{alt}](figuras/{nombre}.svg)\n"
    if figuras:
        figuras.mkdir(parents=True, exist_ok=True)
        fig.savefig(figuras / f"{nombre}.png", dpi=200, metadata={"Software": None})
    buf = io.StringIO()
    fig.savefig(buf, format="svg", metadata={"Date": None, "Creator": None})
    plt.close(fig)
    svg = re.sub(r"<style[^>]*>.*?</style>", "", buf.getvalue()[buf.getvalue().index("<svg"):], flags=re.S)
    return f'<figure class="fig" id="fig-{nombre}" aria-label="{nombre}">{svg}</figure>'


def pendiente(texto: str) -> str:
    """Un gráfico sin datos: aviso en HTML (en el Markdown del sitio es un párrafo con la clase `pend`)."""
    return f"<p class='pend'>pendiente: {texto}</p>"


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
    """Tabla del bloque `resultado` de una hipótesis (D9): sin columna «hipótesis»; la de «semillas» solo si alguna fila
    difiere (si no, una línea debajo lo dice); las semillas ganadas, con una barrita de proporción."""
    filas, veredictos, deltas, aes, semillas = [], [], [], [], []
    if not ap.empty:
        filas.append(["C", _m(ap["g_control"].iloc[0]), "—", "—", "—", f"{ap['tiempo_total_control_s'].iloc[0]:,.0f}", "1.00",
                      "—", "—"])
        semillas.append(estado("C", fin)[0])
        veredictos, deltas, aes = [""], [None], [None]
    for b in ctx.variantes:
        r, n = fila(ap, b), estado(b, fin)[0]
        if r is None:
            filas.append([b] + ["pendiente"] * 8)
            semillas.append(n)
            veredictos, deltas, aes = veredictos + ["pendiente"], deltas + [None], aes + [None]
            continue
        v = veredicto(ap, fin, b)
        vale = "sí" if v in ("no pierde", "gana") and r["aceleracion"] >= A_VALE else "no"
        ganadas, total = int(r["semillas_ganadas"]), int(r["n_semillas"])
        filas.append([b, _m(r["g_control"] + r["delta_g_media"]),
                      celda_ic((r["delta_g_media"], r["delta_g_ic_inf"], r["delta_g_ic_sup"])),
                      celda(f"{ganadas}/{total}", prop=ganadas / total if total else None), celda_ic(_auc(r), _a),
                      f"{r['tiempo_total_s']:,.0f}", celda(f"{r['aceleracion']:.2f}"), celda_veredicto(v),
                      vale if not v.startswith("pendiente") else "pendiente"])
        semillas.append(total)
        veredictos, deltas, aes = veredictos + [v], deltas + [r["delta_g_media"]], aes + [r["aceleracion"]]
    cab = ["variante", "G media (M$)", "Δ [IC 95%] (M$)", "semillas ganadas", "ΔAUC [IC 95%]", "T (s)", "aceleración (×)",
           "ganancia contra el control", "vale la pena (no pierde y ≥ 2×)"]
    marcar_mejores(filas, veredictos, {2: deltas, 6: aes})
    distintas = sorted({int(n) for n in semillas})
    if len(distintas) > 1:  # las semillas difieren entre filas: la columna vuelve
        cab.insert(1, "semillas")
        for f, n in zip(filas, semillas):
            f.insert(1, n)
        pie = ""
    else:
        pie = f"<p class='nota'>Todas las variantes con {distintas[0]} semillas.</p>" if distintas else ""
    return html_tabla(cab, filas) + pie


# --- celdas de las tablas del HTML (D5, D8): las reglas acá, los colores en `_sass/custom/custom.scss` ---

def clase_veredicto(v) -> str:
    """`ok`, `pierde`, `ind`, `pend` o "" (no es un veredicto, o es «no cambia» de una diferencia entre variantes)."""
    v = str(v)
    return {"pierde": "pierde", "no pierde": "ok", "gana": "ok", "indeterminado": "ind", "mejora": "ok",
            "empeora": "pierde"}.get(
        v, "pend" if v.startswith("pendiente") else "")


def celda(v: str, ic: str | None = None, clases: str = "", barra: tuple | None = None, nota: str | None = None,
          pill: bool = False, prop: float | None = None) -> dict:
    """Celda estructurada de `html_tabla`: valor, IC debajo, clases del `td`, barra del IC, nota al pie, etiqueta y, con
    `prop` (0 a 1), una barrita de proporción debajo del valor."""
    return {"v": v, "ic": ic, "clases": clases, "barra": barra, "nota": nota, "pill": pill, "prop": prop}


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
    """Tabla HTML sin envoltorio propio: el recuadro y el desplazamiento los pone el tema con un solo contenedor (D4).
    Con una línea en blanco antes y después, para que Markdown la tome como bloque. Cada celda es texto (si es un
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
        if c.get("prop") is not None:
            partes.append(f"<span class='prop' style='--p:{100 * c['prop']:.0f}%'></span>")
        if c["barra"]:
            lo, ancho = escala[j]
            pct = lambda x: f"{100 * (x - lo) / ancho:.1f}%"
            partes.append(f"<span class='icbar' style='--l:{pct(c['barra'][0])};--r:{pct(c['barra'][1])};--z:{pct(0.0)}'>"
                          "</span>")
        return (f"<td class='{c['clases']}'>" if c["clases"] else "<td>") + "".join(partes) + "</td>"

    cuerpo = "".join("<tr>" + "".join(td(c, j) for j, c in enumerate(f)) + "</tr>" for f in filas)
    pie = "".join(f"<p class='nota'><sup>{k}</sup> {html.escape(notas[k])}</p>" for k in sorted(usadas)) if notas else ""
    return ("<table><tr>" + "".join(f"<th>{html.escape(c)}</th>" for c in cab) + "</tr>" + cuerpo + "</table>" + pie)


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
    cab = ("variante", "T_opt (s)", "T_final (s)", "K", f"G del ensamble en {MES} (M$)", "G − Ḡ_C (M$)",
           f"G − ensamble {N_SEMILLAS} de C (M$)")
    if not ctx.agregador:
        return intro + f"<p>{html.escape(ref)}.</p>" + html_tabla(cab, filas)
    # en Resultados, una pestaña por hipótesis para que la tabla entre en 800 px de alto (D16)
    sangrar = lambda t: "\n".join("    " + linea if linea else "" for linea in t.splitlines())  # noqa: E731
    pestanas = "\n\n".join(f'=== "{h}"\n\n' + sangrar(html_tabla(cab, [f for f in filas if ctx.hip_de[f[0]] == h]))
                           for h in ctx.hipotesis)
    return intro + f"<p>{html.escape(ref)}.</p>\n\n" + pestanas


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
    """Una fila del bloque A, con todo lo que muestra la tabla HTML del bloque generado."""
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


def desglose_tiempo(ctx: Contexto, fin: pd.DataFrame, ap: pd.DataFrame) -> list[dict]:
    """T de la réplica 0 partido en optimización, entrenamiento final (`lgb.train`) y el resto del final (armado y
    predicción): un dict por variante, el control primero. La suma es el T de `apareado.csv`."""
    out = []
    for b in [lg.CONTROL, *ctx.variantes]:
        r = None if b == lg.CONTROL else fila(ap, b)
        sub = fin[fin["variante"] == b]
        if sub.empty or (b != lg.CONTROL and r is None) or "tiempo_lgbtrain_s" not in sub:
            continue
        t_total = float(ap["tiempo_total_control_s"].iloc[0] if r is None else r["tiempo_total_s"])
        t_ent, t_lgb = float(sub["tiempo_entrenamiento_s"].mean()), float(sub["tiempo_lgbtrain_s"].mean())
        out.append({"variante": b, "hipotesis": "control" if r is None else ctx.hip_de[b], "optimizacion": t_total - t_ent,
                    "final": t_lgb, "resto": t_ent - t_lgb})
    return out


def delta_semillas(ctx: Contexto, finr: pd.DataFrame) -> dict[str, dict]:
    """Δ de cada semilla de la réplica 0 (contra la misma semilla del control) y Δ de cada réplica (media de sus semillas
    contra la del control en esa réplica, o contra la media de las réplicas del control si esa no se corrió)."""
    if not len(finr) or "g" not in finr or "replica_opt" not in finr:
        return {}
    g = finr.groupby(["variante", "replica_opt", "semilla"])["g"].mean()
    if lg.CONTROL not in g.index.get_level_values(0):
        return {}
    c = g[lg.CONTROL]
    c_rep = c.groupby(level=0).mean()
    out = {}
    for b in ctx.variantes:
        if b not in g.index.get_level_values(0):
            continue
        v = g[b]
        sem = v.loc[0] if 0 in v.index.get_level_values(0) else None
        d_sem = [] if sem is None or 0 not in c.index.get_level_values(0) else \
            [float(x - c.loc[0][s]) for s, x in sem.items() if s in c.loc[0].index]
        d_rep = [float(m - (c_rep[r] if r in c_rep.index else c_rep.mean())) for r, m in v.groupby(level=0).mean().items()]
        out[b] = {"semillas": d_sem, "replicas": d_rep if len(d_rep) >= 2 else []}
    return out


def calcular_bloque_a(ctx: Contexto, fin: pd.DataFrame, ap: pd.DataFrame, n_boot: int = N_BOOT) -> dict:
    """Todo el bloque A y las tablas de réplicas, calculado una vez desde el ledger."""
    vacio = {"filas": [], "rep": pd.DataFrame(), "g_c1": None, "g_c10": None, "ti": {}, "g_rep": {}, "desglose": [],
             "semillas": {}}
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
            "desglose": desglose_tiempo(ctx, fin, ap), "semillas": delta_semillas(ctx, finr),
            "g_cR": None if c_rep is None else float(c_rep["g_media_replicas"]),
            "n_cR": None if c_rep is None else int(c_rep["n_replicas"]), "t_cR": t_cr,
            "delta": float(ap["delta_g_margen"].iloc[0]), "g_c0": float(ap["g_control"].iloc[0]),
            "t_c0": float(ap["tiempo_total_control_s"].iloc[0]), "g_rep": g_rep}


AVISO_A = ("Ḡ, T y la aceleración salen de la réplica 0 en las variantes sin réplicas; en las marcadas (R=n), Ḡ es la media entre "
           "réplicas, T la mediana entre réplicas y la aceleración = T_C / T con T_C también mediana entre réplicas, así que se comparan "
           "con Ḡ_C con réplicas y no con Ḡ_C de la réplica 0.")


def referencia_control(a: dict) -> str:
    txt = (f"Final entrenado con {VENTANA}, {N_SEMILLAS} semillas por réplica; N* = {a['n_est']:,} clientes contactados; "
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


CAB_A = ("variante", "hipótesis", "Ḡ (M$)", "Δ réplica 0 [IC] (M$)", "Δ con réplicas [IC] (M$)", "ΔAUC en 201910 [IC]", "T mediana (s)", "aceleración (×)",
         "tiempo igual, réplicas [IC t] (M$)", "tiempo igual, bootstrap de clientes [IC] (M$)", "ganancia contra el control (fuente)")


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


def _cifra(etiqueta: str, unidad: str, s: pd.Series, escala: float = 1.0) -> list[str]:
    """Fila numérica de una cifra de un exploratorio: etiqueta, unidad, mediana, mínimo, máximo y n (ya con la escala)."""
    x = pd.to_numeric(s, errors="coerce").dropna() * escala
    if x.empty:
        return [etiqueta, unidad, "sin datos numéricos", "", "", "0"]
    f = (lambda v: f"{v:,.2f}") if x.abs().max() >= 100 else (lambda v: f"{v:.4g}")
    return [etiqueta, unidad, f(x.median()), f(x.min()), f(x.max()), str(len(x))]


def fig_sensibilidad(serie: pd.Series, unidad: str, titulo: str, nombre: str, destino: Path) -> str:
    """Δ por muestra: un punto por muestra y su mediana, en `unidad` (la figura que `sensibilidad_muestra` declara con
    `csv` y `columna`: el estudio original no tiene gráficos). Las figuras de un exploratorio van junto a su página."""
    global DESTINO
    x = pd.to_numeric(serie, errors="coerce").dropna().to_numpy()
    if not len(x):
        return pendiente("la columna del estudio no tiene datos")
    previo, DESTINO = DESTINO, Destino(destino)
    try:
        fig, ax = plt.subplots(figsize=(ANCHO * 0.7, 3.2))
        y = np.linspace(-0.25, 0.25, len(x)) if len(x) > 1 else np.zeros(1)
        ax.scatter(x, y, color=PALETA[0], s=36, zorder=3, label="muestra")
        ax.axvline(float(np.median(x)), color=TINTA, linestyle=":", label=f"mediana {np.median(x):.2f} {unidad}")
        ax.axvline(0, color="#999999", linewidth=0.8)
        ax.set_yticks([])
        ax.set_ylim(-0.6, 0.6)
        ax.set_xlabel(f"Δ de ganancia contra el control ({unidad})")
        ax.legend(loc="upper left", frameon=False)
        _ejes(ax)
        fig.suptitle(titulo)
        enlace = figura(fig, nombre, None)
        archivos = dict(DESTINO.archivos)
    finally:
        DESTINO = previo
    if DESTINO is not None:
        DESTINO.archivos.update(archivos)
    return enlace


def bloque_b(raiz: Path = rutas.RAIZ, pagina: Path | None = None) -> list[dict]:
    """Una fila por `exploratorio.json`. Un CSV que falta deja la tabla como pendiente con el nombre del archivo.
    `cifras` mezcla filas numéricas (etiqueta, unidad, mediana, mínimo, máximo, n) y avisos de pendiente (texto);
    `figuras` son pares (enlace Markdown relativo a `pagina`, leyenda). Una columna declarada como texto vale como
    una con solo `columna`, sin escala ni unidad."""
    import json
    import os
    pagina = pagina or raiz / "experimentos" / "sampling_1" / "exploratorios" / "README.md"
    filas = []
    for m in reg.manifiestos(raiz):
        d = json.loads(m.read_text())
        cifras, figuras = [], []
        for t in d.get("tablas", []):
            ruta = m.parent / t["csv"]
            if not ruta.is_file():
                cifras.append(f"pendiente: falta {t['csv']}")
                continue
            df = pd.read_csv(ruta)
            for c in t["columnas"]:
                c = c if isinstance(c, dict) else {"columna": c}
                if c["columna"] not in df:
                    cifras.append(f"pendiente: falta la columna {c['columna']} de {ruta.name}")
                    continue
                cifras.append(_cifra(c.get("etiqueta") or f"{ruta.name}, {c['columna']}", c.get("unidad", ""),
                                     df[c["columna"]], c.get("escala", 1.0)))
        for f in d.get("figuras", []):
            if f.get("archivo"):
                figuras.append((f"![{f['leyenda']}]({os.path.relpath(m.parent / f['archivo'], pagina.parent)})", f["leyenda"]))
                continue
            ruta = m.parent / f["csv"]
            if not ruta.is_file():
                figuras.append((pendiente(f"falta {f['csv']}"), f["leyenda"]))
                continue
            serie = pd.read_csv(ruta).get(f["columna"], pd.Series(dtype=float)) * f.get("escala", 1.0)
            enlace = fig_sensibilidad(serie, f.get("unidad", ""), f["leyenda"], m.parent.name, pagina.parent / "figuras")
            figuras.append((enlace, ""))
        filas.append({"carpeta": str(m.parent.relative_to(raiz)), "pregunta": d.get("pregunta", ""),
                      "protocolo": d.get("protocolo", ""), "figuras": figuras, "cifras": cifras,
                      "advertencia": d.get("advertencia", "")})
    return filas


def tabla_md(cab, filas) -> str:
    esc = lambda c: str(c).replace("|", "\\|").replace("\n", " ")
    return ("| " + " | ".join(cab) + " |\n|" + "---|" * len(cab) + "\n"
            + "".join("| " + " | ".join(esc(c) for c in f) + " |\n" for f in filas))


CAB_CIFRAS = ("cifra", "unidad", "mediana", "mínimo", "máximo", "n")


def lista_b(b: list[dict]) -> str:
    """Bloque B de los exploratorios: una sección por estudio con su pregunta (`question`), el protocolo, las figuras con
    su leyenda, las cifras en una tabla numérica plegada y la advertencia (`warning`)."""
    if not b:
        return "No hay exploratorios declarados.\n"
    sangria = lambda t: "\n".join("    " + linea if linea else "" for linea in t.splitlines())  # noqa: E731
    out = []
    for f in b:
        out += [f"### {Path(f['carpeta']).name}\n", f'!!! question "Pregunta"\n{sangria(f["pregunta"])}\n',
                f"**Protocolo.** {f['protocolo']}\n"]
        for enlace, leyenda in f.get("figuras", []):
            out.append(enlace.strip() + "\n")
            if leyenda:
                out.append(f"<p class='nota'>{html.escape(leyenda)}</p>\n")
        filas = [c for c in f["cifras"] if not isinstance(c, str)]
        pend = [c for c in f["cifras"] if isinstance(c, str)]
        if filas:
            out.append(_plegable("Cifras principales", tabla_md(CAB_CIFRAS, filas)) + "\n")
        if pend:
            out.append("\n".join(f"- {c}" for c in pend) + "\n")
        out.append(f'!!! warning "Advertencia"\n{sangria(f["advertencia"])}\n')
    return "\n".join(out)


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
    ax.set_yticks(range(len(filas)), etiquetas, fontsize=11)
    ax.invert_yaxis()
    for i in range(1, len(filas)):
        if filas[i]["hipotesis"] != filas[i - 1]["hipotesis"]:
            for x in (ax, *otros):
                x.axhline(i - 0.5, color="#dddddd", lw=0.8)


def _marcas_veredicto(clases: list[str]) -> tuple[list, list[str]]:
    usadas = [c for c in ("ok", "ind", "pierde", "pend") if c in clases]
    return ([Line2D([], [], color=COLOR_VEREDICTO[c], marker="o", ls="") for c in usadas],
            [NOMBRE_VEREDICTO[c] for c in usadas])


MARCAS = "osD^v<>p"
TINTA = "#0b0b0b"  # texto en tinta primaria, nunca en el color de la serie


def _etiquetas_sin_pisar(ax, puntos: list[tuple[float, float]], textos: list[str], alto: float = 0.055,
                         ancho: float = 0.09) -> None:
    """Etiqueta cada punto (en datos) sin que dos etiquetas se pisen ni tapen puntos vecinos: un punto aislado lleva su
    etiqueta a la derecha; los puntos pegados en x forman un grupo, con sus etiquetas en una columna a la derecha del
    grupo (ordenadas por y) unidas a su punto por una línea. Lo que aun choque se corre con `desplazar_dentro`. Los
    límites de `ax` ya tienen que estar fijados."""
    a_fraccion = ax.transScale + ax.transLimits
    pts = [tuple(a_fraccion.transform(p)) for p in puntos]
    grupos: list[list[int]] = []
    for i in sorted(range(len(pts)), key=lambda i: pts[i][0]):
        cerca = next((g for g in grupos if any(pts[i][0] - pts[j][0] < 0.045 and abs(pts[i][1] - pts[j][1]) < 0.2
                                               for j in g)), None)
        if cerca is not None:
            cerca.append(i)
        else:
            grupos.append([i])
    pos: list = [None] * len(pts)
    for g in grupos:
        if len(g) == 1:
            px, py = pts[g[0]]
            pos[g[0]] = (px - 0.03, py) if px > 0.85 else (px + 0.012, py)
            continue
        x = max(pts[j][0] for j in g) + 0.03
        centro = sum(pts[j][1] for j in g) / len(g)
        # Si otro punto ocupa el lugar de la columna a la derecha, la columna va a la izquierda del grupo.
        if any(j not in g and -0.01 < pts[j][0] - x < 0.12 and abs(pts[j][1] - centro) < (len(g) / 2 + 1) * alto
               for j in range(len(pts))):
            x = min(pts[j][0] for j in g) - 0.03
        for k, j in enumerate(sorted(g, key=lambda j: -pts[j][1])):
            pos[j] = (x, centro + (len(g) / 2 - k - 0.5) * alto)
    for i, (lx, ly) in enumerate(desplazar_dentro(pos, alto, ancho)):
        (px, py), t = pts[i], textos[i]
        der = lx < px or lx > 0.9
        ax.annotate(t, puntos[i], xytext=(lx - 0.012 if lx > 0.9 and lx >= px else lx, ly), textcoords="axes fraction", fontsize=11,
                    color=TINTA, va="center", ha="right" if der else "left",
                    arrowprops=dict(arrowstyle="-", color="#aaaaaa", lw=0.6, shrinkA=1, shrinkB=4,
                                    relpos=(1.0 if der else 0.0, 0.5)) if (lx - px > 0.02 or abs(ly - py) > 1e-9) else None)


def _marcador_veredicto(ax, x, d, ic, color, clase, **kw) -> None:
    """Punto con su IC vertical: círculo lleno si no pierde, círculo vacío si pierde, rombo gris claro si es indeterminado (D16)."""
    ax.errorbar([x], [d], yerr=[[d - ic[0]], [ic[1] - d]], fmt="none", capsize=2, color=color, lw=1.2, zorder=2)
    cara = {"ok": color, "ind": "#d9d9d9"}.get(clase, "white")
    ax.scatter([x], [d], s=64 if clase != "ind" else 56, marker="D" if clase == "ind" else "o", facecolor=cara,
               edgecolor=color, linewidth=1.6, zorder=3, **kw)


def _etiquetas_en_columna(ax, puntos: list[tuple[float, float]], textos: list[str]) -> None:
    """Para un panel denso: las etiquetas van en una columna a la izquierda de los puntos, cada una unida a su punto por
    una línea fina. El orden de la columna sale de minimizar los cruces entre las líneas (intercambios de a pares, en
    orden fijo, así que regenerar da lo mismo)."""
    a_fraccion = ax.transScale + ax.transLimits
    pts = [tuple(a_fraccion.transform(p)) for p in puntos]
    n = len(pts)
    x_col = max(0.3, min(p[0] for p in pts) - 0.08)
    ys = [0.95 - k * 0.9 / (n - 1) for k in range(n)]
    orden = sorted(range(n), key=lambda i: -pts[i][1])

    def cruza(a, b, c, d) -> bool:
        def ccw(p, q, r):
            return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
        return ccw(a, c, d) * ccw(b, c, d) < 0 and ccw(a, b, c) * ccw(a, b, d) < 0

    def cruces(o) -> int:
        seg = [((x_col + 0.01, ys[k]), pts[i]) for k, i in enumerate(o)]
        return sum(cruza(*seg[i], *seg[j]) for i in range(n) for j in range(i + 1, n))

    mejor = cruces(orden)
    mejoro = True
    while mejoro and mejor:
        mejoro = False
        for i in range(n):
            for j in range(i + 1, n):
                orden[i], orden[j] = orden[j], orden[i]
                c = cruces(orden)
                if c < mejor:
                    mejor, mejoro = c, True
                else:
                    orden[i], orden[j] = orden[j], orden[i]
    lugar = {i: k for k, i in enumerate(orden)}
    for i in range(n):  # en el orden de `puntos`, que es el de `ax.texts`
        ax.annotate(textos[i], puntos[i], xytext=(x_col, ys[lugar[i]]), textcoords="axes fraction", fontsize=11,
                    color=TINTA, va="center", ha="right",
                    bbox=dict(boxstyle="square,pad=0.1", fc="white", ec="none", alpha=0.8),
                    arrowprops=dict(arrowstyle="-", color="#aaaaaa", lw=0.6, shrinkA=1, shrinkB=4, relpos=(1.0, 0.5)))


def fig_tradeoff(ctx: Contexto, a: dict, figuras: Path | None, nombre: str = "tradeoff") -> str:
    """Mapa del tradeoff en paneles de 2 × 2, uno por hipótesis (D10, D16): aceleración (log) contra Δ con su IC, con
    los ejes compartidos. El control es la referencia en (1×, 0), la línea de 2× y −δ punteado; el color es el de la
    hipótesis, el veredicto va en el marcador y las variantes que valen la pena llevan la etiqueta en negrita."""
    filas = [f for f in a["filas"] if f["variante"] in ctx.variantes and delta(f) is not None and f["A"] is not None]
    if not filas:
        return pendiente("ninguna variante tiene Δ contra el control")
    d_m = a["delta"] / 1e6
    ics = {f["variante"]: tuple(x / 1e6 for x in delta(f)) for f in filas}
    aes = [f["A"] for f in filas]
    lo, hi = min(min(i[1] for i in ics.values()), -d_m), max(max(i[2] for i in ics.values()), 0.0)
    pad = 0.08 * (hi - lo)
    hips = [h for h in ctx.hipotesis if any(f["hipotesis"] == h for f in filas)]
    cols = 2 if len(hips) > 1 else 1
    nf = math.ceil(len(hips) / cols)
    fig, axs = plt.subplots(nf, cols, figsize=(ANCHO, 3.6 * nf + 1.0), sharex=True, sharey=True, squeeze=False)
    xmin, xmax = min(min(aes), 1) / 1.35, max(max(aes), A_VALE) * 1.8
    clases = []
    for ax, h in zip(axs.flat, hips):
        ax.set_xscale("log")
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(lo - pad, hi + pad)
        ax.axhspan(-d_m, hi + pad, color=COLOR_VEREDICTO["ok"], alpha=0.07, lw=0)
        ax.axhline(0, color=COLOR_C, lw=0.8)
        ax.axhline(-d_m, color=COLOR_C, ls=":", lw=1)
        ax.axvline(1, color=COLOR_C, ls="--", lw=0.8)
        ax.axvline(A_VALE, color=COLOR_C, ls="-.", lw=0.8)
        ax.scatter([1], [0], s=40, color=COLOR_C, zorder=3)
        propias = [f for f in filas if f["hipotesis"] == h]
        puntos, textos, vale = [], [], []
        for f in propias:
            c = clase_veredicto(f["veredicto"])
            clases.append(c)
            _marcador_veredicto(ax, f["A"], ics[f["variante"]][0], ics[f["variante"]][1:], ctx.color[h], c)
            puntos.append((f["A"], ics[f["variante"]][0]))
            textos.append(f["variante"])
            vale.append(c == "ok" and f["A"] >= A_VALE)
        n0 = len(ax.texts)
        if len(puntos) >= 6:
            _etiquetas_en_columna(ax, puntos, textos)
        else:
            _etiquetas_sin_pisar(ax, puntos, textos, alto=0.1, ancho=0.2)
        for t, v in zip(ax.texts[n0:], vale):
            t.set_color(ctx.color[h])
            t.set_fontweight("bold" if v else "normal")
        ax.set_title(h, fontsize=12, loc="left", color=ctx.color[h], fontweight="bold")
        ax.set_xticks([x for x in (0.5, 1, 2, 5, 10, 20, 50) if xmin <= x <= xmax], [f"{x:g}×" for x in (0.5, 1, 2, 5, 10, 20, 50) if xmin <= x <= xmax])
        ax.minorticks_off()
        _ejes(ax)
    for ax in axs.flat[len(hips):]:
        ax.set_visible(False)
    for ax in axs[-1]:
        ax.set_xlabel("aceleración (×) = T(C) / T, escala log")
    for ax in axs[:, 0]:
        ax.set_ylabel("Δ contra el control (M$, IC 95%)")
    sin_perder = [f for f in filas if clase_veredicto(f["veredicto"]) == "ok" and f["A"] >= A_VALE]
    if sin_perder:
        mejor = max(sin_perder, key=lambda f: f["A"])
        titulo = (f"{len(sin_perder)} de {len(filas)} variantes no pierden y aceleran {A_VALE:g}× o más; "
                  f"la más rápida entre ellas es {mejor['variante']} ({mejor['A']:.1f}×)")
    else:
        titulo = f"Ninguna de las {len(filas)} variantes no pierde y acelera {A_VALE:g}× o más"
    fig.suptitle(titulo, fontsize=13, x=0.01, ha="left", wrap=True)
    marcas = [Line2D([], [], color=TINTA, marker="o", ls="", mfc=TINTA), Line2D([], [], color=TINTA, marker="o", ls="", mfc="white", mew=1.6),
              Line2D([], [], color=COLOR_C, marker="o", ls="")]
    nombres = ["no pierde (círculo lleno)", "pierde (círculo vacío)", "control (1×, 0)"]
    if "ind" in clases:
        marcas.insert(2, Line2D([], [], color=TINTA, marker="D", ls="", mfc="#d9d9d9", mew=1.6))
        nombres.insert(2, "indeterminado (rombo gris)")
    marcas += [Line2D([], [], color=COLOR_C, ls=":", lw=1), Line2D([], [], color=COLOR_C, ls="-.", lw=0.8)]
    nombres += ["−δ (debajo, pierde)", f"{A_VALE:g}×"]
    fig.legend(marcas, nombres, frameon=False, fontsize=10, loc="lower center", ncol=3)
    fig.tight_layout(rect=(0, 0.09, 1, 0.94))
    return figura(fig, nombre, figuras, ajustar=False)


def fig_fraccion(ctx: Contexto, a: dict, figuras: Path | None) -> str:
    """Δ contra la fracción de muestra (`Variante.tasa`) en paneles de 2 × 2, uno por hipótesis (D16): una línea por
    `Variante.metodo` con dos tasas o más, con la banda de su IC y la línea de −δ; ejes compartidos."""
    por: dict[tuple[str, str], list[tuple]] = {}
    for f in a["filas"]:
        v, d = reg.VARIANTES.get(f["variante"]), delta(f)
        if v is not None and d is not None:
            por.setdefault((v.dueno.upper(), v.metodo), []).append((v.tasa, *d, f["variante"]))
    familias = {k: sorted(p) for k, p in por.items() if len({x[0] for x in p}) >= 2}
    if not familias:
        return pendiente("ninguna familia de variantes tiene dos fracciones con datos")
    hips = [h for h in ctx.hipotesis if any(k[0] == h for k in familias)]
    cols = 2 if len(hips) > 1 else 1
    nf = math.ceil(len(hips) / cols)
    fig, axs = plt.subplots(nf, cols, figsize=(ANCHO, 3.2 * nf + 1.0), sharex=True, sharey=True, squeeze=False)
    d_m = a["delta"] / 1e6
    tasas = sorted({x[0] for p in familias.values() for x in p})
    for ax, h in zip(axs.flat, hips):
        for j, ((_, m), p) in enumerate(k for k in familias.items() if k[0][0] == h):
            t = np.array([x[0] for x in p])
            d, lo, hi = (np.array([x[i] for x in p]) / 1e6 for i in (1, 2, 3))
            ax.fill_between(t, lo, hi, color=ctx.color[h], alpha=0.16, lw=0)
            ax.plot(t, d, "-" + MARCAS[j % len(MARCAS)], ms=6, mec="white", mew=1, lw=2, color=ctx.color[h], label=m)
        ax.axhline(0, color=COLOR_C, lw=0.8)
        ax.axhline(-d_m, color=COLOR_C, ls=":", lw=1)
        ax.set_xscale("log")
        ax.set_xticks(tasas, [f"{t:g}" for t in tasas])
        ax.minorticks_off()
        ax.set_title(h, fontsize=12, loc="left", color=ctx.color[h], fontweight="bold")
        ax.legend(frameon=False, fontsize=10, loc="lower right")
        _ejes(ax)
    for ax in axs.flat[len(hips):]:
        ax.set_visible(False)
    for ax in axs[-1]:
        ax.set_xlabel("fracción de la muestra (log)")
    for ax in axs[:, 0]:
        ax.set_ylabel("Δ contra el control (M$)")
    peor = min((x for p in familias.values() for x in p), key=lambda x: x[1])
    fig.suptitle(f"Δ contra la fracción de muestra: el punto más bajo es {peor[4]} ({peor[1] / 1e6:+.1f} M\\$), "
                 f"{'por debajo de' if peor[1] / 1e6 < -d_m else 'dentro de'} −δ (punteada)", fontsize=13, x=0.01, ha="left", wrap=True)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    return figura(fig, "fraccion", figuras, ajustar=False)


def fig_desglose(ctx: Contexto, a: dict, figuras: Path | None) -> str:
    """Desglose del tiempo T de la réplica 0 por variante y para el control: optimización, entrenamiento final y el
    resto del final (armado y predicción), en barras apiladas."""
    d = a.get("desglose", [])
    if len(d) < 2:
        return pendiente("faltan los tiempos del control o de las variantes")
    fig, ax = plt.subplots(figsize=(ANCHO, 5.2))
    x, base = np.arange(len(d)), np.zeros(len(d))
    for clave, color, etiqueta in (("optimizacion", PALETA[0], "optimización (Optuna)"),
                                   ("final", PALETA[1], "entrenamiento final"),
                                   ("resto", PALETA[2], "armado y predicción del final")):
        v = np.array([r[clave] for r in d])
        ax.bar(x, v, bottom=base, width=0.72, color=color, edgecolor="white", linewidth=1.2, label=etiqueta)
        base += v
    ax.set_xticks(x, [r["variante"] for r in d], rotation=60, ha="right", fontsize=11)
    c, corta = d[0], min(d[1:], key=lambda r: r["optimizacion"])
    t_c = c["optimizacion"] + c["final"] + c["resto"]
    fig.suptitle(f"En el control la optimización es el {100 * c['optimizacion'] / t_c:.0f} % de T ({c['optimizacion']:.0f} s "
                 f"de {t_c:.0f} s); la variante con la optimización más corta, {corta['variante']}, la baja a "
                 f"{corta['optimizacion']:.0f} s", fontsize=14, x=0.01, ha="left")
    ax.set_ylabel("tiempo T de la réplica 0 (s)")
    ax.legend(frameon=False, fontsize=11, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.22))
    _ejes(ax)
    return figura(fig, "desglose_tiempo", figuras)


def _paneles_por_hipotesis(ctx: Contexto, filas: list[dict], alto_fila: float, extra: float = 2.4):
    """Paneles de 2 × 2, uno por hipótesis (D16), con el eje x compartido y una fila por variante en cada panel; el alto
    de cada fila de paneles sigue a su panel con más variantes. Devuelve la figura, los ejes y las hipótesis."""
    hips = [h for h in ctx.hipotesis if any(f["hipotesis"] == h for f in filas)]
    cols = 2 if len(hips) > 1 else 1
    nf = math.ceil(len(hips) / cols)
    por_fila = [max(sum(f["hipotesis"] == h for f in filas) for h in hips[i * cols:(i + 1) * cols]) for i in range(nf)]
    fig, axs = plt.subplots(nf, cols, figsize=(ANCHO, alto_fila * sum(por_fila) + extra), sharex=True, squeeze=False,
                            gridspec_kw={"height_ratios": por_fila})
    for ax in axs.flat[len(hips):]:
        ax.set_visible(False)
    return fig, axs, hips


def fig_semillas(ctx: Contexto, a: dict, figuras: Path | None) -> str:
    """Δ de cada semilla (un punto) por variante en paneles de 2 × 2, uno por hipótesis (D16); las réplicas de Optuna,
    con otro marcador (media de sus semillas). El color es el de la hipótesis y el veredicto va en la caja: llena si no
    pierde, solo el borde si pierde."""
    s = a.get("semillas", {})
    filas = [f for f in a["filas"] if s.get(f["variante"], {}).get("semillas")]
    if not filas:
        return pendiente("ninguna variante tiene Δ por semilla")
    fig, axs, hips = _paneles_por_hipotesis(ctx, filas, 0.34)
    hay_rep = False
    for ax, h in zip(axs.flat, hips):
        propias = [f for f in filas if f["hipotesis"] == h]
        col = ctx.color[h]
        for i, f in enumerate(propias):
            ok = clase_veredicto(f["veredicto"]) == "ok"
            sem = np.array(s[f["variante"]]["semillas"]) / 1e6
            q1, q3 = np.percentile(sem, [25, 75])
            ax.barh(i, q3 - q1, left=q1, height=0.56, facecolor=col if ok else "none", alpha=0.3 if ok else 1,
                    edgecolor=col, linewidth=1, zorder=1)
            ax.vlines(sem.mean(), i - 0.28, i + 0.28, color=col, linewidth=2.2, zorder=2)
            ax.scatter(sem, i + (np.arange(len(sem)) % 5 - 2) * 0.09, s=16, color=col, alpha=0.65, lw=0, zorder=2)
            rep = np.array(s[f["variante"]]["replicas"]) / 1e6
            if len(rep):
                hay_rep = True
                ax.scatter(rep, [i] * len(rep), s=46, marker="D", facecolor="white", edgecolor=col, linewidth=1.5, zorder=3)
        ax.axvline(0, color=COLOR_C, lw=0.8)
        ax.axvline(-a["delta"] / 1e6, color=COLOR_C, ls=":", lw=1)
        ax.set_yticks(range(len(propias)), [f["variante"] for f in propias], fontsize=11)
        ax.set_ylim(len(propias) - 0.5, -0.5)
        ax.set_title(h, fontsize=12, loc="left", color=col, fontweight="bold")
        _ejes(ax)
    for ax in axs[-1]:
        ax.set_xlabel("Δ contra la misma semilla del control (M$); punteada: −δ")
    amplio = max(filas, key=lambda f: np.ptp(s[f["variante"]]["semillas"]))
    fig.suptitle(f"Cada punto es una semilla: la dispersión entre semillas llega a "
                 f"{np.ptp(s[amplio['variante']]['semillas']) / 1e6:.1f} M$ ({amplio['variante']})", fontsize=14, x=0.01,
                 ha="left")
    marcas = [Line2D([], [], color=COLOR_C, marker="o", ms=4, ls=""), Line2D([], [], color=COLOR_C, lw=2.2),
              plt.Rectangle((0, 0), 1, 1, facecolor=COLOR_C, alpha=0.3, edgecolor=COLOR_C),
              plt.Rectangle((0, 0), 1, 1, facecolor="none", edgecolor=COLOR_C)]
    nombres = ["semilla (réplica 0)", "media de las semillas", "caja llena: Q1–Q3, no pierde", "caja vacía: Q1–Q3, pierde"]
    if hay_rep:
        marcas.append(Line2D([], [], color=COLOR_C, marker="D", mfc="white", ls=""))
        nombres.append("réplica de Optuna (media de sus semillas)")
    fig.legend(marcas, nombres, frameon=False, fontsize=11, ncol=2, loc="lower center")
    fig.tight_layout(rect=(0, 0.1, 1, 0.96))
    return figura(fig, "semillas_replicas", figuras, ajustar=False)


def fig_grilla(ctx: Contexto, a: dict, figuras: Path | None) -> str:
    """Grilla de veredictos: familia (`Variante.metodo`) contra tasa; cada celda con el color y el texto del veredicto, y
    vacía si esa combinación no está en el registro."""
    from matplotlib.patches import Rectangle
    celdas: dict[tuple[str, float], list[dict]] = {}
    for f in a["filas"]:
        v = reg.VARIANTES.get(f["variante"])
        if v is not None:
            celdas.setdefault((v.metodo, v.tasa), []).append(f)
    if not celdas:
        return pendiente("no hay variantes registradas con datos")
    metodos = list(dict.fromkeys(m for m, _ in celdas))
    tasas = sorted({t for _, t in celdas})
    fig, ax = plt.subplots(figsize=(ANCHO, 0.72 * len(metodos) + 1.8))
    for (m, t), fs in celdas.items():
        i, j = metodos.index(m), tasas.index(t)
        c = clase_veredicto(fs[0]["veredicto"]) or "pend"
        ax.add_patch(Rectangle((j - 0.46, i - 0.46), 0.92, 0.92, facecolor=COLOR_VEREDICTO[c], alpha=0.25, lw=0))
        ax.text(j, i, "\n".join(f"{f['variante']}\n{NOMBRE_VEREDICTO[clase_veredicto(f['veredicto']) or 'pend']}"
                                for f in fs), ha="center", va="center", fontsize=11, color=TINTA)
    ax.set_xlim(-0.5, len(tasas) - 0.5)
    ax.set_ylim(len(metodos) - 0.5, -0.5)
    ax.set_xticks(range(len(tasas)), [f"{t:g}" for t in tasas])
    ax.set_yticks(range(len(metodos)), [f"{m} ({celdas[next(k for k in celdas if k[0] == m)][0]['hipotesis']})"
                                        for m in metodos], fontsize=11)
    ax.set_xlabel("fracción de la muestra")
    ax.tick_params(length=0)
    ax.spines[:].set_visible(False)
    cuenta = {c: sum(clase_veredicto(f["veredicto"]) == c for fs in celdas.values() for f in fs) for c in ("ok", "pierde", "ind")}
    total = sum(len(fs) for fs in celdas.values())
    pend = total - sum(cuenta.values())
    fig.suptitle(f"De {total} variantes: no pierden {cuenta['ok']}, pierden {cuenta['pierde']}, indeterminadas "
                 f"{cuenta['ind']}, pendientes {pend}", fontsize=14, x=0.01, ha="left")
    return figura(fig, "grilla_veredictos", figuras)


def delta_ronda_anterior(raiz: Path = rutas.RAIZ) -> pd.DataFrame:
    """Δ apareado (réplica 0) de la ronda anterior de todos los ledgers, por variante (`ronda_201903-201906/`)."""
    tablas = []
    for e in reg.duenos():
        f = rutas.ledger(e) / "ronda_201903-201906" / "apareado.csv"
        if f.exists():
            tablas.append(lg.leer_csv(f))
    if not tablas:
        return pd.DataFrame()
    return pd.concat(tablas, ignore_index=True).drop_duplicates("variante").set_index("variante")


def fig_rondas(ctx: Contexto, a: dict, figuras: Path | None, anterior: pd.DataFrame | None = None) -> str:
    """Comparación entre rondas: por variante, Δ de la ronda anterior (círculo hueco) unido por un segmento al de la
    vigente (círculo lleno); sin ronda anterior, solo el punto vigente."""
    anterior = delta_ronda_anterior() if anterior is None else anterior
    filas = [f for f in a["filas"] if f["d0"] is not None]
    if not filas:
        return pendiente("ninguna variante tiene Δ en la ronda vigente")
    fig, ax = plt.subplots(figsize=(ANCHO, 0.32 * len(filas) + 1.9))
    cambios = []
    for i, f in enumerate(filas):
        col = COLOR_VEREDICTO[clase_veredicto(f["veredicto"])]
        nuevo = f["d0"][0] / 1e6
        if len(anterior) and f["variante"] in anterior.index:
            viejo = float(anterior.loc[f["variante"], "delta_g_media"]) / 1e6
            ax.plot([viejo, nuevo], [i, i], color="#aaaaaa", lw=1.6, zorder=1)
            ax.scatter([viejo], [i], s=46, facecolor="white", edgecolor=col, linewidth=1.5, zorder=2)
            cambios.append((abs(nuevo - viejo), f["variante"], nuevo - viejo))
        ax.scatter([nuevo], [i], s=46, color=col, zorder=3)
    ax.axvline(0, color=COLOR_C, lw=0.8)
    _filas_por_variante(ax, filas, [_etiqueta(f) for f in filas])
    if cambios:
        _, v, dd = max(cambios)
        titulo = f"La mayor diferencia entre rondas es la de {v}: Δ cambia {dd:+.1f} M$"
    else:
        titulo = "Ninguna variante tiene ronda anterior para comparar"
    fig.suptitle(titulo, fontsize=14, x=0.01, ha="left")
    ax.set_xlabel("Δ apareado de la réplica 0 contra el control (M$); hueco: ronda anterior, lleno: vigente")
    _ejes(ax)
    return figura(fig, "rondas", figuras)


def _curvas(fin: pd.DataFrame, variante: str) -> dict[int, pd.Series]:
    """Curva de ganancia en `MES` (por clientes contactados) de cada semilla final de `variante`."""
    col = f"curva_{MES}"
    if col not in fin:
        return {}
    sub = fin[fin["variante"] == variante]
    return {int(s): lg.leer_curva(Path(), r).set_index("envios")["ganancia"] for s, r in zip(sub["semilla"], sub[col])
            if isinstance(r, str)}


def curvas_diferencia(fin: pd.DataFrame, variante: str) -> pd.DataFrame | None:
    """G(variante) − G(C) por clientes contactados, una columna por semilla (la misma semilla en las dos curvas)."""
    cc, cv = _curvas(fin, lg.CONTROL), _curvas(fin, variante)
    semillas = sorted(set(cc) & set(cv))
    if not semillas:
        return None
    return pd.concat([(cv[s] - cc[s]).rename(s) for s in semillas], axis=1).dropna(how="all")


def fig_curva_diferencia(ctx: Contexto, h: str, fin: pd.DataFrame, ap: pd.DataFrame, figuras: Path | None) -> str:
    """Curva de diferencia de la hipótesis `h`: G(variante) − G(C) contra clientes contactados, un panel por variante, con la mediana, la
    banda mín–máx entre semillas, la línea de 0 y el corte N*."""
    difs = {b: curvas_diferencia(fin, b) for b in ctx.hipotesis[h][1]}
    difs = {b: d for b, d in difs.items() if d is not None}
    if not difs or ap.empty:
        return pendiente("faltan curvas del control o de las variantes")
    n_est = int(ap["n_estrella"].iloc[0])
    cols = 2  # siempre dos columnas de paneles (D14)
    filas = math.ceil(len(difs) / cols)
    fig, axs = plt.subplots(filas, cols, figsize=(ANCHO, 3.1 * filas + 0.9), sharex=True, sharey=True, squeeze=False)
    debajo = []
    for ax, (b, d) in zip(axs.flat, difs.items()):
        med = d.median(axis=1) / 1e6
        ax.fill_between(d.index, d.min(axis=1) / 1e6, d.max(axis=1) / 1e6, color=ctx.color[h], alpha=0.2, lw=0)
        ax.plot(d.index, med, color=ctx.color[h], lw=1.6)
        ax.axhline(0, color=COLOR_C, lw=0.8)
        ax.axvline(n_est, color="#999999", ls=":", lw=1)
        ax.set_xlim(0, 15000)
        ax.set_xticks([0, 5000, 10000, 15000])
        ax.set_title(b, fontsize=10, loc="left")
        _ejes(ax)
        if float(med.loc[:n_est].iloc[-1]) < 0:
            debajo.append(b)
    for ax in axs.flat[len(difs):]:
        ax.set_visible(False)
    for ax in axs[-1]:
        ax.set_xlabel("N clientes contactados")
    for ax in axs[:, 0]:
        ax.set_ylabel(f"G(variante) − G(C), {MES} (M$)")
    resumen = ", ".join(debajo[:3]) + ("…" if len(debajo) > 3 else "")
    fig.suptitle(f"{h}: en N* = {n_est:,} clientes contactados, {len(debajo)} de {len(difs)} variantes quedan por debajo del control"
                 + (f" ({resumen})" if debajo else "") + "; línea: mediana, banda: mín–máx entre semillas",
                 fontsize=14, x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    return figura(fig, f"curva_diferencia_{h}", figuras, ajustar=False)


def fig_curvas_ganancia(ctx: Contexto, h: str, fin: pd.DataFrame, ap: pd.DataFrame, figuras: Path | None) -> str:
    """Curvas de ganancia de la hipótesis `h`: un panel por variante (siempre dos columnas, D14) con G en `MES` contra N
    clientes contactados, la banda P10–P90 entre semillas de la variante y de la control, la mediana del control punteada
    y el corte N*."""
    curvas = {b: _curvas(fin, b) for b in ctx.hipotesis[h][1]}
    curvas = {b: c for b, c in curvas.items() if c}
    control = _curvas(fin, lg.CONTROL)
    if not curvas or not control or ap.empty:
        return pendiente("faltan curvas del control o de las variantes")
    n_est = int(ap["n_estrella"].iloc[0])
    cols = 2
    filas = math.ceil(len(curvas) / cols)
    bandas = lambda c: pd.concat(list(c.values()), axis=1)  # noqa: E731
    bc = bandas(control)
    fig, axs = plt.subplots(filas, cols, figsize=(ANCHO, 3.0 * filas + 1.0), sharex=True, sharey=True, squeeze=False)
    mejores = []
    for ax, (b, c) in zip(axs.flat, curvas.items()):
        bv = bandas(c)
        ax.fill_between(bc.index, bc.quantile(0.1, axis=1) / 1e6, bc.quantile(0.9, axis=1) / 1e6, color=COLOR_C, alpha=0.18, lw=0)
        ax.fill_between(bv.index, bv.quantile(0.1, axis=1) / 1e6, bv.quantile(0.9, axis=1) / 1e6, color=ctx.color[h], alpha=0.25, lw=0)
        ax.plot(bc.index, bc.median(axis=1) / 1e6, color=COLOR_C, ls=":", lw=1.4)
        ax.plot(bv.index, bv.median(axis=1) / 1e6, color=ctx.color[h], lw=1.8)
        ax.axvline(n_est, color="#999999", ls=":", lw=1)
        ax.set_xlim(0, 15000)
        ax.set_xticks([0, 5000, 10000, 15000])
        ax.set_title(b, fontsize=11, loc="left")
        _ejes(ax)
        mejores.append((float(bv.median(axis=1).loc[:n_est].iloc[-1]) / 1e6, b))
    for ax in axs.flat[len(curvas):]:
        ax.set_visible(False)
    for ax in axs[-1]:
        ax.set_xlabel("N clientes contactados")
    for ax in axs[:, 0]:
        ax.set_ylabel(f"G en {MES} (M$)")
    g_c = float(bc.median(axis=1).loc[:n_est].iloc[-1]) / 1e6
    g, mejor = max(mejores)
    fig.suptitle(f"{h}: con N* = {n_est:,} clientes contactados el control rinde {g_c:.1f} M$ y la mejor variante, {mejor}, {g:.1f} M$; "
                 "banda: P10–P90 entre semillas, punteada: mediana del control", fontsize=13, x=0.01, ha="left", wrap=True)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    return figura(fig, f"curvas_{h}", figuras, ajustar=False)


def curvas_ensamble(ctx: Contexto, fin: pd.DataFrame, ap: pd.DataFrame, a: dict) -> dict[str, list[tuple[int, float, float]]]:
    """{variante: [(K, T, G)]} del control y de las variantes que valen la pena (no pierden y A ≥ `A_VALE`): G es la
    ganancia en `MES` al corte N* del ensamble de las primeras K semillas y T = T_opt + K · T_final. Las mismas
    probabilidades y el mismo corte que `tiempo_igual`, sin bootstrap."""
    if ap.empty:
        return {}
    n_est, t_c = int(ap["n_estrella"].iloc[0]), float(ap["tiempo_total_control_s"].iloc[0])
    vale = [f["variante"] for f in a["filas"] if clase_veredicto(f["veredicto"]) == "ok" and f["A"] is not None and f["A"] >= A_VALE]
    salida = {}
    for b in [lg.CONTROL, *vale]:
        pr = _probs(fin, b, N_SEMILLAS)
        if pr is None:
            continue
        _, baja2, ps = pr
        t_fin = float(fin.loc[fin["variante"] == b, "tiempo_entrenamiento_s"].mean())
        r = None if b == lg.CONTROL else fila(ap, b)
        t_opt = (t_c if r is None else float(r["tiempo_total_s"])) - t_fin
        salida[b] = [(k, t_opt + k * t_fin, ganancia(np.mean(ps[:k], axis=0), baja2, n_est)) for k in range(1, len(ps) + 1)]
    return salida


def _panel_ensamble(ctx: Contexto, curvas: dict, t_c: float, por_tiempo: bool) -> tuple:
    """Figura de 2 × 2 paneles, uno por hipótesis (D16): G del ensamble de las primeras K semillas contra K o contra el
    tiempo T_opt + K · T_final; el control se repite gris en cada panel."""
    fig, axs = plt.subplots(2, 2, figsize=(ANCHO, 7.4), sharex=True, sharey=True, squeeze=False)
    c = curvas[lg.CONTROL]
    for ax, h in zip(axs.flat, list(ctx.hipotesis)[:4]):
        x = lambda pts: [p[1] if por_tiempo else p[0] for p in pts]  # noqa: E731
        ax.plot(x(c), [p[2] / 1e6 for p in c], color=COLOR_C, lw=2.2, label="C (control)", zorder=2)
        propias = [b for b in curvas if b != lg.CONTROL and ctx.hip_de.get(b) == h]
        for j, b in enumerate(propias):
            pts = curvas[b]
            ax.plot(x(pts), [p[2] / 1e6 for p in pts], color=ctx.color[h], lw=1.4, marker=MARCAS[j % len(MARCAS)], ms=4,
                    label=b, zorder=3)
        if por_tiempo:
            ax.axvline(t_c, color=TINTA, ls=":", lw=1.2)
            ax.set_xscale("log")
        ax.set_title(h, fontsize=11, loc="left", color=TINTA)
        if propias:
            ax.legend(frameon=False, fontsize=9, loc="lower right", ncol=2)
        else:
            ax.text(0.5, 0.15, "ninguna variante vale la pena", transform=ax.transAxes, ha="center", fontsize=10, color=COLOR_C)
        _ejes(ax)
    for ax in axs[-1]:
        ax.set_xlabel("tiempo T_opt + K · T_final (s); punteada: T(C)" if por_tiempo else "K: semillas en el ensamble")
    for ax in axs[:, 0]:
        ax.set_ylabel(f"G del ensamble en {MES} (M\\$)")
    return fig, axs


def fig_ensamble(ctx: Contexto, fin: pd.DataFrame, ap: pd.DataFrame, a: dict, figuras: Path | None) -> str:
    """Ensamble según K y según el tiempo, cada una en 2 × 2 paneles por hipótesis con las variantes que valen la pena y
    el control de referencia."""
    curvas = curvas_ensamble(ctx, fin, ap, a)
    if lg.CONTROL not in curvas or len(curvas) < 2:
        return pendiente("faltan las predicciones del control o de las variantes que valen la pena")
    t_c = float(ap["tiempo_total_control_s"].iloc[0])
    en_tiempo = [(g, b) for b, pts in curvas.items() if b != lg.CONTROL for _, t, g in pts if t <= t_c]
    g_c20 = curvas[lg.CONTROL][-1][2]
    if en_tiempo:
        g_m, mejor = max(en_tiempo)
        titulo = (f"Con el tiempo del control ({t_c:,.0f} s), {mejor} ensambla hasta {g_m / 1e6:.1f} M\\$; "
                  f"el control con sus {N_SEMILLAS} semillas llega a {g_c20 / 1e6:.1f} M\\$")
    else:
        titulo = f"Ninguna variante alcanza a ensamblar dentro del tiempo del control ({t_c:,.0f} s)"
    salida = []
    for por_tiempo, nombre in ((False, "ensamble_k"), (True, "ensamble")):
        fig, _ = _panel_ensamble(ctx, curvas, t_c, por_tiempo)
        fig.suptitle(titulo if por_tiempo else f"G del ensamble según K: el control con sus {N_SEMILLAS} semillas llega a "
                     f"{g_c20 / 1e6:.1f} M\\$", fontsize=13, x=0.01, ha="left", wrap=True)
        fig.tight_layout(rect=(0, 0, 1, 0.94))
        salida.append(figura(fig, nombre, figuras, ajustar=False))
    return "\n\n".join(reversed(salida))


def fig_ic_rondas(ctx: Contexto, a: dict, figuras: Path | None, anterior: pd.DataFrame | None = None) -> str:
    """IC 95 % de Δ por variante en las dos rondas: el de la ronda anterior en gris y el de la vigente en el color de su
    hipótesis, con −δ de la vigente punteado."""
    anterior = delta_ronda_anterior() if anterior is None else anterior
    filas = [f for f in a["filas"] if f["d0"] is not None]
    if not filas or not len(anterior):
        return pendiente("ninguna variante tiene Δ en las dos rondas")
    fig, ax = plt.subplots(figsize=(ANCHO, 0.42 * len(filas) + 1.9))
    angostos = 0
    for i, f in enumerate(filas):
        d, lo, hi = (x / 1e6 for x in f["d0"])
        if f["variante"] in anterior.index:
            r = anterior.loc[f["variante"]]
            lo0, hi0 = float(r["delta_g_ic_inf"]) / 1e6, float(r["delta_g_ic_sup"]) / 1e6
            ax.plot([lo0, hi0], [i - 0.17] * 2, color="#9a9a9a", lw=3, solid_capstyle="butt", zorder=2)
            ax.scatter([float(r["delta_g_media"]) / 1e6], [i - 0.17], color="#555555", s=18, zorder=3)
            angostos += (hi - lo) < (hi0 - lo0)
        ax.plot([lo, hi], [i + 0.17] * 2, color=ctx.color[ctx.hip_de[f["variante"]]], lw=3, solid_capstyle="butt", zorder=2)
        ax.scatter([d], [i + 0.17], color=TINTA, s=18, zorder=3)
    ax.axvline(0, color=COLOR_C, lw=0.8)
    ax.axvline(-a["delta"] / 1e6, color=COLOR_C, ls=":", lw=1)
    _filas_por_variante(ax, filas, [_etiqueta(f) for f in filas])
    fig.suptitle(f"El IC de la ronda vigente es más angosto que el de la anterior en {angostos} de {len(filas)} variantes",
                 fontsize=14, x=0.01, ha="left")
    ax.set_xlabel("Δ de la réplica 0 (M\\$, IC 95 %); gris: ronda anterior; punteada: −δ")
    _ejes(ax)
    return figura(fig, "ic_rondas", figuras)


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


def fig_tiempo_igual_ic(ctx: Contexto, a: dict, figuras: Path | None) -> str:
    """D: G del ensamble de K semillas − Ḡ_C, con el IC entre réplicas y el de bootstrap de clientes."""
    filas = []
    for f in a["filas"]:
        tr = f["ti_rep"]
        r = (tr["media"], tr["inf"], tr["sup"]) if tr and tr["n"] >= 2 else None
        if r or f["ti_boot"]:
            filas.append((f, r, f["ti_boot"]))
    if not filas:
        return pendiente("ninguna variante tiene su ensamble a tiempo igual")
    fig, axs, hips = _paneles_por_hipotesis(ctx, [f for f, _, _ in filas], 0.32)
    for ax, h in zip(axs.flat, hips):
        propias = [x for x in filas if x[0]["hipotesis"] == h]
        col = ctx.color[h]
        for i, (_, r, b) in enumerate(propias):
            for t, dy, marca, relleno in ((r, -0.15, "o", col), (b, 0.15, "s", "white")):
                if t:
                    m, lo, hi = (x / 1e6 for x in t[:3])
                    ax.errorbar([m], [i + dy], xerr=[[m - lo], [hi - m]], fmt=marca, ms=4, mfc=relleno, capsize=2, color=col)
        ax.axvline(0, color=COLOR_C, lw=0.8)
        ax.set_yticks(range(len(propias)), [f["variante"] for f, _, _ in propias], fontsize=11)
        ax.set_ylim(len(propias) - 0.5, -0.5)
        ax.set_title(h, fontsize=12, loc="left", color=col, fontweight="bold")
        _ejes(ax)
    for ax in axs[-1]:
        ax.set_xlabel(f"G del ensamble de K semillas en {MES} − Ḡ_C (M$)")
    fig.legend([Line2D([], [], color=TINTA, marker="o", ls=""), Line2D([], [], color=TINTA, marker="s", mfc="white", ls="")],
               ["réplicas (IC t; cada réplica contra Ḡ_C de su réplica)", "bootstrap de clientes (réplica 0)"],
               frameon=False, fontsize=11, loc="lower center", ncol=2)
    intervalos = [t for _, r, b in filas for t in (r or b,)]
    ganan = sum(t[1] > 0 for t in intervalos)
    fig.suptitle(f"A tiempo igual, {ganan} de {len(filas)} variantes superan al control (intervalo entero sobre 0)",
                 fontsize=12, x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0.07, 1, 0.96))
    return figura(fig, "tiempo_igual", figuras, ajustar=False)


def fig_diferencias(ctx: Contexto, a: dict, figuras: Path | None) -> str:
    """G: cada diferencia entre variantes de `replicas.csv` con su IC, por veredicto."""
    rep = a["rep"]
    r = rep[[" - " in v for v in rep.index]] if len(rep) else rep
    if r.empty:
        return pendiente("no hay diferencias entre variantes con réplicas")
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
    ax.set_yticks(range(len(r)), list(r.index), fontsize=11)
    ax.invert_yaxis()
    ax.legend([Line2D([], [], color=COLOR_VEREDICTO[c], marker="o", ls="") for c in textos], list(textos.values()),
              frameon=False, fontsize=11, loc="upper center", bbox_to_anchor=(0.5, -0.06 - 1.2 / (0.4 * len(r) + 1.6)),
              ncol=len(textos))
    ax.set_xlabel("Δ entre variantes (M$), IC entre réplicas" + ("; punteada: −δ" if margen else ""))
    ax.set_title(f"{sum(not (lo <= 0 <= hi) for lo, hi in zip(r['delta_g_ic_inf'], r['delta_g_ic_sup']))} de {len(r)} "
                 "diferencias entre variantes tienen el intervalo fuera de 0", fontsize=11, loc="left")
    _ejes(ax)
    return figura(fig, "diferencias", figuras)


# --- tablas del HTML: resumen y detalle del bloque A, pares y tarjetas del bloque B (D5, D8) ---

#: Notas al pie de las celdas `—` (ninguna celda repite una nota que vale para toda la columna).
NOTAS = {"a": "sin réplicas de optimización: Δ, A y el veredicto salen de la réplica 0 (Δ apareado por semilla).",
         "b": "no aplica: K < 2, en el tiempo del control no entra un segundo modelo final de la variante.",
         "c": "con menos réplicas que Δ: en alguna réplica K < 2."}
CAB_RESUMEN = ("variante", "hipótesis", "R", "Δ [IC 95%] (M$)", "aceleración (×)", "ganancia contra el control")
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


def pestanas_bloque_a(ctx: Contexto, filas_a: list[dict]) -> str:
    """El resumen del bloque A en pestañas (D16): «Lo mejor de cada hipótesis» primero y una por hipótesis. Las pestañas
    van dentro del marcador; el contenido de cada una, sangrado cuatro espacios, como lo pide `pymdownx.tabbed`."""
    def mejor(fs: list[dict]) -> list[dict]:
        """La variante más rápida entre las que valen la pena o, si ninguna vale la pena, la de mayor Δ."""
        vale = [f for f in fs if clase_veredicto(f["veredicto"]) == "ok" and f["A"] is not None and f["A"] >= A_VALE]
        if vale:
            return [max(vale, key=lambda f: f["A"])]
        con_delta = [f for f in fs if delta(f)]
        return [max(con_delta, key=lambda f: delta(f)[0])] if con_delta else []

    por_hipotesis = [(h, [f for f in filas_a if f["hipotesis"] == h]) for h in ctx.hipotesis]
    grupos = [("Lo mejor de cada hipótesis", [m for _, fs in por_hipotesis for m in mejor(fs)])] + por_hipotesis
    sangrar = lambda t: "\n".join("    " + linea if linea else "" for linea in t.splitlines())  # noqa: E731
    return "\n\n".join(f'=== "{titulo}"\n\n' + sangrar(tabla_resumen(fs) if fs else pendiente("sin variantes")) for titulo, fs in grupos)


def tabla_pares(rep: pd.DataFrame) -> str:
    """Las filas de `pares_replicas` con Δ resaltado y el veredicto como etiqueta."""
    filas = [[v, celda_ic((r["delta_g_media"], r["delta_g_ic_inf"], r["delta_g_ic_sup"])), f"{int(r['n_replicas'])}",
              "Welch, sin aparear" if str(r.get("nota", "")).startswith("sin aparear") else "t, apareado",
              celda_veredicto(r["veredicto"])] for v, r in rep.iterrows() if " - " in v]
    return html_tabla(CAB_PARES, filas)


# --- bloques entre marcadores (sitio-legible D4) ---

class MarcadorFaltante(Exception):
    """Un README no tiene el marcador de un bloque que el generador produce."""


def marcadores(nombre: str) -> tuple[str, str]:
    return f"<!-- generado:{nombre} -->", f"<!-- /generado:{nombre} -->"


def bloque(nombre: str, contenido: str, fecha: str) -> str:
    """El bloque completo, con sus marcadores y la línea que avisa que no se edita."""
    ini, fin = marcadores(nombre)
    return f"{ini}\nGenerado por `comun/reporte.py` el {fecha}; no editar.\n\n{contenido.strip()}\n\n{fin}"


def reemplazar_bloques(texto: str, bloques: dict[str, str], archivo: str = "", fecha: str | None = None) -> str:
    """`texto` con el contenido de cada bloque reemplazado y el resto intacto. Falla, sin devolver nada, si falta el
    marcador de apertura o de cierre de alguno."""
    fecha = fecha or f"{datetime.now():%Y-%m-%d}"
    posiciones = {}
    for nombre in bloques:
        ini, fin = marcadores(nombre)
        i = texto.find(ini)
        j = texto.find(fin, i + len(ini)) if i >= 0 else -1
        if i < 0 or j < 0:
            faltante = ini if i < 0 else fin
            raise MarcadorFaltante(f"{archivo}: falta el marcador {faltante}")
        posiciones[nombre] = (i, j + len(fin))
    for nombre, (i, j) in sorted(posiciones.items(), key=lambda kv: -kv[1][0]):
        texto = texto[:i] + bloque(nombre, bloques[nombre], fecha) + texto[j:]
    return texto


def escribir_bloques(plan: list[tuple[Path, dict[str, str]]], archivos: dict[Path, bytes] | None = None,
                     fecha: str | None = None) -> list[Path]:
    """Valida los marcadores de todos los archivos del `plan` y recién entonces escribe los README y las figuras
    (`archivos`): un error no deja la mitad regenerada."""
    nuevos = {ruta: reemplazar_bloques(ruta.read_text(), bl, str(ruta), fecha) for ruta, bl in plan}
    for ruta, texto in nuevos.items():
        ruta.write_text(texto)
    for ruta, datos in (archivos or {}).items():
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_bytes(datos)
    return list(nuevos)


def tiene_marcadores(ruta: Path) -> bool:
    return ruta.is_file() and "<!-- generado:" in ruta.read_text()


def linea_ronda(ap: pd.DataFrame) -> str:
    if ap.empty:
        return "N* pendiente"
    return (f"Final entrenado con {VENTANA}, {N_SEMILLAS} semillas; N* = {int(ap['n_estrella'].iloc[0]):,} clientes contactados (fijo, "
            f"de la ronda anterior); δ = {_m(ap['delta_g_margen'].iloc[0])} M$")


def _plegable(titulo: str, cuerpo: str) -> str:
    """`<details>` con Markdown adentro: el sitio lo interpreta (`md_in_html`) y GitHub lo muestra plegado."""
    return f'<details markdown="1">\n<summary>{html.escape(titulo)}</summary>\n\n{cuerpo.strip()}\n\n</details>'


def _agregador(memo: dict) -> tuple[Contexto, pd.DataFrame, pd.DataFrame, dict]:
    """Contexto, finales, apareado y bloque A del agregador; se calcula una vez por corrida."""
    if "a" not in memo:
        ctx = Contexto(reg.AGREGADOR)
        fin, ap = cargar([reg.CONTROL, *ctx.exps])
        memo["a"] = (ctx, fin, ap, calcular_bloque_a(ctx, fin, ap))
    return memo["a"]


def bloques_control(exp: str, figuras: Path | None, memo: dict) -> dict[str, str]:
    fin, ap = cargar([reg.CONTROL])
    n, completo = estado(lg.CONTROL, fin)
    if ap.empty:
        return {"estado": pendiente("el control no tiene resultados finales")}
    lineas = [f"- {linea_ronda(ap)}.",
              f"- Ḡ_C (réplica 0) = {_m(ap['g_control'].iloc[0])} M$; T_C = {ap['tiempo_total_control_s'].iloc[0]:,.0f} s.",
              f"- Finales del control: {n} de {N_SEMILLAS} semillas" + ("." if completo else " (pendiente).")]
    return {"estado": "\n".join(lineas)}


def bloques_hipotesis(exp: str, figuras: Path | None, memo: dict) -> dict[str, str]:
    ctx = Contexto(exp)
    fin, ap = cargar([reg.CONTROL, *ctx.exps])
    partes = [f"{linea_ronda(ap)}. Vale la pena: no pierde y acelera {A_VALE:g}× o más."]
    if ctx.variantes:
        a = _agregador(memo)[3]
        partes.append(fig_tradeoff(ctx, a, figuras, f"tradeoff_{exp}"))
    partes.append(tabla_variantes(ctx, fin, ap))
    partes += [fig_curvas_ganancia(ctx, h, fin, ap, figuras) for h in ctx.hipotesis]
    partes += [fig_curva_diferencia(ctx, h, fin, ap, figuras) for h in ctx.hipotesis]
    return {"resultado": "\n\n".join(partes)}


def _sin_datos(nombres: tuple[str, ...]) -> dict[str, str]:
    sin = pendiente("el control no tiene sus semillas")
    return {n: sin for n in nombres}


BLOQUES_SAMPLING = ("mapa", "grilla", "desglose", "bloque-a", "fraccion", "ensamble", "tiempo-igual", "semillas")
BLOQUES_ANEXO = ("bloque-a-completo", "varianza", "diferencias", "ic-rondas")
BLOQUES_INICIO = ("hallazgo-tradeoff", "hallazgo-tiempo", "hallazgo-ensamble")


def bloques_sampling(exp: str, figuras: Path | None, memo: dict) -> dict[str, str]:
    ctx, fin, ap, a = _agregador(memo)
    if not a["filas"]:
        return _sin_datos(BLOQUES_SAMPLING)
    return {
        "mapa": fig_tradeoff(ctx, a, figuras),
        "grilla": fig_grilla(ctx, a, figuras),
        "desglose": fig_desglose(ctx, a, figuras),
        "bloque-a": "\n\n".join([referencia_control(a), AVISO_A_HTML, pestanas_bloque_a(ctx, a["filas"]),
                                 _plegable("Detalle del bloque A", html_tabla(CAB_DETALLE, [celdas_detalle(f) for f in a["filas"]], NOTAS))]),
        "fraccion": fig_fraccion(ctx, a, figuras),
        "ensamble": fig_ensamble(ctx, fin, ap, a, figuras),
        "tiempo-igual": tiempo_igual(ctx, fin, ap) + "\n\n" + fig_tiempo_igual_ic(ctx, a, figuras),
        "semillas": fig_semillas(ctx, a, figuras) if len(a["rep"]) else pendiente("ninguna variante tiene réplicas"),
    }


def bloques_anexo(exp: str, figuras: Path | None, memo: dict) -> dict[str, str]:
    ctx, fin, ap, a = _agregador(memo)
    if not a["filas"]:
        return _sin_datos(BLOQUES_ANEXO)
    notas = [f"- `{f['variante']}`: {f['nota']}" for f in a["filas"] if f["nota"]]
    completo = ["#### Bloque A: mismo protocolo\n", referencia_control(a) + "\n", AVISO_A + "\n",
                tabla_md(CAB_A, [celdas_bloque_a(f) for f in a["filas"]])]
    if notas:
        completo += ["Notas:\n", "\n".join(notas) + "\n"]
    if len(a["rep"]):
        completo += ["#### Varianza entre réplicas y entre semillas\n", tabla_md(CAB_VAR, varianza(a["rep"], ctx))]
        if pares_replicas(a["rep"]):
            completo += ["#### Diferencias entre variantes\n", tabla_md(CAB_PARES, pares_replicas(a["rep"]))]
    return {
        "bloque-a-completo": _plegable("Tablas completas del bloque A", "\n".join(completo)),
        "varianza": html_tabla(CAB_VAR, varianza(a["rep"], ctx)) if len(a["rep"]) else pendiente("ninguna variante tiene réplicas"),
        "diferencias": (tabla_pares(a["rep"]) + "\n\n" + fig_diferencias(ctx, a, figuras)
                        if pares_replicas(a["rep"]) else pendiente("no hay diferencias entre variantes con réplicas")),
        "ic-rondas": fig_ic_rondas(ctx, a, figuras),
    }


def bloques_inicio(exp: str, figuras: Path | None, memo: dict) -> dict[str, str]:
    """Una figura por hallazgo de la portada y las tarjetas; las figuras se enlazan desde la raíz del repo."""
    ctx, fin, ap, a = _agregador(memo)
    if not a["filas"]:
        return _sin_datos(BLOQUES_INICIO)
    desde_raiz = lambda md: md.replace("](figuras/", f"](experimentos/{exp}/figuras/")  # noqa: E731
    return {
        "hallazgo-tradeoff": desde_raiz(fig_tradeoff(ctx, a, figuras)),
        "hallazgo-tiempo": desde_raiz(fig_desglose(ctx, a, figuras)),
        "hallazgo-ensamble": desde_raiz(fig_ensamble(ctx, fin, ap, a, figuras)),
    }


def bloques_exploratorios(exp: str, figuras: Path | None, memo: dict) -> dict[str, str]:
    return {"bloque-b": AVISO_B + "\n\n" + lista_b(bloque_b())}


def tarjetas(a: dict, ctx: Contexto, prefijo: str) -> str:
    """Una tarjeta por hipótesis con su veredicto leído de las filas del bloque A (que salen del ledger); `prefijo` es la
    ruta desde la página que las muestra hasta la raíz del repo."""
    out = ['<div class="grid cards" markdown>\n']
    por_exp = {e: _titulo_hipotesis(e) for e in ctx.exps}
    for e, (nombre, titulo) in por_exp.items():
        filas = [f for f in a["filas"] if f["hipotesis"] == nombre]
        if not filas:
            resumen = "pendiente: sin resultados todavía."
        else:
            clases = [clase_veredicto(f["veredicto"]) for f in filas]
            formas = {"ok": ("no pierde", "no pierden"), "pierde": ("pierde", "pierden"),
                      "ind": ("indeterminada", "indeterminadas"), "pend": ("pendiente", "pendientes")}
            partes = [f"{n} {formas[k][n != 1]}" for k in formas if (n := sum(c == k for c in clases))]
            rapidas = [f for f, c in zip(filas, clases) if c == "ok" and f["A"] is not None and f["A"] >= A_VALE]
            resumen = f"{len(filas)} variantes: " + ", ".join(partes) + "."
            if rapidas:
                mejor = max(rapidas, key=lambda f: f["A"])
                resumen += f" La más rápida que no pierde: {mejor['variante']} ({mejor['A']:.1f}×)."
        idea = _idea_hipotesis(e)
        out.append(f"-   **[{nombre} · {titulo}]({prefijo}experimentos/{e}/README.md)**\n\n    ---\n\n"
                   + (f"    {idea}\n\n" if idea else "") + f"    {resumen}\n")
    out.append("</div>")
    return "\n".join(out)


def bloques_tarjetas(prefijo: str):
    def generar_tarjetas(exp: str, figuras: Path | None, memo: dict) -> dict[str, str]:
        ctx, _, _, a = _agregador(memo)
        return {"tarjetas": tarjetas(a, ctx, prefijo) if a["filas"] else pendiente("el control no tiene sus semillas")}
    return generar_tarjetas


def bloques_inicio_y_tarjetas(exp: str, figuras: Path | None, memo: dict) -> dict[str, str]:
    return {**bloques_inicio(exp, figuras, memo), **bloques_tarjetas("")(exp, figuras, memo)}


def destinos(exp: str) -> list[tuple[Path, object]]:
    """(archivo, función que arma sus bloques) de cada archivo que genera `exp`; el primero es su README."""
    base = rutas.experimento(exp)
    if exp == reg.CONTROL:
        return [(base / "README.md", bloques_control)]
    if exp == reg.AGREGADOR:
        return [(base / "README.md", bloques_sampling), (base / "anexo.md", bloques_anexo),
                (base / "exploratorios" / "README.md", bloques_exploratorios),
                (rutas.RAIZ / "index.md", bloques_inicio_y_tarjetas), (rutas.RAIZ / "sitio" / "hipotesis" / "README.md", bloques_tarjetas("../../"))]
    return [(base / "README.md", bloques_hipotesis)]


def planificar(exps: list[str], figuras: Path | None = None) -> tuple[list[tuple[Path, dict[str, str]]], dict[Path, bytes], list[Path]]:
    """(plan, archivos de figuras, archivos omitidos por no tener marcadores todavía). No escribe nada."""
    global DESTINO
    plan, archivos, omitidos, memo = [], {}, [], {}
    for exp in exps:
        for ruta, fn in destinos(exp):
            if not tiene_marcadores(ruta):
                omitidos.append(ruta)
                continue
            DESTINO = Destino(rutas.experimento(exp) / "figuras")
            try:
                plan.append((ruta, fn(exp, figuras, memo)))
                archivos.update(DESTINO.archivos)
            finally:
                DESTINO = None
    return plan, archivos, omitidos


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--exp", "--experimento", dest="exp", help="carpeta de experimentos/ (control, h1, ..., sampling_1)")
    g.add_argument("--todos", action="store_true", help="todos los experimentos del registro")
    p.add_argument("--figuras", type=Path, help="además guarda las figuras como PNG en este directorio")
    a = p.parse_args()
    exps = [reg.CONTROL, *[e for e in reg.duenos() if e != reg.CONTROL], reg.AGREGADOR] if a.todos else [a.exp]
    plan, archivos, omitidos = planificar(exps, a.figuras)
    try:
        escritos = escribir_bloques(plan, archivos)
    except MarcadorFaltante as e:
        raise SystemExit(f"error: {e}; no se escribió nada")
    for ruta in escritos:
        print(ruta)
    for ruta in omitidos:
        print(f"omitido (sin marcadores): {ruta}")


if __name__ == "__main__":
    main()
