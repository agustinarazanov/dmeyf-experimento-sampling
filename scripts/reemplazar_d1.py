"""Reemplazo de D1 (renombrar-brazos) sobre los archivos que se pasan; reglas de lo específico a lo general.

    python scripts/reemplazar_d1.py archivo...
"""
import re
import sys

REGLAS = [
    (r"\bdel brazo\b", "de la variante"), (r"\bal brazo\b", "a la variante"),
    (r"\bEl brazo\b", "La variante"), (r"\bel brazo\b", "la variante"),
    (r"\bUn brazo\b", "Una variante"), (r"\bun brazo\b", "una variante"),
    (r"\bLos brazos\b", "Las variantes"), (r"\blos brazos\b", "las variantes"),
    (r"BRAZOS", "VARIANTES"), (r"Brazos", "Variantes"), (r"Brazo", "Variante"),
    (r"brazos", "variantes"), (r"brazo", "variante"),
]

for ruta in sys.argv[1:]:
    t = orig = open(ruta, encoding="utf-8").read()
    for pat, rep in REGLAS:
        t = re.sub(pat, rep, t)
    if t != orig:
        open(ruta, "w", encoding="utf-8").write(t)
