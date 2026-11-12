"""Datos: descarga del crudo, panel 2019 con lags y deltas de orden 2 (DuckDB) y lectura por mes.

El panel se construye una sola vez por máquina y se guarda en Parquet dentro de `DATOS_DIR`, fuera del repo. El SQL de
la etiqueta sigue a `competencia-2/src/fe_panel.py` (`_SQL_BASE`, `sql_lag`, `sql_delta`): BAJA+1 si el cliente no está
en t+1; BAJA+2 si está en t+1 y no en t+2; CONTINUA si está en los dos. Los lags son por fila del cliente.

    python -m comun.datos [--filas 20000]
"""

from __future__ import annotations

import argparse
import logging
import time
import urllib.request
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from comun import baseline as bl

log = logging.getLogger("datos")

ID = "numero_de_cliente"
MES = "foto_mes"
CLASE = "clase_ternaria"
Y = "y"            # BAJA+1 ∪ BAJA+2
BAJA2 = "es_baja2"  # BAJA+2: contra esto se calcula la ganancia
NO_PREDICTORAS = [ID, MES, CLASE, Y, BAJA2]

#: Meses leídos por `cargar_meses` en este proceso; la etapa `optimizar` no debe incluir 201910.
MESES_LEIDOS: list[int] = []

_MACROS = """
create or replace macro mes_indice(m) as ((m // 100) * 12 + (m % 100) - 1);
create or replace macro indice_mes(i) as ((i // 12) * 100 + (i % 12) + 1);
create or replace macro mes_mas(m, n) as indice_mes(mes_indice(m) + n);
"""


def ruta_crudo() -> Path:
    return bl.DATOS_DIR / "competencia_02_crudo.csv.gz"


def ruta_panel(filas: int | None = None) -> Path:
    return bl.DATOS_DIR / (f"panel_2019_smoke{filas}.parquet" if filas else "panel_2019.parquet")


def asegurar_crudo() -> Path:
    """Baja el crudo del GCS del curso a `DATOS_DIR` si no está."""
    destino = ruta_crudo()
    if destino.exists():
        return destino
    bl.DATOS_DIR.mkdir(parents=True, exist_ok=True)
    log.info("bajando %s", bl.URL_CRUDO)
    parcial = destino.with_suffix(".gz.part")
    urllib.request.urlretrieve(bl.URL_CRUDO, parcial)
    parcial.rename(destino)
    return destino


def _lista(meses) -> str:
    return ", ".join(str(m) for m in meses)


