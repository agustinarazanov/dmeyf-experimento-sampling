"""Comprueba que la sección `## Predicción` de cada README de `control` y `h1` a `h4` es igual, byte a byte, a la del
commit base `BASE` (el último antes de `informe-por-ejes`): las predicciones se escribieron antes de los resultados y no
se tocan. La sección va desde `## Predicción` hasta el siguiente `## `. Sale con 1 nombrando el archivo que difiere.

    python -m scripts.verificar_predicciones
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
BASE = "1a5c0da1"
READMES = [f"experimentos/{e}/README.md" for e in ("control", "h1", "h2", "h3", "h4")]
SECCION = re.compile(r"^## Predicción[^\n]*\n.*?(?=^## |\Z)", re.S | re.M)


def seccion(texto: str) -> str | None:
    m = SECCION.search(texto)
    return m.group(0) if m else None


def texto_base(ruta: str) -> str:
    return subprocess.run(
        ["git", "show", f"{BASE}:{ruta}"], cwd=RAIZ, check=True, capture_output=True, text=True
    ).stdout


def main() -> int:
    errores = []
    for ruta in READMES:
        actual = seccion((RAIZ / ruta).read_text())
        base = seccion(texto_base(ruta))
        if base is None:
            errores.append(f"{ruta}: el commit base {BASE} no tiene `## Predicción`")
        elif actual != base:
            errores.append(f"{ruta}: la sección Predicción difiere de la del commit {BASE}")
    for e in errores:
        print(e)
    if not errores:
        print(f"verificar_predicciones: {len(READMES)} secciones Predicción iguales a las de {BASE}")
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main())
