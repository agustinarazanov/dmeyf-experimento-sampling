"""Concordancia de género tras `reemplazar_d3.py` (renombrar-brazos D3, paso 3): "los 8 variantes" -> "las 8 variantes".

    python scripts/concordar_d3.py
"""
import re
import subprocess

EXCEPTO = ("openspec/changes/renombrar-brazos/", "openspec/specs/", "scripts/")
NUM = r"(\d+|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|once|doce|ambos)"
REGLAS = [
    (r"\b([Tt])odos las variantes", r"\1odas las variantes"), (r"\b([Tt])odos los variantes", r"\1odas las variantes"),
    (r"\b([Ll])os " + NUM + r" variantes", r"\1as \2 variantes"),
    (r"\b([Ll])os " + NUM + r" de las variantes", r"\1as \2 de las variantes"),
    (r"\b(de|De) los " + NUM + r" variantes", r"\1 las \2 variantes"),
    (r"\b([Dd])e los " + NUM + r" variantes", r"\1e las \2 variantes"),
    (r"\b([Ll])os tres variantes", r"\1as tres variantes"),
    (r"\b([Nn])ingún variante", r"\1inguna variante"), (r"\b([Aa])lgún variante", r"\1lguna variante"),
    (r"\b([Ee])ste variante", r"\1sta variante"), (r"\b([Ee])se variante", r"\1sa variante"),
    (r"\b([Dd])os variantes\b", r"\1os variantes"),
]
for ruta in subprocess.check_output(["git", "ls-files"], text=True).splitlines():
    if ruta.startswith(EXCEPTO):
        continue
    try:
        t = open(ruta, encoding="utf-8").read()
    except (UnicodeDecodeError, FileNotFoundError):
        continue
    n = t
    for pat, rep in REGLAS:
        n = re.sub(pat, rep, n)
    if n != t:
        open(ruta, "w", encoding="utf-8").write(n)

# Correcciones a mano (salida de los grep de concordancia de D3): (archivo, antes, después)
MANUAL = [
    ("experimentos/h2/docs/hipotesis.md", "en estos variantes", "en estas variantes"),
    ("experimentos/h2/docs/hipotesis.md", "**Variante descriptivo `goss`", "**Variante descriptiva `goss`"),
    ("experimentos/sampling_1/docs/bitacora.md", "como variante descriptivo", "como variante descriptiva"),
    ("experimentos/sampling_1/informe/decisiones.md", "Ningún otro variante cumple", "Ninguna otra variante cumple"),
    ("experimentos/sampling_1/informe/decisiones.md", ": los de H1 con A", ": las de H1 con A"),
    ("experimentos/sampling_1/informe/decisiones.md", "y los de H2 que no pierden", "y las de H2 que no pierden"),
    ("experimentos/sampling_1/informe/informe.md", "Diez variantes contra el control, cada uno con su Optuna",
     "Diez variantes contra el control, cada una con su Optuna"),
    ("experimentos/sampling_1/informe/guion.md", "Diez variantes contra el control, cada uno con su Optuna",
     "Diez variantes contra el control, cada una con su Optuna"),
    ("experimentos/sampling_1/informe/informe.md", "las variantes agresivos", "las variantes agresivas"),
    ("openspec/changes/archive/2026-11-02-experimento-sampling-velocidad/design.md", "es una variante descriptivo",
     "es una variante descriptiva"),
    ("openspec/changes/archive/2026-11-02-experimento-sampling-velocidad/specs/ledger-resultados/spec.md",
     "una variante y una semilla ya registrados", "una variante y una semilla ya registradas"),
    ("openspec/changes/archive/2026-11-03-separar-hipotesis/specs/protocolo-experimental/spec.md",
     "variantes propios", "variantes propias"),
    ("tests/test_variantes.py", "variante_viejo", "variante_vieja"),
    ("experimentos/sampling_1/docs/diseno.md", "los diez de H1–H3", "las diez de H1–H3"),
]
for ruta, antes, despues in MANUAL:
    t = open(ruta, encoding="utf-8").read()
    if antes in t:
        open(ruta, "w", encoding="utf-8").write(t.replace(antes, despues))
for ruta, antes, despues in [
    ("experimentos/sampling_1/informe/decisiones.md", "los dos H3, U0.25", "las dos H3, U0.25"),
    ("experimentos/sampling_1/informe/decisiones.md", "los tres más\n", "las tres más\n"),
    ("experimentos/sampling_1/informe/decisiones.md", "Los tres más agresivos, que pierden", "Las tres más agresivas, que pierden"),
    ("experimentos/sampling_1/informe/informe.md", "los tres más agresivos", "las tres más agresivas"),
    ("experimentos/sampling_1/informe/informe.md", "Los dos H3 siguen", "Las dos H3 siguen"),
]:
    t = open(ruta, encoding="utf-8").read()
    if antes in t:
        open(ruta, "w", encoding="utf-8").write(t.replace(antes, despues))
for ruta, antes, despues in [
    ("experimentos/sampling_1/informe/decisiones.md", "\nagresivos quedan por debajo", "\nagresivas quedan por debajo"),
    ("experimentos/sampling_1/informe/informe.md", "El único que mejora de forma notable es U0.5", "La única que mejora de forma notable es U0.5"),
]:
    t = open(ruta, encoding="utf-8").read()
    if antes in t:
        open(ruta, "w", encoding="utf-8").write(t.replace(antes, despues))
for ruta, antes, despues in [
    ("experimentos/h3/docs/hipotesis.md", "como una variante nuevo", "como una variante nueva"),
    ("experimentos/sampling_1/informe/guion.md", "están los dos de H3. Los de muestreo al azar caen a medida que aceleran. Los de bagging",
     "están las dos de H3. Las de muestreo al azar caen a medida que aceleran. Las de bagging"),
    ("experimentos/sampling_1/informe/guion.md", "Los dos H3 quedan arriba del control (+3,9 y +2,8 M$), los agresivos siguen abajo y U0.5 es el que más sube",
     "Las dos H3 quedan arriba del control (+3,9 y +2,8 M$), las agresivas siguen abajo y U0.5 es la que más sube"),
]:
    t = open(ruta, encoding="utf-8").read()
    if antes in t:
        open(ruta, "w", encoding="utf-8").write(t.replace(antes, despues))
