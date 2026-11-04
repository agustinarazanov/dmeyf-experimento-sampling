"""Insumos de sensibilidad_07 y ganancia_08 desde el crudo autorizado: Parquet 2019, target y features.

Reemplaza a 01-04 del repo de origen con lo mínimo que hace falta para regenerar exactamente los mismos datos:

  1. 2019 tipado. Del crudo (`comun.datos.asegurar_crudo`, 201901-202108) se leen como texto las filas de
     201901-201912 y cada columna se convierte con el esquema versionado en `referencia/esquema_2019.json` (el que
     infirió 02: BIGINT si todos los valores no vacíos son enteros exactos; si no, DOUBLE; nunca float32). Un
     BIGINT escrito como real (p. ej. `1.2e+07`, de R/fwrite) pasa por DOUBLE sólo si es entero exacto con
     |x| <= 2^53. Las celdas vacías quedan NULL. El 4-nov-2026 se comprobó que las 1.563.565 filas de 2019 del
     crudo, tipadas así, son idénticas al Parquet de 2019 que usaron las corridas (EXCEPT ALL en ambos sentidos).
  2. Target (03, regla de la competencia 1): sobre la grilla clientes x meses de 2019, BAJA+1 si falta en t+1;
     BAJA+2 si está en t+1 y falta en t+2; CONTINUA si está en ambos; NULL sin horizonte. clase_binaria = 1 para
     BAJA+1 y BAJA+2. Sólo lee numero_de_cliente y foto_mes.
  3. Features (04): lag_k = k-ésima observación previa del cliente (lag OVER PARTITION BY numero_de_cliente ORDER
     BY foto_mes), delta_k = x - lag_k, k = 1, 2, sobre las 152 columnas originales, que se conservan; tipos del
     origen, sin imputar. 760 predictores en el orden `originales, _lag1, _delta1, _lag2, _delta2`. Un Parquet por
     mes ordenado por numero_de_cliente, y `manifiesto.json` con claves y predictores.

Verificaciones: esquema y orden de columnas del crudo, tokens no numéricos, enteros no exactos, filas por mes,
claves únicas, cobertura del target, BAJA+2 por mes contra la referencia, sha256 de la lista de predictores y huella
por mes de las features (`bit_xor(hash(col))`, la de 04; depende de la versión de duckdb, con 1.5.5 bloquea). La
verificación definitiva de los datos son las huellas sha256 de X, y y claves que calculan 07 y 08 al cargar.

Nunca sobrescribe: escribe en `<destino>.tmp-<pid>` y publica con rename sólo si todo pasa.

    python -m experimentos.h3.sensibilidad_muestra.insumos [--crudo RUTA] [--solo-verificar]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import shutil
import sys
import time
from pathlib import Path

import duckdb

from comun import datos as cd
from experimentos.h3.sensibilidad_muestra import rutas

log = logging.getLogger("insumos")

KEYS = ["numero_de_cliente", "foto_mes"]
SUFIJOS = ["lag1", "delta1", "lag2", "delta2"]
MESES = [201901 + i for i in range(12)]
INT_RE = r"-?[0-9]+"
MAX_EXACTO = 2**53
ESQUEMA = rutas.REFERENCIA / "esquema_2019.json"
HUELLAS = rutas.REFERENCIA / "huellas_datos.json"
DUCKDB_REFERENCIA = "1.5.5"

# SQL de 03_construir_target.py, sin cambios.
SQL_TARGET = """
WITH crudo AS (
    SELECT numero_de_cliente, foto_mes FROM read_parquet(?)
), periodos AS (
    SELECT DISTINCT foto_mes FROM crudo
), clientes AS (
    SELECT DISTINCT numero_de_cliente FROM crudo
), todo AS (
    SELECT numero_de_cliente, foto_mes FROM clientes CROSS JOIN periodos
), presencia AS (
    SELECT
        t.numero_de_cliente
        , t.foto_mes
        , if(c.numero_de_cliente IS NULL, 0, 1) AS mes_0
    FROM todo t
    LEFT JOIN crudo c USING (numero_de_cliente, foto_mes)
), clase AS (
    SELECT
        *
        , lead(mes_0, 1) OVER (PARTITION BY numero_de_cliente ORDER BY foto_mes) AS mes_1
        , lead(mes_0, 2) OVER (PARTITION BY numero_de_cliente ORDER BY foto_mes) AS mes_2
    FROM presencia
)
SELECT
    numero_de_cliente
    , foto_mes
    , CASE
        WHEN mes_1 = 0 THEN 'BAJA+1'
        WHEN mes_1 = 1 AND mes_2 = 0 THEN 'BAJA+2'
        WHEN mes_1 = 1 AND mes_2 = 1 THEN 'CONTINUA'
        ELSE NULL
      END AS clase_ternaria
    , CASE
        WHEN mes_1 = 0 OR (mes_1 = 1 AND mes_2 = 0) THEN 1
        WHEN mes_1 = 1 AND mes_2 = 1 THEN 0
        ELSE NULL
      END::TINYINT AS clase_binaria
    , (mes_1 IS NOT NULL AND mes_2 IS NOT NULL) AS horizonte_completo
