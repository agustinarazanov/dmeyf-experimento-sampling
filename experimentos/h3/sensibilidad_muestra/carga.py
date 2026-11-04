"""Carga validada de features y target en float64 (de 05_baseline_inicial.py, sin cambios de lógica).

- Unión 1:1 features-target, cobertura completa y etiquetas no nulas, validada en SQL.
- Las columnas BIGINT pasan a float64 con CAST explícito, después de verificar |x| <= 2^53 (conversión exacta).
  Las DOUBLE quedan igual. Los NULL pasan a NaN (faltante nativo de LightGBM, sin imputar). Nunca float32.
- Las matrices se escriben por bloques en np.memmap respaldados en disco; LightGBM las recibe sin copiarlas.
- El orden de filas es el de los archivos de features leídos en secuencia (un Parquet por mes, ordenado por
  numero_de_cliente). La etiqueta se alinea por (foto_mes, numero_de_cliente).

Las rutas salen de `rutas.py` (DATOS_DIR de `comun.baseline`); las dos únicas diferencias con 05 son esas rutas y
que el mes prohibido es un parámetro del módulo (`MES_PROHIBIDO`), que ganancia_08 apaga para la evaluación final.
"""
from __future__ import annotations

import logging
import time
from pathlib import Path

import numpy as np

from experimentos.h3.sensibilidad_muestra import rutas

log = logging.getLogger("carga")

KEYS = ["numero_de_cliente", "foto_mes"]
TARGET_COLS = {"clase_ternaria", "clase_binaria", "horizonte_completo"}
#: 201910 no se lee salvo en la evaluación final (ganancia_08 lo pone en None).
MES_PROHIBIDO: int | None = 201910
HILOS = 4
FILAS_POR_BLOQUE = 8 * 2048  # vectores de duckdb por bloque de escritura
MAX_EXACTO = 2**53


def q(c: str) -> str:
    return '"' + c.replace('"', '""') + '"'


def memoria(proc) -> dict:
    mi = proc.memory_info()
    return {"rss_mb": round(mi.rss / 2**20, 1),
            "pico_working_set_mb": round(getattr(mi, "peak_wset", 0) / 2**20, 1),
            "pico_commit_privado_mb": round(getattr(mi, "peak_pagefile", 0) / 2**20, 1)}


def archivos(meses: list[int]) -> list[str]:
    assert MES_PROHIBIDO is None or MES_PROHIBIDO not in meses
    return [(rutas.features_dir() / f"features_{m}.parquet").as_posix() for m in meses]


def validar_union(con, meses: list[int]) -> dict:
    """Relación 1:1 features-target, cobertura completa y etiquetas no nulas, en SQL."""
    f, lista = archivos(meses), ", ".join(str(m) for m in meses)
    r = con.execute(f"""
        WITH f AS (SELECT numero_de_cliente, foto_mes FROM read_parquet({f})),
             t AS (SELECT * FROM read_parquet('{rutas.target().as_posix()}') WHERE foto_mes IN ({lista}))
        SELECT
          (SELECT count(*) FROM f),
          (SELECT count(DISTINCT (numero_de_cliente, foto_mes)) FROM f),
          (SELECT count(*) FROM t),
          (SELECT count(DISTINCT (numero_de_cliente, foto_mes)) FROM t),
          (SELECT count(*) FROM f JOIN t USING (numero_de_cliente, foto_mes)),
          (SELECT count(*) FROM f ANTI JOIN t USING (numero_de_cliente, foto_mes)),
          (SELECT count(*) FROM t ANTI JOIN f USING (numero_de_cliente, foto_mes)),
          (SELECT count(*) FROM t WHERE clase_binaria IS NULL OR clase_ternaria IS NULL),
          (SELECT count(*) FROM t WHERE clase_binaria IS DISTINCT FROM
                 CASE clase_ternaria WHEN 'CONTINUA' THEN 0 WHEN 'BAJA+1' THEN 1 WHEN 'BAJA+2' THEN 1 END),
          (SELECT count(*) FROM t WHERE NOT horizonte_completo)""").fetchone()
    n_f, nk_f, n_t, nk_t, n_join, f_sin_t, t_sin_f, nulos, mal, sin_horiz = map(int, r)
    checks = {"features_claves_unicas": n_f == nk_f, "target_claves_unicas": n_t == nk_t,
              "union_1a1_cobertura_completa": n_join == n_f == n_t and f_sin_t == 0 and t_sin_f == 0,
              "sin_etiquetas_nulas": nulos == 0, "binaria_coherente_con_ternaria": mal == 0,
              "horizonte_completo": sin_horiz == 0}
    return {"filas_features": n_f, "filas_target": n_t, "filas_union": n_join,
            "features_sin_target": f_sin_t, "target_sin_features": t_sin_f, "etiquetas_nulas": nulos,
            "binaria_incoherente": mal, "sin_horizonte_completo": sin_horiz, "checks": checks}


def agregar(con, f: list[str], exprs: list[str], lote: int = 100) -> list:
    """Evalúa agregados por lotes de columnas: 760 a la vez exceden el límite de memoria de duckdb."""
    out = []
    for i in range(0, len(exprs), lote):
        out.extend(con.execute(f"SELECT {', '.join(exprs[i:i + lote])} FROM read_parquet({f})").fetchone())
    return out


