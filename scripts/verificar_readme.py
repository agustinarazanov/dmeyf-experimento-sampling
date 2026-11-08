"""Comprueba que los números del README salen de `sampling_1/informe/informe.md` y que sus enlaces existen
(cambio `renombrar-brazos`, tarea 4.1). Sale con 1 si algo no coincide.

    python -m scripts.verificar_readme

- Tabla de resultados: cada fila del README (Δ, IC, A, veredicto) tiene que ser idéntica a la de la variante en el
  informe, y tienen que estar las mismas variantes.
- Números sueltos del texto (con coma decimal o con signo, como `8,41` o `+6,05`): cada uno tiene que aparecer en el
  informe.
- Enlaces relativos `[texto](ruta)`: la ruta (sin `#ancla`, con `%20` como espacio) tiene que existir.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote

RAIZ = Path(__file__).resolve().parent.parent
README = RAIZ / "README.md"
INFORME = RAIZ / "experimentos/sampling_1/informe/informe.md"

NUMERO = re.compile(r"[+−-]?\d+,\d+|[+−]\d+(?:[.,]\d+)?")
ENLACE = re.compile(r"\]\(([^)\s]+)\)")


def _filas(texto: str) -> dict[str, str]:
    """Filas de la tabla de resultados (la que empieza con `| variante | Δ media`), por variante."""
    filas, dentro = {}, False
    for linea in texto.splitlines():
        if linea.startswith("| variante | Δ media"):
            dentro = True
            continue
        if dentro:
            if not linea.startswith("|"):
                break
            celdas = [c.strip() for c in linea.strip("|").split("|")]
            if set(celdas[0]) <= {"-"}:
                continue
            filas[celdas[0]] = linea.strip()
    return filas


def _sin_tabla_ni_codigo(texto: str) -> str:
    """El texto del README sin las líneas de tablas ni los bloques de código."""
    salida, codigo = [], False
    for linea in texto.splitlines():
        if linea.startswith("```"):
            codigo = not codigo
            continue
        if codigo or linea.startswith("|"):
            continue
        salida.append(linea)
    return "\n".join(salida)


def main() -> int:
    readme, informe = README.read_text(), INFORME.read_text()
    errores: list[str] = []

    filas_r, filas_i = _filas(readme), _filas(informe)
    if not filas_i:
        errores.append("no encontré la tabla de resultados en informe.md")
    if set(filas_r) != set(filas_i):
        errores.append(f"variantes distintas: README {sorted(filas_r)} / informe {sorted(filas_i)}")
    for v in sorted(set(filas_r) & set(filas_i)):
        if filas_r[v] != filas_i[v]:
            errores.append(f"fila {v} distinta:\n  README:  {filas_r[v]}\n  informe: {filas_i[v]}")

    texto = _sin_tabla_ni_codigo(readme)
    numeros = NUMERO.findall(texto)
    for n in sorted(set(numeros)):
        if n not in informe:
            errores.append(f"número del texto que no está en informe.md: {n}")

    enlaces = [e for e in ENLACE.findall(readme) if not re.match(r"[a-z]+://", e)]
    for e in enlaces:
        ruta = unquote(e.split("#", 1)[0])
        if ruta and not (RAIZ / ruta).exists():
            errores.append(f"enlace roto: {e}")

    print(f"{len(filas_r)} filas de la tabla, {len(set(numeros))} números del texto, {len(enlaces)} enlaces")
    for err in errores:
        print("✗", err)
    if not errores:
        print("✓ todo coincide con informe.md y todos los enlaces existen")
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main())
