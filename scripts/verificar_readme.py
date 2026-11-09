"""Comprueba que los números del README salen de `sampling_1/informe/tabla_resultados.md` y que sus enlaces existen
(cambio `renombrar-brazos`, tarea 4.1; desde `h3-semillas-optuna` 5.2 la fuente es la tabla del reporte y no la del
informe). Sale con 1 si algo no coincide.

    python -m scripts.verificar_readme

- Números del texto (fuera de bloques de código, de `código` y de destinos de enlaces, y sin contar los pegados a letras,
  como `H3` o `h4`): cada uno, leído con coma decimal y punto de miles, tiene que estar en la tabla con los mismos
  decimales. Las excepciones son identificadores que no son resultados y están en `NO_RESULTADOS`.
- Enlaces relativos `[texto](ruta)`: la ruta (sin `#ancla`, con `%20` como espacio) tiene que existir.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote

RAIZ = Path(__file__).resolve().parent.parent
README = RAIZ / "README.md"
TABLA = RAIZ / "experimentos/sampling_1/informe/tabla_resultados.md"

# año del curso y de los datos, mensaje de Zulip, versión de Python, fases de las VMs, pasos 07 y 08 de Martín y las 50
# semillas de la pregunta de Luis
NO_RESULTADOS = {"2026", "2019", "208986", "3,14", "1", "4", "5", "07", "08", "50"}

NUM_TABLA = re.compile(r"\d[\d,]*(?:\.\d+)?")
NUM_TEXTO = re.compile(r"(?<![\w.,@−-])[−-]?\d+(?:\.\d{3})*(?:,\d+)?(?![\w@])")
ENLACE = re.compile(r"\]\(([^)\s]+)\)")


def _texto(readme: str) -> str:
    """El README sin bloques de código, sin `código` y sin destinos de enlaces."""
    salida, codigo = [], False
    for linea in readme.splitlines():
        if linea.startswith("```"):
            codigo = not codigo
            continue
        if not codigo:
            salida.append(re.sub(r"\]\([^)]*\)", "]", re.sub(r"`[^`]*`", " ", linea)))
    return "\n".join(salida)


def _en_tabla(token: str, tabla: set[float]) -> bool:
    t = token.replace("−", "").replace("-", "").replace(".", "").replace(",", ".")
    d = len(t.split(".")[1]) if "." in t else 0
    return any(round(v, d) == float(t) for v in tabla)


def main() -> int:
    readme = README.read_text()
    tabla = {float(x.replace(",", "")) for x in NUM_TABLA.findall(TABLA.read_text())}
    errores: list[str] = []

    numeros = sorted(set(NUM_TEXTO.findall(_texto(readme))))
    for n in numeros:
        if n not in NO_RESULTADOS and not _en_tabla(n, tabla):
            errores.append(f"número del texto que no está en tabla_resultados.md: {n}")

    enlaces = [e for e in ENLACE.findall(readme) if not re.match(r"[a-z]+://", e)]
    for e in enlaces:
        ruta = unquote(e.split("#", 1)[0])
        if ruta and not (RAIZ / ruta).exists():
            errores.append(f"enlace roto: {e}")

    print(f"{len(numeros)} números del texto, {len(enlaces)} enlaces")
    for err in errores:
        print("✗", err)
    if not errores:
        print("✓ todos los números están en tabla_resultados.md y todos los enlaces existen")
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main())
