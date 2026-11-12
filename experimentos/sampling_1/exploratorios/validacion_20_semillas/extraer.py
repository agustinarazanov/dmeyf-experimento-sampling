"""Tablas de los reportes de 20 semillas de Luis (`originales/reporte_h*.html`) a CSV, y su comparación con nuestra
réplica 0 de 10 semillas (`<exp>/ledger/apareado.csv`). Nada se escribe a mano: el README copia de acá.

    python -m experimentos.sampling_1.exploratorios.validacion_20_semillas.extraer
    python -m experimentos.sampling_1.exploratorios.validacion_20_semillas.extraer --verificar

Lo que Luis reportó no tiene código ni ledger: no hay semillas por fila, así que la columna "reproducido" de la
comparación es la de nuestro protocolo (10 semillas oficiales, réplica 0) y no una reproducción de sus 20.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

from comun import rutas

AQUI = Path(__file__).resolve().parent
ORIGINALES = AQUI / "originales"
REPORTADO = AQUI / "resultados" / "reportado_20_semillas.csv"
COMPARACION = AQUI / "resultados" / "comparacion_10_semillas.csv"

# Nombre de Luis -> variante nuestra más cercana. H4_HardNeg usa los hiperparámetros fijos de su script
# (estrategia 7 de validacion_50_semillas); H4H-0.1 es la búsqueda reconstruida, no la misma corrida.
EQUIVALENTE = {"H4_HardNeg": "H4H-0.1", "FastRetrain_H4_50pct": "H4F-0.05"}

class _Tabla(HTMLParser):
    """Filas de la primera `<table>` del reporte."""

    def __init__(self):
        super().__init__()
        self.filas, self._fila, self._celda, self._en, self._listo = [], None, None, False, False

    def handle_starttag(self, tag, attrs):
        if self._listo:
            return
        if tag == "table":
            self._en = True
        elif self._en and tag == "tr":
            self._fila = []
        elif self._en and tag in ("td", "th"):
            self._celda = ""

    def handle_endtag(self, tag):
        if tag == "table" and self._en:
            self._en, self._listo = False, True
        elif self._en and tag in ("td", "th") and self._fila is not None:
            self._fila.append(self._celda.strip())
            self._celda = None
        elif self._en and tag == "tr" and self._fila is not None:
            self.filas.append(self._fila)
            self._fila = None

    def handle_data(self, data):
        if self._celda is not None:
            self._celda += data


def _num(s: str) -> float:
    return float(s.replace("+", "").replace(",", ""))


def reportado() -> list[dict]:
    out = []
    for ruta in sorted(ORIGINALES.glob("reporte_h*.html")):
        p = _Tabla()
        p.feed(ruta.read_text(encoding="utf-8"))
        cab, *filas = p.filas
        assert cab[0] == "brazo" and len(cab) == 11, f"{ruta.name}: cabecera inesperada {cab}"
        exp = ruta.stem.removeprefix("reporte_")
        for f in filas:
            if f[0] == "C":
                continue
            ic = re.findall(r"[-+]?[\d.]+", f[5])
            out.append({"experimento": exp, "variante_luis": f[0], "variante": EQUIVALENTE.get(f[0], f[0]),
                        "semillas": int(f[2]), "g_media": _num(f[3]), "delta_media": _num(f[4]),
                        "ic_inf": _num(ic[0]), "ic_sup": _num(ic[1]), "ganadas": f[6], "tiempo_s": _num(f[7]),
                        "aceleracion": _num(f[8]), "veredicto": f[9], "vale_la_pena": f[10]})
    return out


def control_reportado() -> set[tuple[str, str]]:
    """(G media, T) del control en cada reporte; tienen que ser iguales en los cuatro."""
    vistos = set()
    for ruta in sorted(ORIGINALES.glob("reporte_h*.html")):
        p = _Tabla()
        p.feed(ruta.read_text(encoding="utf-8"))
        vistos |= {(f[3], f[7]) for f in p.filas[1:] if f[0] == "C"}
    return vistos


def comparacion(rep: list[dict]) -> list[dict]:
    out = []
    for r in rep:
        ap = {f["variante"]: f for f in csv.DictReader(open(rutas.RAIZ / "experimentos" / r["experimento"] / "ledger" / "apareado.csv"))}
        a = ap.get(r["variante"])
        fila = {"experimento": r["experimento"], "variante_luis": r["variante_luis"], "variante": r["variante"],
                "delta_luis_20": r["delta_media"], "veredicto_luis_20": r["veredicto"], "tiempo_luis_s": r["tiempo_s"]}
        if a is None:
            fila |= {"delta_nuestro_10": "", "ic_nuestro_10": "", "veredicto_nuestro_10": "sin variante equivalente",
                     "tiempo_nuestro_s": "", "diferencia_delta": ""}
        else:
            d = float(a["delta_g_media"]) / 1e6
            fila |= {"delta_nuestro_10": round(d, 2),
                     "ic_nuestro_10": f"[{float(a['delta_g_ic_inf']) / 1e6:+.2f}, {float(a['delta_g_ic_sup']) / 1e6:+.2f}]",
                     "veredicto_nuestro_10": a["veredicto"], "tiempo_nuestro_s": round(float(a["tiempo_total_s"]), 0),
                     "diferencia_delta": round(r["delta_media"] - d, 2)}
        out.append(fila)
    return out


def _csv(filas: list[dict]) -> str:
    return ",".join(filas[0]) + "\n" + "".join(",".join(f'"{v}"' if "," in str(v) else str(v) for v in f.values()) + "\n" for f in filas)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--verificar", action="store_true", help="falla si los CSV no coinciden con lo que sale de los HTML y los ledgers")
    a = ap.parse_args(argv)
    rep = reportado()
    salidas = {REPORTADO: _csv(rep), COMPARACION: _csv(comparacion(rep))}
    if len(control_reportado()) != 1:
        print(f"✗ el control no es el mismo en los cuatro reportes: {control_reportado()}")
        return 1
    if a.verificar:
        malos = [r.name for r, t in salidas.items() if not r.is_file() or r.read_text() != t]
        for m in malos:
            print(f"✗ {m} no coincide; correr sin --verificar")
        return 1 if malos else 0
    for r, t in salidas.items():
        r.write_text(t)
        print(f"{r.relative_to(rutas.RAIZ)}: {t.count(chr(10)) - 1} filas")
    return 0


if __name__ == "__main__":
    sys.exit(main())
