"""Copia ledger/luis/ a exploratorios/validacion_50_semillas/resultados/ y escribe procedencia.json (4.4).

Copias byte a byte (sin el panel de D7, que no es un resultado de las estrategias). Se corre desde la raíz del repo.
"""
import glob
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys

import lightgbm
import numpy
import pandas

ORIGEN = "experimentos/sampling_1/ledger/luis"
DESTINO = "experimentos/sampling_1/exploratorios/validacion_50_semillas/resultados"

os.makedirs(DESTINO, exist_ok=True)
archivos = {}
for f in sorted(glob.glob(ORIGEN + "/*")):
    if not os.path.isfile(f) or "panel_d7" in f:
        continue
    nombre = os.path.basename(f)
    shutil.copyfile(f, f"{DESTINO}/{nombre}")
    with open(f, "rb") as h:
        archivos[nombre] = {"origen": f, "sha256": hashlib.sha256(h.read()).hexdigest()}

commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
procedencia = {
    "descripcion": (
        "Procedencia de los archivos de resultados/: copias byte a byte de ledger/luis/ (salidas de las VMs "
        "n2-highmem-8 de la fase 6 con validacion.py --estrategia N, más los agregados de validacion.py --agregar "
        "y presupuesto.py hechos en la Mac). Panel de comun.datos; el panel de Luis (D7) va aparte, en "
        "ledger/luis/panel_luis."
    ),
    "commit_de_la_copia": commit,
    "archivos": archivos,
    "versiones_agregados": {
        "python": sys.version.split()[0],
        "plataforma": platform.platform(),
        "lightgbm": lightgbm.__version__,
        "numpy": numpy.__version__,
        "pandas": pandas.__version__,
    },
}
with open(f"{DESTINO}/procedencia.json", "w") as h:
    json.dump(procedencia, h, indent=1, ensure_ascii=False)
print(len(archivos), "archivos copiados")

resumen = pandas.read_csv(f"{DESTINO}/resumen_50_semillas_original.csv")
print(resumen.columns.tolist())
print(resumen.groupby(resumen.columns[0]).size().to_dict())