FROM clase
WHERE mes_0 = 1
ORDER BY foto_mes, numero_de_cliente
"""


# --- features (pipeline_competencia02/features.py del repo de origen, sin cambios) -------------------


def q(c: str) -> str:
    return '"' + c.replace('"', '""') + '"'


def nombres(cols: list[str]) -> list[str]:
    return cols + [f"{c}_{s}" for s in SUFIJOS for c in cols]


def crear_prev(con, src: str):
    """Mes de la 1ª y 2ª observación previa de cada fila (sólo claves)."""
    con.execute(f"""
        CREATE OR REPLACE TEMP TABLE prev AS
        SELECT numero_de_cliente, foto_mes,
               lag(foto_mes, 1) OVER w AS m1,
               lag(foto_mes, 2) OVER w AS m2
        FROM {src}
        WINDOW w AS (PARTITION BY numero_de_cliente ORDER BY foto_mes)""")


def sql_mes(src: str, cols: list[str], mes: int) -> str:
    derived = []
    for s, alias in (("lag1", "p1"), ("delta1", "p1"), ("lag2", "p2"), ("delta2", "p2")):
        for c in cols:
            if s.startswith("lag"):
                derived.append(f"{alias}.{q(c)} AS {q(c + '_' + s)}")
            else:
                derived.append(f"(c.{q(c)} - {alias}.{q(c)}) AS {q(c + '_' + s)}")
    orig = ", ".join(f"c.{q(c)}" for c in cols)
    return f"""
        WITH k AS (SELECT * FROM prev WHERE foto_mes = {mes}),
        p1 AS (SELECT s.* FROM {src} s
               SEMI JOIN (SELECT numero_de_cliente, m1 AS foto_mes FROM k WHERE m1 IS NOT NULL) x
               USING (numero_de_cliente, foto_mes)),
        p2 AS (SELECT s.* FROM {src} s
               SEMI JOIN (SELECT numero_de_cliente, m2 AS foto_mes FROM k WHERE m2 IS NOT NULL) x
               USING (numero_de_cliente, foto_mes))
        SELECT c.numero_de_cliente, c.foto_mes, {orig}, {', '.join(derived)}
        FROM {src} c
        JOIN k USING (numero_de_cliente, foto_mes)
        LEFT JOIN p1 ON p1.numero_de_cliente = c.numero_de_cliente AND p1.foto_mes = k.m1
        LEFT JOIN p2 ON p2.numero_de_cliente = c.numero_de_cliente AND p2.foto_mes = k.m2
        WHERE c.foto_mes = {mes}
        ORDER BY c.numero_de_cliente"""


# --- utilidades -------------------------------------------------------------------------------------


def conectar(tmp: Path, memoria: str = "4GB"):
    con = duckdb.connect()
    con.execute(f"SET temp_directory = '{tmp.as_posix()}'")
    con.execute(f"SET memory_limit = '{memoria}'")
    con.execute("SET threads = 4")
    con.execute("SET preserve_insertion_order = true")
    return con


def publicar(tmp: Path, destino: Path, intentos: int = 30) -> None:
    """rename con reintentos: el antivirus puede tener abiertos los archivos recién escritos."""
    if destino.exists():
        raise RuntimeError(f"{destino} apareció durante la ejecución; no se sobrescribe")
    for i in range(intentos):
        try:
            os.rename(tmp, destino)
            return
        except OSError:
            if i == intentos - 1:
                raise
            time.sleep(2)


def huella_xor(con, archivo: Path, cols: list[str]) -> tuple[int, str]:
    """bit_xor(hash(col)) de todas las columnas, combinado con xor (04, leer_completo)."""
    hashes = ", ".join(f"bit_xor(hash({q(c)}))" for c in cols)
    r = con.execute(f"SELECT count(*), {hashes} FROM read_parquet('{archivo.as_posix()}')").fetchone()
    h = 0
    for v in r[1:]:
        h ^= int(v)
    return int(r[0]), f"{h:016x}"


# --- pasos ------------------------------------------------------------------------------------------


def paso_2019(crudo: Path, destino: Path, esquema: dict, duck_tmp: Path) -> dict:
    cols = [c for c, _ in esquema["columnas"]]
    tipos = dict(esquema["columnas"])
    con = conectar(duck_tmp)
    cab = [r[0] for r in con.execute(f"DESCRIBE SELECT * FROM read_csv('{crudo.as_posix()}', all_varchar=true) "
                                     f"LIMIT 0").fetchall()]
    if cab != cols:
        raise RuntimeError("las columnas del crudo no son las del esquema de 2019 (nombres u orden)")
    spec = "{" + ", ".join(f"'{c}': 'VARCHAR'" for c in cols) + "}"
    con.execute(f"""CREATE TEMP VIEW texto AS SELECT * FROM read_csv('{crudo.as_posix()}', header=true, nullstr='',
                    auto_detect=false, columns={spec}) WHERE CAST(foto_mes AS BIGINT) BETWEEN 201901 AND 201912""")
    # tokens: no numéricos en cualquier columna; en BIGINT, reales que no sean enteros exactos
    malos = []
    for i in range(0, len(cols), 40):
        exprs = []
        for c in cols[i:i + 40]:
            d = f"try_cast({q(c)} AS DOUBLE)"
            cond = f"{q(c)} IS NOT NULL AND {d} IS NULL"
            if tipos[c] == "BIGINT":
                cond += (f" OR ({q(c)} IS NOT NULL AND NOT regexp_full_match({q(c)}, '{INT_RE}') AND NOT "
                         f"coalesce({d} = trunc({d}) AND abs({d}) <= {MAX_EXACTO}, false))"
                         f" OR (regexp_full_match({q(c)}, '{INT_RE}') AND try_cast({q(c)} AS BIGINT) IS NULL)")
            exprs.append(f"count(*) FILTER (WHERE {cond})")
        r = con.execute(f"SELECT {', '.join(exprs)} FROM texto").fetchone()
        malos += [(c, int(v)) for c, v in zip(cols[i:i + 40], r) if v]
    if malos:
        raise RuntimeError(f"valores que no entran en el esquema de 2019: {malos}")

    def cast(c: str) -> str:
        if tipos[c] == "DOUBLE":
            return f"CAST({q(c)} AS DOUBLE) AS {q(c)}"
        return (f"CASE WHEN regexp_full_match({q(c)}, '{INT_RE}') THEN CAST({q(c)} AS BIGINT) "
                f"ELSE CAST(CAST({q(c)} AS DOUBLE) AS BIGINT) END AS {q(c)}")

    tmp = destino.with_name(f"{destino.name}.tmp-{os.getpid()}")
    con.execute(f"COPY (SELECT {', '.join(cast(c) for c in cols)} FROM texto) TO '{tmp.as_posix()}' "
                f"(FORMAT parquet, COMPRESSION zstd, ROW_GROUP_SIZE 200000)")
    desc = [(n, t) for n, t, *_ in con.execute(f"DESCRIBE SELECT * FROM read_parquet('{tmp.as_posix()}')").fetchall()]
    por_mes = {str(m): int(n) for m, n in con.execute(
        f"SELECT foto_mes, count(*) FROM read_parquet('{tmp.as_posix()}') GROUP BY 1 ORDER BY 1").fetchall()}
    dup = con.execute(f"SELECT count(*) - count(DISTINCT (numero_de_cliente, foto_mes)) FROM "
                      f"read_parquet('{tmp.as_posix()}')").fetchone()[0]
    con.close()
    checks = {"esquema_y_orden": [list(x) for x in desc] == esquema["columnas"],
              "filas_por_mes": por_mes == esquema["filas_por_mes"], "claves_unicas": dup == 0}
    if not all(checks.values()):
        raise RuntimeError(f"2019 tipado no coincide con la referencia: {checks}; temporal en {tmp}")
    publicar(tmp, destino)
    return {"checks": checks, "filas": sum(por_mes.values())}


def paso_target(src: Path, destino: Path, huellas: dict, duck_tmp: Path) -> dict:
    con = conectar(duck_tmp)
    tmp = destino.with_name(f"{destino.name}.tmp-{os.getpid()}")
    con.execute(f"COPY ({SQL_TARGET}) TO '{tmp.as_posix()}' (FORMAT parquet, COMPRESSION zstd)", [src.as_posix()])
    t, s = f"read_parquet('{tmp.as_posix()}')", f"read_parquet('{src.as_posix()}')"
    n, nk = con.execute(f"SELECT count(*), count(DISTINCT (numero_de_cliente, foto_mes)) FROM {t}").fetchone()
    a = con.execute(f"SELECT count(*) FROM {s} x ANTI JOIN {t} y USING (numero_de_cliente, foto_mes)").fetchone()[0]
    b = con.execute(f"SELECT count(*) FROM {t} y ANTI JOIN {s} x USING (numero_de_cliente, foto_mes)").fetchone()[0]
    b2 = {str(m): int(k) for m, k in con.execute(
        f"SELECT foto_mes, count(*) FROM {t} WHERE clase_ternaria = 'BAJA+2' GROUP BY 1").fetchall()}
    con.close()
    ref = {m: v["baja2_03"] for m, v in huellas["etiquetas_grupo_vs_03"].items()}
    checks = {"claves_unicas": n == nk, "cobertura_igual_al_origen": a == 0 and b == 0,
              "baja2_por_mes_igual_a_la_referencia": {m: b2.get(m) for m in ref} == ref}
    if not all(checks.values()):
        raise RuntimeError(f"target no coincide con la referencia: {checks}; temporal en {tmp}")
    publicar(tmp, destino)
    return {"checks": checks, "filas": int(n)}


def paso_features(src: Path, destino: Path, esquema: dict, huellas: dict, duck_tmp: Path) -> dict:
    con = conectar(duck_tmp)
    con.execute(f"CREATE VIEW src AS SELECT * FROM read_parquet('{src.as_posix()}')")
    cols = [c for c, _ in esquema["columnas"] if c not in KEYS]
    pred = nombres(cols)
    sha_pred = hashlib.sha256(json.dumps(pred).encode()).hexdigest()
    if len(pred) != huellas["predictores"]["cantidad"] or sha_pred != huellas["predictores"]["sha256"]:
        raise RuntimeError("la lista de predictores no es la de las corridas (sha256 distinto)")
    crear_prev(con, "src")
    futuro = con.execute("SELECT count(*) FROM prev WHERE m1 >= foto_mes OR m2 >= m1").fetchone()[0]
    if futuro:
        raise RuntimeError("hay observaciones previas posteriores a la fila")
    tmp = destino.with_name(f"{destino.name}.tmp-{os.getpid()}")
    tmp.mkdir()
    bloquea = duckdb.__version__ == DUCKDB_REFERENCIA
    por_mes = {}
    for m in MESES:
        t = time.perf_counter()
        f = tmp / f"features_{m}.parquet"
        con.execute(f"COPY ({sql_mes('src', cols, m)}) TO '{f.as_posix()}' (FORMAT parquet, COMPRESSION zstd)")
        filas, h = huella_xor(con, f, KEYS + pred)
        por_mes[str(m)] = {"filas": filas, "huella_xor": h,
                           "huella_igual_a_04": h == esquema["huella_xor_features_por_mes"][str(m)],
                           "segundos": round(time.perf_counter() - t, 1)}
        log.info("features %d: %s", m, por_mes[str(m)])
    con.close()
    checks = {"filas_por_mes": {m: v["filas"] for m, v in por_mes.items()} == esquema["filas_por_mes"],
              "huella_xor_igual_a_04": all(v["huella_igual_a_04"] for v in por_mes.values())}
    if not checks["filas_por_mes"] or (bloquea and not checks["huella_xor_igual_a_04"]):
        raise RuntimeError(f"features no coinciden con la referencia: {checks}; temporal en {tmp}")
    if not checks["huella_xor_igual_a_04"]:
        log.warning("duckdb %s: la huella xor depende de la versión (referencia %s); valen las huellas sha256 de "
                    "07/08", duckdb.__version__, DUCKDB_REFERENCIA)
    manifiesto = {"claves": KEYS, "predictores": pred, "etiquetas": rutas.target().name,
                  "definicion": "lag_k = k-ésima observación previa del cliente; delta_k = x - lag_k; k = 1, 2; "
                                "152 originales + 608 derivadas; tipos del origen; sin imputar",
                  "origen": rutas.parquet_2019().name, "sha256_predictores": sha_pred,
                  "archivos": {m: {"filas": v["filas"], "huella_xor": v["huella_xor"]} for m, v in por_mes.items()},
                  "duckdb": duckdb.__version__}
    (tmp / "manifiesto.json").write_text(json.dumps(manifiesto, indent=1, ensure_ascii=False), encoding="utf-8")
    publicar(tmp, destino)
    return {"checks": checks, "por_mes": por_mes}


def verificar_existentes(esquema: dict, huellas: dict) -> dict:
    """Sin escribir nada: compara insumos ya generados con la referencia (huellas xor de features y predictores)."""
    man = json.loads((rutas.features_dir() / "manifiesto.json").read_text(encoding="utf-8"))
    sha_pred = hashlib.sha256(json.dumps(man["predictores"]).encode()).hexdigest()
    con = duckdb.connect()
    con.execute("SET threads = 4")
    por_mes = {}
    for m in MESES:
        filas, h = huella_xor(con, rutas.features_dir() / f"features_{m}.parquet", KEYS + man["predictores"])
        por_mes[str(m)] = {"filas": filas, "huella_igual_a_04": h == esquema["huella_xor_features_por_mes"][str(m)]}
    tipos = [[n, t] for n, t, *_ in con.execute(
        f"DESCRIBE SELECT * FROM read_parquet('{rutas.parquet_2019().as_posix()}')").fetchall()]
    con.close()
    return {"predictores_sha256_igual": sha_pred == huellas["predictores"]["sha256"],
            "esquema_2019_igual": tipos == esquema["columnas"], "features_por_mes": por_mes,
            "ok": sha_pred == huellas["predictores"]["sha256"] and tipos == esquema["columnas"]
                  and all(v["huella_igual_a_04"] for v in por_mes.values())}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--crudo", type=Path, help="crudo ya descargado (por defecto DATOS_DIR/competencia_02_crudo.csv.gz,"
                                                " que se baja si falta)")
    ap.add_argument("--solo-verificar", action="store_true", help="no genera: verifica los insumos existentes")
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s", datefmt="%H:%M:%S")
    esquema = json.loads(ESQUEMA.read_text(encoding="utf-8"))
    huellas = json.loads(HUELLAS.read_text(encoding="utf-8"))
    log.info("DATOS_DIR %s", rutas.datos_dir())
    if a.solo_verificar:
        r = verificar_existentes(esquema, huellas)
        print(json.dumps(r, indent=1, ensure_ascii=False))
        return 0 if r["ok"] else 1

    t0 = time.perf_counter()
    rutas.datos_dir().mkdir(parents=True, exist_ok=True)
    crudo = a.crudo.resolve() if a.crudo else cd.asegurar_crudo()
    duck_tmp = rutas.datos_dir() / f".duckdb_tmp-{os.getpid()}"
    duck_tmp.mkdir()
    rep = {"crudo": crudo.name, "duckdb": duckdb.__version__}
    try:
        pasos = [("2019", rutas.parquet_2019(), lambda d: paso_2019(crudo, d, esquema, duck_tmp)),
                 ("target", rutas.target(), lambda d: paso_target(rutas.parquet_2019(), d, huellas, duck_tmp)),
                 ("features", rutas.features_dir(),
                  lambda d: paso_features(rutas.parquet_2019(), d, esquema, huellas, duck_tmp))]
        for nombre, destino, fn in pasos:
            if destino.exists():
                log.info("%s: %s ya existe; no se sobrescribe (borrarlo a mano para regenerarlo)", nombre, destino)
                rep[nombre] = "existente"
                continue
            t = time.perf_counter()
            rep[nombre] = fn(destino)
            rep[nombre]["segundos"] = round(time.perf_counter() - t, 1)
            log.info("%s: %s", nombre, rep[nombre]["checks"])
    finally:
        shutil.rmtree(duck_tmp, ignore_errors=True)
    rep["total_s"] = round(time.perf_counter() - t0, 1)
    print(json.dumps(rep, indent=1, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
