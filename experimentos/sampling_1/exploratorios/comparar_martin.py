"""Compara las salidas nuevas de 07 y 08 (ledger/martin, D5) con `procedencia.json` de la H3 de Martín.

Por archivo: sha256 con fin de línea LF contra `sha256_lf`, y columna por columna (las de tiempo se informan aparte).

    python -m experimentos.sampling_1.exploratorios.comparar_martin
"""

from __future__ import annotations

import csv
import hashlib
import json

from comun import rutas

REF = rutas.EXPERIMENTOS / "h3" / "sensibilidad_muestra" / "resultados"
MARTIN = rutas.ledger("sampling_1") / "martin"
TIEMPOS = {"tiempo_busqueda_s", "tiempo_ajuste_completo_reutilizado_s", "segundos_prediccion"}


def nueva(nombre_script: str, archivo: str):
    """El archivo de la corrida más reciente que lo tiene."""
    hallados = sorted((MARTIN / nombre_script[:2] / nombre_script).glob(f"*/{archivo}"))
    return hallados[-1]


def comparar() -> list[dict]:
    proc = json.loads((REF / "procedencia.json").read_text())
    filas = []
    for nombre, info in proc["archivos"].items():
        nuevo = nueva(info["script"], info["archivo"])
        sha = hashlib.sha256(nuevo.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        a = list(csv.reader((REF / nombre).open(newline="")))
        b = list(csv.reader(nuevo.open(newline="")))
        distintas = {a[0][j] for x, y in zip(a, b) for j, (u, v) in enumerate(zip(x, y)) if u != v}
        filas.append({
            "archivo": nombre, "corrida": nuevo.parent.name, "sha256_igual": sha == info["sha256_lf"],
            "misma_forma": len(a) == len(b) and a[0] == b[0],
            "columnas_distintas": sorted(distintas), "solo_tiempos": distintas <= TIEMPOS,
        })
    return filas


if __name__ == "__main__":
    for f in comparar():
        print(json.dumps(f, ensure_ascii=False))
