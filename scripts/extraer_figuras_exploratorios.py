"""Guarda como PNG los gráficos embebidos (base64) en los reportes HTML de los estudios exploratorios, junto a cada
estudio en `figuras/` (inicio-y-resultados D4). De una sola vez y determinista: los bytes son los del reporte, y correrlo
dos veces no cambia nada.

    python -m scripts.extraer_figuras_exploratorios [--seco]

El nombre del archivo sale del `alt` de la imagen y, si no tiene, del último título (`<h1>`–`<h4>`) que la precede.
"""

from __future__ import annotations

import argparse
import base64
import re
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
EXPLORATORIOS = RAIZ / "experimentos" / "sampling_1" / "exploratorios"

#: reporte HTML -> carpeta del estudio que lo contiene
REPORTES = {
    "validacion_20_semillas/originales/reporte_h1.html": "validacion_20_semillas",
    "validacion_20_semillas/originales/reporte_h2.html": "validacion_20_semillas",
    "validacion_20_semillas/originales/reporte_h3.html": "validacion_20_semillas",
    "validacion_20_semillas/originales/reporte_h4.html": "validacion_20_semillas",
    "validacion_50_semillas/reporte_original.html": "validacion_50_semillas",
    "validacion_50_semillas/resultados/reporte_50_semillas_original.html": "validacion_50_semillas",
}

IMG = re.compile(r"<img\b[^>]*>", re.I)
SRC = re.compile(r"""src=["']data:image/png;base64,([^"']+)["']""", re.I)
ALT = re.compile(r"""alt=["']([^"']*)["']""", re.I)
TITULO = re.compile(r"<h[1-4][^>]*>(.*?)</h[1-4]>", re.S | re.I)


def _slug(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", sin_tildes.lower()).strip("_")


def extraer(html: str) -> list[tuple[str, bytes]]:
    """(nombre, bytes del PNG) de cada imagen embebida; nombre sin repetir dentro del reporte."""
    salida, usados = [], set()
    for m in IMG.finditer(html):
        src = SRC.search(m.group(0))
        if not src:
            continue
        alt = ALT.search(m.group(0))
        titulos = TITULO.findall(html[: m.start()])
        base = _slug(alt.group(1)) if alt and alt.group(1) else _slug(re.sub(r"<[^>]+>", "", titulos[-1])) if titulos else "figura"
        nombre, n = base, 2
        while nombre in usados:
            nombre, n = f"{base}_{n}", n + 1
        usados.add(nombre)
        salida.append((nombre, base64.b64decode(src.group(1))))
    return salida


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--seco", action="store_true", help="solo lista lo que guardaría")
    a = p.parse_args()
    for reporte, estudio in REPORTES.items():
        destino = EXPLORATORIOS / estudio / "figuras"
        for nombre, datos in extraer((EXPLORATORIOS / reporte).read_text()):
            ruta = destino / f"{nombre}.png"
            print(ruta.relative_to(RAIZ), f"({len(datos) // 1024} KB)")
            if not a.seco:
                destino.mkdir(parents=True, exist_ok=True)
                ruta.write_bytes(datos)


if __name__ == "__main__":
    main()
