"""Rutas del paquete. Los datos viven en DATOS_DIR (de `comun.baseline`, variable de entorno), nunca en el repo.

    DATOS_DIR/competencia_02_crudo.csv.gz                 crudo autorizado (comun.datos lo baja si falta)
    DATOS_DIR/competencia_02_2019.parquet                 insumos.py: 2019 tipado (BIGINT/DOUBLE)
    DATOS_DIR/competencia_02_2019_target.parquet          insumos.py: clase_ternaria, clase_binaria
    DATOS_DIR/competencia_02_2019_features/               insumos.py: features_AAAAMM.parquet + manifiesto.json
    DATOS_DIR/h3_sensibilidad_muestra/ejecuciones/        salidas de sensibilidad_07 y ganancia_08 (--salida)

Los nombres no chocan con los del panel del grupo (`panel_2019*.parquet`).
"""
from __future__ import annotations

from pathlib import Path

from comun import baseline as bl
from comun import datos as cd

PAQUETE = Path(__file__).resolve().parent
REFERENCIA = PAQUETE / "referencia"
RESULTADOS = PAQUETE / "resultados"


def datos_dir() -> Path:
    return bl.DATOS_DIR


def crudo() -> Path:
    return cd.ruta_crudo()


def parquet_2019() -> Path:
    return datos_dir() / "competencia_02_2019.parquet"


def target() -> Path:
    return datos_dir() / "competencia_02_2019_target.parquet"


def features_dir() -> Path:
    return datos_dir() / "competencia_02_2019_features"


def salida_por_defecto() -> Path:
    return datos_dir() / "h3_sensibilidad_muestra" / "ejecuciones"