def perfil_tipos(con, meses: list[int], pred: list[str], tipos: dict) -> dict:
    """Máximo |x| de las BIGINT (para la conversión exacta) y no finitos de las DOUBLE."""
    f = archivos(meses)
    big = [c for c in pred if tipos[c] == "BIGINT"]
    dbl = [c for c in pred if tipos[c] == "DOUBLE"]
    otros = sorted({tipos[c] for c in pred} - {"BIGINT", "DOUBLE"})
    if otros:
        raise RuntimeError(f"tipos no previstos entre los predictores: {otros}")
    r = agregar(con, f, [f"max(abs({q(c)}))" for c in big])
    max_abs = {c: (None if v is None else int(v)) for c, v in zip(big, r)}
    r = agregar(con, f, [f"count(*) FILTER (WHERE isnan({q(c)}) OR isinf({q(c)}))" for c in dbl])
    no_finitos = {c: int(v) for c, v in zip(dbl, r) if v}
    nulos = sum(agregar(con, f, [f"count(*) - count({q(c)})" for c in pred]))
    peor = max((v for v in max_abs.values() if v is not None), default=0)
    return {"bigint": len(big), "double": len(dbl), "max_abs_bigint": peor,
            "bigint_exacto_en_float64": peor <= MAX_EXACTO,
            "double_no_finitos": no_finitos, "celdas_null_a_nan": int(nulos)}


def cargar(con, meses: list[int], pred: list[str], tipos: dict, destino: Path) -> tuple[np.memmap, np.ndarray, np.ndarray]:
    """Escribe la matriz float64 (filas x 760) en un memmap, por bloques, sin ordenar ni copiar todo en RAM."""
    f = archivos(meses)
    n = con.execute(f"SELECT count(*) FROM read_parquet({f})").fetchone()[0]
    X = np.lib.format.open_memmap(destino, mode="w+", dtype=np.float64, shape=(n, len(pred)))
    expr = ", ".join(f"CAST({q(c)} AS DOUBLE) AS {q(c)}" if tipos[c] == "BIGINT" else q(c) for c in pred)
    con.execute("SET threads = 1")  # flujo secuencial: menos memoria y orden de archivos garantizado
    rel = con.execute(f"SELECT numero_de_cliente, foto_mes, {expr} FROM read_parquet({f})")
    cli = np.empty(n, np.int64)
    mes = np.empty(n, np.int64)
    i, b, t = 0, 0, time.perf_counter()
    while True:
        df = rel.fetch_df_chunk(FILAS_POR_BLOQUE // 2048)
        if df.empty:
            break
        k = len(df)
        cli[i:i + k] = df["numero_de_cliente"].to_numpy(np.int64)
        mes[i:i + k] = df["foto_mes"].to_numpy(np.int64)
        bloque = df[pred].to_numpy(dtype=np.float64, na_value=np.nan)
        if bloque.dtype != np.float64:
            raise RuntimeError(f"tipo inesperado en el bloque: {bloque.dtype}")
        X[i:i + k] = bloque
        i, b = i + k, b + 1
        del df, bloque
        if b % 8 == 0 or i == n:
            log.info("  %s: %s/%s filas (%.0f%%) en %.0fs", destino.name, f"{i:,}", f"{n:,}", 100 * i / n,
                     time.perf_counter() - t)
    if i != n:
        raise RuntimeError(f"se leyeron {i} filas de {n}")
    del rel
    con.execute(f"SET threads = {HILOS}")
    X.flush()
    return X, cli, mes


def etiquetas(con, meses: list[int], cli: np.ndarray, mes: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Alinea clase_binaria y clase_ternaria con el orden de las filas de X, por ambas claves."""
    lista = ", ".join(str(m) for m in meses)
    t = con.execute(f"SELECT numero_de_cliente, foto_mes, clase_binaria, clase_ternaria "
                    f"FROM read_parquet('{rutas.target().as_posix()}') WHERE foto_mes IN ({lista}) "
                    f"ORDER BY foto_mes, numero_de_cliente").fetchnumpy()
    if cli.max() >= 10**10 or np.asarray(t["numero_de_cliente"]).max() >= 10**10:
        raise RuntimeError("numero_de_cliente no entra en la clave compuesta")
    clave_t = np.asarray(t["foto_mes"], np.int64) * 10**10 + np.asarray(t["numero_de_cliente"], np.int64)
    clave_x = mes * 10**10 + cli
    pos = np.searchsorted(clave_t, clave_x)
    pos = np.minimum(pos, len(clave_t) - 1)
    if not (np.all(np.diff(clave_t) > 0) and len(clave_t) == len(clave_x) and np.array_equal(clave_t[pos], clave_x)
            and len(np.unique(pos)) == len(pos)):
        raise RuntimeError("las claves de features y target no se alinean 1:1")
    yb = np.asarray(t["clase_binaria"])
    if np.ma.is_masked(yb):
        raise RuntimeError("hay etiquetas nulas")
    return np.asarray(yb, np.int8)[pos], np.asarray(t["clase_ternaria"], object)[pos]