def construir_panel(filas: int | None = None, destino: Path | None = None) -> Path:
    """Crudo -> panel 2019 con target, lag1, lag2, delta1 y delta2 de cada columna numérica, en Parquet.

    `filas` es solo para smoke tests: se queda con clientes (por hash del id) hasta rondar esa cantidad de filas.
    """
    crudo = asegurar_crudo()
    destino = destino or ruta_panel(filas)
    destino.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute(_MACROS)
    con.execute(
        f"create table crudo as select * from read_csv('{crudo}', sample_size=-1) "
        f"where {MES} between {bl.CRUDO_DESDE} and {bl.CRUDO_HASTA}"
    )
    if filas:
        total = con.execute(f"select count(*) from crudo where {MES} in ({_lista(bl.MESES_PANEL)})").fetchone()[0]
        corte = min(1.0, filas / total)
        con.execute(f"delete from crudo where hash({ID}) % 1000000 >= {int(corte * 1_000_000)}")

    tipos = con.execute("select column_name, column_type from (describe crudo)").fetchall()
    numericas = [
        c for c, t in tipos
        if c not in (ID, MES) and t.split("(")[0] in ("BIGINT", "INTEGER", "DOUBLE", "FLOAT", "DECIMAL", "SMALLINT", "TINYINT", "HUGEINT")
    ]
    descartadas = [c for c, _ in tipos if c not in numericas and c not in (ID, MES)]
    if descartadas:
        log.warning("columnas no numéricas fuera del panel: %s", descartadas)

    con.execute(f"""
        create table etiqueta as
        select k.{ID}, k.{MES},
               case when p1.{ID} is null then 'BAJA+1'
                    when p2.{ID} is null then 'BAJA+2'
                    else 'CONTINUA' end as {CLASE}
        from crudo k
        left join crudo p1 on p1.{ID} = k.{ID} and p1.{MES} = mes_mas(k.{MES}, 1)
        left join crudo p2 on p2.{ID} = k.{ID} and p2.{MES} = mes_mas(k.{MES}, 2)
        where k.{MES} in ({_lista(bl.MESES_TRAIN_FINAL + [bl.MES_VALIDACION, bl.MES_TEST])})
    """)
    cols = [f"c.{x}::FLOAT as {x}" for x in numericas]
    for n in range(1, bl.LAGS + 1):
        cols += [f"lag(c.{x}, {n}) over h::FLOAT as {x}__lag{n}" for x in numericas]
    for n in range(1, bl.LAGS + 1):
        cols += [f"(c.{x} - lag(c.{x}, {n}) over h)::FLOAT as {x}__delta{n}" for x in numericas]
    # la ventana corre sobre 201901..201910 completo y recién después se filtran los meses, para que el lag de 201908
    # sea 201907 y no 201906
    sql = f"""
        select * from (
            select c.{ID}, c.{MES}, e.{CLASE},
                   (e.{CLASE} in ('BAJA+1', 'BAJA+2'))::TINYINT as {Y},
                   (e.{CLASE} = 'BAJA+2')::TINYINT as {BAJA2},
                   {', '.join(cols)}
            from crudo c
            left join etiqueta e using ({ID}, {MES})
            where c.{MES} <= {bl.MES_TEST}
            window h as (partition by c.{ID} order by c.{MES})
        ) where {MES} in ({_lista(bl.MESES_PANEL)})
        order by {MES}, {ID}
    """
    con.execute(f"copy ({sql}) to '{destino}' (format parquet, compression zstd)")
    con.close()
    return destino


def _tiene_meses(ruta: Path) -> bool:
    """Un panel sin alguno de `MESES_PANEL` (p. ej. el viejo, sin 201907) se reconstruye (D2)."""
    con = duckdb.connect()
    try:
        meses = {r[0] for r in con.execute(f"select distinct {MES} from read_parquet('{ruta}')").fetchall()}
    finally:
        con.close()
    return set(bl.MESES_PANEL) <= meses


def asegurar_panel(filas: int | None = None) -> tuple[Path, float]:
    """Devuelve (ruta del panel, segundos que costó prepararlo); 0,0 si ya existía."""
    ruta = ruta_panel(filas)
    if ruta.exists() and _tiene_meses(ruta):
        return ruta, 0.0
    t0 = time.perf_counter()
    construir_panel(filas)
    return ruta, time.perf_counter() - t0


def cargar_meses(meses: list[int], filas: int | None = None) -> pd.DataFrame:
    """Filas de los meses pedidos, features en float32. Anota los meses leídos en el log y en `MESES_LEIDOS`."""
    ruta = ruta_panel(filas)
    log.info("MESES_LEIDOS %s", ",".join(str(m) for m in meses))
    MESES_LEIDOS.extend(meses)
    con = duckdb.connect()
    df = con.execute(f"select * from read_parquet('{ruta}') where {MES} in ({_lista(meses)})").df()
    con.close()
    return df


def columnas_predictoras(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c not in NO_PREDICTORAS]


def matriz(df: pd.DataFrame, columnas: list[str]) -> np.ndarray:
    return df[columnas].to_numpy(dtype=np.float32)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--filas", type=int, default=None, help="smoke test: panel de ~N filas")
    a = p.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    ruta, seg = asegurar_panel(a.filas)
    print(f"{ruta} ({seg:.1f} s)")


if __name__ == "__main__":
    main()
