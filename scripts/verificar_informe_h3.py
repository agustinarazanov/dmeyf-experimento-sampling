"""Comprueba que cada número del texto escrito a mano de los `experimentos/hN/README.md` sale de los ledgers o del
bloque `bloque-a-completo` de `experimentos/sampling_1/README.md` (`sitio-legible` 2.7, D9; antes `informe.md` contra
`tabla_resultados.md`). Lo que está entre `<!-- generado:… -->` y `<!-- /generado:… -->` no se revisa: lo escribe el
generador. Sale con 1 si algo no coincide. Con `--informe` revisa solo esos README (repetible).

    python -m scripts.verificar_informe_h3
    python -m scripts.verificar_informe_h3 --informe experimentos/h4/README.md

- Filas de tabla copiadas del reporte (punto decimal): tienen que ser idénticas a una línea del bloque
  `bloque-a-completo`.
- Cualquier otro número del texto (coma decimal, punto de miles, `−` como signo) tiene que coincidir, a la cantidad de
  decimales con que está escrito, con un valor de las fuentes:
  - los números del bloque `bloque-a-completo`;
  - `replicas.csv` de `control`, `h3` y `h4` (en M$ y `frac_entre` en %), más la parte de Optuna en la
    varianza de Ḡ con un estudio y n = 10 o 50 semillas, var_entre / (var_entre + var_dentro / n), y el desvío de Ḡ,
    √(var_entre + var_dentro / n);
  - `apareado.csv` de `h3` y `h4` (réplica 0, en M$, la aceleración y −δ);
  - la mediana de `feature_fraction` de los estudios de `C` y de `U0.1` (réplicas 0…7);
  - las constantes del diseño (`CONSTANTES`).
- No se miran los números dentro de `código`, ni los destinos de enlaces, ni los subíndices `_{…}`, ni los pegados a
  letras (`H3`, `D4`).
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
EXP = RAIZ / "experimentos"
TABLA = EXP / "sampling_1/anexo.md"
BLOQUE = "bloque-a-completo"
GENERADO = re.compile(r"<!-- generado:([\w-]+) -->.*?<!-- /generado:\1 -->", re.S)

# N*, R, k = 0…7, 10 y 50 semillas, 80 pares, 7 g.l., IC 95%, meses y año, tasas (en % y en fracción), √10, el mensaje
# de Zulip de la consigna; desde `final-con-julio-agosto` 4.2, 20 semillas, los meses de las ventanas del final y los
# mensajes de Zulip de los apartamientos (211210 ventana, 211718 reoptimizar)
CONSTANTES = [3300, 8, 0, 7, 10, 50, 80, 95, 2019, 201908, 201910, 5, 25, 0.05, 0.1, 0.25, 208135,
              20, 201903, 201905, 201906, 211210, 211718]
# desde `sitio-legible` 3.3–3.6 las predicciones y el diseño están en el mismo README: 40 trials, 100 iteraciones,
# learning_rate 0,01 (GOSS) y 0,08 (sonda), 30 % de filas de GOSS y 30 % más de costo con 10 réplicas, δ = 0,02 · Ḡ_C,
# δ y Ḡ_C de la ronda 201903–201906 fijados en la regla de réplicas (5,52 y 276,10), semiamplitud ±5,8 con 5 réplicas,
# recorte 8000 de `min_data_in_leaf`, pozo del 35 %, presupuesto de 900 s, celdas y finales de la grilla (64, 1.280, 800),
# el IC de `H4F-0.05` de la ronda anterior citado en la predicción de `H4O-0.5` y las cifras de 201910 del exploratorio
# `validacion_50_semillas` que cita el origen de H4 (+7,19, −2,31, 283,25 y 276,65 M$)
CONSTANTES += [40, 100, 0.01, 0.08, 30, 0.02, 5.52, 276.10, 5.8, 8000, 35, 900, 64, 1280, 800, -0.83, 4.54,
               7.19, -2.31, 283.25, 276.65]
# desde la unión de `tiempos-confiables` con `main` (2b.1) las secciones del 13-nov de diseño están en los README: 21
# estudios `U{r}@k`, 560, 720 y 1.120 finales, 36 estudios de h2, el mensaje de Zulip 212124 del tutor y las filas de
# la receta con bajas de h4 (506.871 filas y 5.312 bajas del train; filas al azar y con bajas por tasa, cocientes, 531)
CONSTANTES += [21, 560, 720, 1120, 36, 212124, 506871, 5312, 253436, 256092, 126718, 130702, 50687, 55468, 25344,
               30390, 1.094, 1.199, 531]

NUM_TABLA = re.compile(r"-?\d[\d,]*(?:\.\d+)?")
NUM_TEXTO = re.compile(r"(?<![\w.,@−-])[−-]?\d+(?:\.\d{3})*(?:,\d+)?(?![\w@])")


def leer_bloque(texto: str, nombre: str) -> str:
    """Lo que hay entre `<!-- generado:nombre -->` y `<!-- /generado:nombre -->`; vacío si falta el bloque."""
    m = re.search(rf"<!-- generado:{re.escape(nombre)} -->(.*?)<!-- /generado:{re.escape(nombre)} -->", texto, re.S)
    return m.group(1) if m else ""


def escrito_a_mano(texto: str) -> list[tuple[int, str]]:
    """(número de línea, línea) de todo lo que está fuera de los bloques generados; las líneas de los bloques se
    reemplazan por vacías para conservar la numeración."""
    sin = GENERADO.sub(lambda m: "\n" * m.group(0).count("\n"), texto)
    return list(enumerate(sin.splitlines(), 1))


def _fuentes(bloque: str) -> list[float]:
    valores = [float(x.replace(",", "")) for x in NUM_TABLA.findall(bloque)]
    rep = pd.concat([pd.read_csv(EXP / e / "ledger/replicas.csv") for e in ("control", "h3", "h4")], ignore_index=True)
    for c in rep.columns:
        if c.startswith(("g_", "delta_g_", "sd_")):
            valores += list(rep[c].dropna() / 1e6)
    valores += list(rep["frac_entre"].dropna() * 100)
    v = rep.dropna(subset=["var_entre"])
    for n in (10, 50):
        total = v["var_entre"] + v["var_dentro"] / n
        valores += list(100 * v["var_entre"] / total) + list(total ** 0.5 / 1e6)
    ap = pd.concat([pd.read_csv(EXP / e / "ledger/apareado.csv") for e in ("h3", "h4")], ignore_index=True)
    for c in ("g_control", "delta_g_margen", "delta_g_media", "delta_g_ic_inf", "delta_g_ic_sup"):
        valores += list(ap[c] / 1e6)
    valores += list(ap["aceleracion"]) + list(-ap["delta_g_margen"] / 1e6)  # −δ, el umbral de pierde
    for base, dueno_k, est in (("control", "control", "C"), ("h1", "h1", "U0.1")):
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
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--informe", type=Path, action="append",
                    help="README a revisar (relativo a la raíz del repo); sin esto, todos los experimentos/hN/README.md")
    pedidos = ap.parse_args().informe
    informes = [i if i.is_absolute() else RAIZ / i for i in pedidos] if pedidos else sorted(EXP.glob("h*/README.md"))
    bloque = leer_bloque(TABLA.read_text(), BLOQUE) if TABLA.exists() else ""
    if not informes or not bloque.strip():
        print("✗ falta el bloque bloque-a-completo en sampling_1/anexo.md o no hay README de hipótesis que revisar")
        return 1
    tabla = set(bloque.splitlines())
    fuentes = _fuentes(bloque)
    errores, revisados, filas = [], 0, 0
    for informe in informes:
        nombre = informe.relative_to(RAIZ) if informe.is_relative_to(RAIZ) else informe
        for i, linea in escrito_a_mano(informe.read_text()):
            if (linea.startswith("|") and re.search(r"\d\.\d", _limpiar(linea)) and not re.search(r"\d,\d", linea)
                    and not set(linea) <= set("|- ")):
                filas += 1
                if linea not in tabla:
                    errores.append(f"{nombre}:{i}: fila que no está en el bloque bloque-a-completo: {linea}")
                continue
            for token in NUM_TEXTO.findall(_limpiar(linea)):
                x, d = _valor(token)
                revisados += 1
                if not any(abs(v - x) <= 0.5 * 10 ** -d + 1e-9 for v in fuentes):
                    errores.append(f"{nombre}:{i}: {token} no sale de ninguna fuente")
    for e in errores:
        print("✗", e)
    print(f"{filas} filas copiadas, {revisados} números del texto, {len(errores)} sin fuente")
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main())
