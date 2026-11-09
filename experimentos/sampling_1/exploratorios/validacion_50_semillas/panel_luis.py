"""Panel de Luis contra `comun.datos` (incorporar-aportes, D7): arma el panel con su SQL y lo compara con el nuestro.

PORTADO sin cambios de lógica: el SQL de `asegurar_panel_desde_cero` del commit 9e1889e (lags, deltas y clase con LEAD
sobre el crudo de 2019, todo en FLOAT). Cambia el entorno: el crudo sale de `comun.datos` y el panel va a
`DATOS_DIR/panel_luis_2019.parquet`, no a Colab ni a Drive.

Compara, como pide D7: columnas (nombres y orden), filas por mes y la huella de cada columna en float32 (sha256 de los
valores en el orden del archivo, con los nulos como NaN). Escribe `panel_d7.json` en la salida de Luis (ledger de
`sampling_1`, sube al bucket). "iguales" exige las tres cosas; el orden cuenta porque `feature_fraction` sortea columnas
por posición.

    python -m experimentos.sampling_1.exploratorios.validacion_50_semillas.panel_luis
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import time
from pathlib import Path

import duckdb
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from comun import baseline as bl
from comun import correr
from comun import datos as dt
from comun import rutas

log = logging.getLogger("panel_luis")

#: Meses del panel de Luis (MESES_HISTORIA + MESES_TRAIN + validación y test en su script); son los nuestros.
MESES_PANEL = [201901, 201902, 201903, 201904, 201905, 201906, 201908, 201910]
SALIDA = rutas.ledger("sampling_1") / "luis"


def ruta_panel_luis() -> Path:
    return bl.DATOS_DIR / "panel_luis_2019.parquet"


def construir_panel_luis(crudo: Path, destino: Path, hilos: int | None = None) -> Path:
    """El SQL de Luis, tal cual (salvo rutas, hilos y memoria)."""
    con = duckdb.connect()
    con.execute("PRAGMA memory_limit='40GB'")
    con.execute(f"PRAGMA threads={hilos or os.cpu_count() or 8}")
    con.execute(f"""
        CREATE OR REPLACE TABLE crudo_2019 AS
        SELECT * FROM read_csv_auto('{crudo}')
        WHERE foto_mes BETWEEN 201901 AND 201912
    """)
    cols_info = con.execute("DESCRIBE crudo_2019").df()
    no_pred = {"numero_de_cliente", "foto_mes", "clase_ternaria"}
    cols_base = [
        r["column_name"] for _, r in cols_info.iterrows()
        if r["column_name"] not in no_pred
        and any(t in r["column_type"].upper() for t in ["INT", "DOUBLE", "FLOAT", "DECIMAL", "REAL", "NUMERIC"])
    ]
    exprs_fe = []
    for c in cols_base:
        exprs_fe.append(f"CAST({c} AS FLOAT) AS {c}")
        exprs_fe.append(f"CAST(LAG({c}, 1) OVER w AS FLOAT) AS {c}__lag1")
        exprs_fe.append(f"CAST(LAG({c}, 2) OVER w AS FLOAT) AS {c}__lag2")
        exprs_fe.append(f"CAST({c} - LAG({c}, 1) OVER w AS FLOAT) AS {c}__delta1")
        exprs_fe.append(f"CAST({c} - LAG({c}, 2) OVER w AS FLOAT) AS {c}__delta2")
    meses_sql = ", ".join(str(m) for m in MESES_PANEL)
    con.execute(f"""
        COPY (
            WITH ventana AS (
                SELECT
                    numero_de_cliente,
                    foto_mes,
                    LEAD(foto_mes, 1) OVER w AS m1,
                    LEAD(foto_mes, 2) OVER w AS m2,
                    {', '.join(exprs_fe)}
                FROM crudo_2019
                WINDOW w AS (PARTITION BY numero_de_cliente ORDER BY foto_mes)
            )
            SELECT
                numero_de_cliente,
                foto_mes,
                CASE
                    WHEN foto_mes IN (201901, 201902, 201911, 201912) THEN NULL
                    WHEN m1 IS NULL OR m1 != foto_mes + 1 THEN 'BAJA+1'
                    WHEN m2 IS NULL OR m2 != foto_mes + 2 THEN 'BAJA+2'
                    ELSE 'CONTINUA'
                END AS clase_ternaria,
                CASE
                    WHEN foto_mes IN (201901, 201902, 201911, 201912) THEN NULL
                    WHEN m1 IS NULL OR m1 != foto_mes + 1 OR m2 IS NULL OR m2 != foto_mes + 2 THEN 1
                    ELSE 0
                END AS y,
                CASE
                    WHEN foto_mes IN (201901, 201902, 201911, 201912) THEN NULL
                    WHEN m1 = foto_mes + 1 AND (m2 IS NULL OR m2 != foto_mes + 2) THEN 1
                    ELSE 0
                END AS es_baja2,
                * EXCLUDE (numero_de_cliente, foto_mes, m1, m2)
            FROM ventana
            WHERE foto_mes IN ({meses_sql})
            ORDER BY foto_mes, numero_de_cliente
        ) TO '{destino}' (FORMAT PARQUET, COMPRESSION ZSTD)
    """)
    con.close()
    return destino


def _valores(col: pa.ChunkedArray) -> np.ndarray:
    """Columna en float32 con nulos como NaN; las de texto, como bytes UTF-8 (con un marcador para los nulos)."""
    if pa.types.is_string(col.type) or pa.types.is_large_string(col.type):
        return np.array([("\0" if v is None else v) for v in col.to_pylist()], dtype=object)
    # sin `safe`: los enteros de más de 2**24 (numero_de_cliente) no entran exactos en float32; las filas se alinean aparte
    return col.cast(pa.float32(), safe=False).to_numpy(zero_copy_only=False).astype(np.float32)


def huella(v: np.ndarray) -> str:
    if v.dtype == object:
        return hashlib.sha256("\n".join(v).encode()).hexdigest()
    v = np.where(np.isnan(v), np.float32(np.nan), v)   # un solo patrón de NaN
    return hashlib.sha256(v.tobytes()).hexdigest()


def _distintas(a: np.ndarray, b: np.ndarray) -> int:
    if a.dtype == object or b.dtype == object:
        return int((a.astype(str) != b.astype(str)).sum())
    return int((~((a == b) | (np.isnan(a) & np.isnan(b)))).sum())


def comparar(nuestro: Path, luis: Path) -> dict:
    """Columnas, filas por mes y huellas de las columnas comunes. Solo compara valores si las filas coinciden."""
    fn, fl = pq.ParquetFile(nuestro), pq.ParquetFile(luis)
    cn, cl = fn.schema_arrow.names, fl.schema_arrow.names
    comunes = [c for c in cn if c in set(cl)]
    r: dict = {
        "columnas": {
            "n_nuestro": len(cn), "n_luis": len(cl),
            "mismos_nombres": set(cn) == set(cl),
            "mismo_orden": cn == cl,
            "solo_nuestro": [c for c in cn if c not in set(cl)],
            "solo_luis": [c for c in cl if c not in set(cn)],
            "primera_posicion_distinta": next((i for i, (a, b) in enumerate(zip(cn, cl)) if a != b), None),
        },
    }
    mes_n = pq.read_table(nuestro, columns=[dt.MES])[dt.MES].to_numpy()
    mes_l = pq.read_table(luis, columns=[dt.MES])[dt.MES].to_numpy()
    filas = lambda m: {int(k): int(v) for k, v in zip(*np.unique(m, return_counts=True))}
    r["filas_por_mes"] = {"nuestro": filas(mes_n), "luis": filas(mes_l), "iguales": filas(mes_n) == filas(mes_l)}
    id_n = pq.read_table(nuestro, columns=[dt.ID])[dt.ID].to_numpy()
    id_l = pq.read_table(luis, columns=[dt.ID])[dt.ID].to_numpy()
    alineadas = len(id_n) == len(id_l) and bool((id_n == id_l).all() and (mes_n == mes_l).all())
    r["filas_alineadas"] = alineadas
    huellas, distintas = {}, {}
    if alineadas:
        for c in comunes:
            a = _valores(pq.read_table(nuestro, columns=[c])[c])
            b = _valores(pq.read_table(luis, columns=[c])[c])
            ha, hb = huella(a), huella(b)
            huellas[c] = ha if ha == hb else {"nuestro": ha, "luis": hb}
            if ha != hb:
                distintas[c] = _distintas(a, b)
    r["huellas"] = {"comparadas": len(huellas), "distintas": distintas, "por_columna": huellas}
    r["iguales"] = bool(r["columnas"]["mismos_nombres"] and r["columnas"]["mismo_orden"]
                        and r["filas_por_mes"]["iguales"] and alineadas and not distintas)
    return r


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--salida", type=Path, default=SALIDA)
    a = p.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    assert MESES_PANEL == bl.MESES_PANEL, "los meses de Luis dejaron de ser los nuestros"
    nuestro, _ = dt.asegurar_panel()
    t0 = time.perf_counter()
    luis = construir_panel_luis(dt.asegurar_crudo(), ruta_panel_luis())
    t_luis = time.perf_counter() - t0
    r = comparar(nuestro, luis)
    commit, sucio = correr.commit_y_sucio()
    r.update(commit=commit, codigo_sucio=sucio, maquina=correr.tipo_de_maquina(), segundos_panel_luis=round(t_luis, 1),
             veredicto="iguales" if r["iguales"] else "distintos")
    a.salida.mkdir(parents=True, exist_ok=True)
    (a.salida / "panel_d7.json").write_text(json.dumps(r, indent=1, ensure_ascii=False))
    print(f"D7: {r['veredicto']} (columnas: mismos nombres {r['columnas']['mismos_nombres']}, mismo orden "
          f"{r['columnas']['mismo_orden']}; filas por mes iguales {r['filas_por_mes']['iguales']}; "
          f"{len(r['huellas']['distintas'])} columnas con huella distinta) -> {a.salida / 'panel_d7.json'}")


if __name__ == "__main__":
    main()
