"""Verifica el panel de smoke (`python -m comun.datos --filas 20000` primero)."""
import duckdb
import pytest

from comun import baseline as bl
from comun import datos as d

RUTA = d.ruta_panel(20000)
pytestmark = pytest.mark.skipif(not RUTA.exists(), reason="falta el panel de smoke")


def test_lag_y_delta_de_cada_columna_numerica_y_sin_target_en_la_historia():
    con = duckdb.connect()
    cols = [r[0] for r in con.execute(f"describe select * from read_parquet('{RUTA}')").fetchall()]
    base = [c for c in cols if "__" not in c and c not in d.NO_PREDICTORAS and c not in (d.ID, d.MES)]
    assert len(base) > 100
    for c in base:
        for sufijo in ("lag1", "lag2", "delta1", "delta2"):
            assert f"{c}__{sufijo}" in cols
    historia = con.execute(
        f"select count(*), count({d.Y}), count({d.CLASE}) from read_parquet('{RUTA}') where {d.MES} in (201901, 201902)"
    ).fetchone()
    assert historia[0] > 0 and historia[1] == 0 and historia[2] == 0
    meses = sorted(r[0] for r in con.execute(f"select distinct {d.MES} from read_parquet('{RUTA}')").fetchall())
    assert meses == sorted(bl.MESES_PANEL)
    # el lag1 de 201908 es de 201907, que no está en el panel pero sí en la ventana
    n_lag = con.execute(f"select count(*) from read_parquet('{RUTA}') where {d.MES} = 201908 and cliente_edad__lag1 is not null").fetchone()[0]
    assert n_lag > 0
    pos = con.execute(f"select avg({d.Y}), avg({d.BAJA2}) from read_parquet('{RUTA}') where {d.MES} = 201903").fetchone()
    assert 0 < pos[1] < pos[0] < 0.1
