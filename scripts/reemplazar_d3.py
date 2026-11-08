"""Reemplazo de D3 (renombrar-brazos) sobre `git ls-files`, con las excepciones de D8.

    python scripts/reemplazar_d3.py

Protege el nombre `renombrar-brazos`; no toca los archivos de D8 ni `openspec/specs/` (esas specs cambian al archivar,
con los deltas del cambio); en la bitácora de sampling_1 deja intactas las entradas del renombre (desde `RENOMBRE`).
"""
import re
import subprocess

EXCEPTO = ("openspec/changes/renombrar-brazos/", "openspec/specs/", "scripts/renombrar_columna.py",
           "scripts/reemplazar_d1.py", "scripts/reemplazar_d3.py", "scripts/foto_renombre.py",
           "scripts/verificar_tokens_renombre.py", "comun/ledger.py", "tests/test_ledger.py", "comun/tokens.py")
BITACORA = "experimentos/sampling_1/docs/bitacora.md"
RENOMBRE = "### 2026-11-08 — cierre revisión del grupo 1 de `renombrar-brazos`"
MARCA = "\0RB\0"
exec(open("scripts/reemplazar_d1.py", encoding="utf-8").read().split("for ruta")[0].split('"""', 2)[2])  # REGLAS

def reemplazar(t):
    t = t.replace("renombrar-brazos", MARCA)
    for pat, rep in REGLAS:
        t = re.sub(pat, rep, t)
    return t.replace(MARCA, "renombrar-brazos")

for ruta in subprocess.check_output(["git", "ls-files"], text=True).splitlines():
    if ruta.startswith(EXCEPTO):
        continue
    try:
        t = open(ruta, encoding="utf-8").read()
    except (UnicodeDecodeError, FileNotFoundError):
        continue
    if ruta == BITACORA:
        corte = t.index(RENOMBRE)
        n = reemplazar(t[:corte]) + t[corte:]
    else:
        n = reemplazar(t)
    if n != t:
        open(ruta, "w", encoding="utf-8").write(n)
