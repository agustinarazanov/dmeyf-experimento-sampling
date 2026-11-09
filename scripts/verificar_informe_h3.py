"""Comprueba que cada número de `experimentos/h3/informe/informe.md` sale de los ledgers o de la tabla del reporte
(cambio `h3-semillas-optuna`, tarea 5.1). Sale con 1 si algo no coincide.

    python -m scripts.verificar_informe_h3

- Filas de tabla copiadas del reporte (punto decimal): tienen que ser idénticas a una línea de
  `sampling_1/informe/tabla_resultados.md`.
- Cualquier otro número del texto (coma decimal, punto de miles, `−` como signo) tiene que coincidir, a la cantidad de
  decimales con que está escrito, con un valor de las fuentes:
  - los números de `tabla_resultados.md`;
  - `h3/ledger/replicas.csv` y `control/ledger/replicas.csv` (en M$ y `frac_entre` en %), más la parte de Optuna en la
    varianza de Ḡ con un estudio y n = 10 o 50 semillas, var_entre / (var_entre + var_dentro / n), y el desvío de Ḡ,
    √(var_entre + var_dentro / n);
  - `h3/ledger/apareado.csv` (réplica 0, en M$, la aceleración y −δ);
  - la mediana de `feature_fraction` de los estudios de `C` y de `U0.1` (réplicas 0…7);
  - las constantes del diseño (`CONSTANTES`).
- No se miran los números dentro de `código`, ni los destinos de enlaces, ni los subíndices `_{…}`, ni los pegados a
  letras (`H3`, `D4`).
"""

from __future__ import annotations

import json
import re
import statistics
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
EXP = RAIZ / "experimentos"
INFORME = EXP / "h3/informe/informe.md"
TABLA = EXP / "sampling_1/informe/tabla_resultados.md"

# N*, R, k = 0…7, 10 y 50 semillas, 80 pares, 7 g.l., IC 95%, meses y año, tasas (en % y en fracción), √10
CONSTANTES = [3300, 8, 0, 7, 10, 50, 80, 95, 2019, 201908, 201910, 5, 25, 0.05, 0.1, 0.25]

NUM_TABLA = re.compile(r"-?\d[\d,]*(?:\.\d+)?")
NUM_TEXTO = re.compile(r"(?<![\w.,@−-])[−-]?\d+(?:\.\d{3})*(?:,\d+)?(?![\w@])")


def _fuentes() -> list[float]:
    valores = [float(x.replace(",", "")) for x in NUM_TABLA.findall(TABLA.read_text())]
    rep = pd.concat([pd.read_csv(EXP / e / "ledger/replicas.csv") for e in ("control", "h3")], ignore_index=True)
    for c in rep.columns:
        if c.startswith(("g_", "delta_g_", "sd_")):
            valores += list(rep[c].dropna() / 1e6)
    valores += list(rep["frac_entre"].dropna() * 100)
    v = rep.dropna(subset=["var_entre"])
    for n in (10, 50):
        total = v["var_entre"] + v["var_dentro"] / n
        valores += list(100 * v["var_entre"] / total) + list(total ** 0.5 / 1e6)
    ap = pd.read_csv(EXP / "h3/ledger/apareado.csv")
    for c in ("g_control", "delta_g_margen", "delta_g_media", "delta_g_ic_inf", "delta_g_ic_sup"):
        valores += list(ap[c] / 1e6)
    valores += list(ap["aceleracion"]) + list(-ap["delta_g_margen"] / 1e6)  # −δ, el umbral de pierde
    for base, dueno_k, est in (("control", "control", "C"), ("h1", "h3", "U0.1")):
        hps = [EXP / base / "ledger/hp" / f"{est}.json"] + sorted((EXP / dueno_k / "ledger/hp").glob(f"{est}@*.json"))
        ff = [json.loads(p.read_text())["hp"]["feature_fraction"] for p in hps]
        if len(ff) != 8:
            raise SystemExit(f"esperaba 8 estudios de {est}, hay {len(ff)}")
        valores.append(statistics.median(ff))
    return valores + CONSTANTES


def _limpiar(linea: str) -> str:
    linea = re.sub(r"`[^`]*`", " ", linea)
    linea = re.sub(r"\]\([^)]*\)", "]", linea)
    return re.sub(r"_\{[^}]*\}", " ", linea)


def _valor(token: str) -> tuple[float, int]:
    t = token.replace("−", "-").replace(".", "").replace(",", ".")
    return float(t), len(t.split(".")[1]) if "." in t else 0


def main() -> int:
    tabla = set(TABLA.read_text().splitlines())
    fuentes = _fuentes()
    errores, revisados, filas = [], 0, 0
    for i, linea in enumerate(INFORME.read_text().splitlines(), 1):
        if linea.startswith("|") and "." in linea and not re.search(r"\d,\d", linea) and not set(linea) <= set("|- "):
            filas += 1
            if linea not in tabla:
                errores.append(f"línea {i}: fila que no está en tabla_resultados.md: {linea}")
            continue
        for token in NUM_TEXTO.findall(_limpiar(linea)):
            x, d = _valor(token)
            revisados += 1
            if not any(abs(v - x) <= 0.5 * 10 ** -d + 1e-9 for v in fuentes):
                errores.append(f"línea {i}: {token} no sale de ninguna fuente")
    for e in errores:
        print("✗", e)
    print(f"{filas} filas copiadas, {revisados} números del texto, {len(errores)} sin fuente")
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main())
