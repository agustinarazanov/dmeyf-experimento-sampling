"""Sin datos: la comparación de paneles de D7 y el SQL de Luis sobre un crudo de juguete; la corrida nueva de 07 (D5)."""
import numpy as np
import pandas as pd
import pytest

from experimentos.sampling_1.exploratorios import replicacion_martin as rm
from experimentos.sampling_1.exploratorios.validacion_50_semillas import panel_luis as pl


def _panel(ruta, df):
    df.to_parquet(ruta, index=False)
    return ruta


def _base():
    # un id de más de 2**24, como los reales: no entra exacto en float32
    return pd.DataFrame({"numero_de_cliente": [16777264, 2, 16777264, 2], "foto_mes": [201908, 201908, 201910, 201910],
                         "clase_ternaria": ["CONTINUA", "BAJA+1", None, "BAJA+2"],
                         "a": np.array([1.0, np.nan, 3.0, 4.0], dtype=np.float32),
                         "b": np.array([0.5, 0.25, 0.0, -1.0], dtype=np.float32)})


def test_paneles_iguales(tmp_path):
    r = pl.comparar(_panel(tmp_path / "n.parquet", _base()), _panel(tmp_path / "l.parquet", _base()))
    assert r["iguales"] and r["huellas"]["comparadas"] == 5 and not r["huellas"]["distintas"]


def test_orden_de_columnas_cuenta(tmp_path):
    d = _base()
    r = pl.comparar(_panel(tmp_path / "n.parquet", d), _panel(tmp_path / "l.parquet", d[["numero_de_cliente", "foto_mes", "clase_ternaria", "b", "a"]]))
    assert r["columnas"]["mismos_nombres"] and not r["columnas"]["mismo_orden"]
    assert r["columnas"]["primera_posicion_distinta"] == 3
    assert not r["huellas"]["distintas"] and not r["iguales"]


def test_valor_distinto_y_tipo_distinto(tmp_path):
    d, l = _base(), _base()
    l.loc[3, "b"] = -2.0
    l["a"] = l["a"].astype("float64")   # misma huella en float32
    r = pl.comparar(_panel(tmp_path / "n.parquet", d), _panel(tmp_path / "l.parquet", l))
    assert r["huellas"]["distintas"] == {"b": 1} and not r["iguales"]


def test_filas_distintas_no_compara_valores(tmp_path):
    r = pl.comparar(_panel(tmp_path / "n.parquet", _base()), _panel(tmp_path / "l.parquet", _base().iloc[:3]))
    assert not r["filas_por_mes"]["iguales"] and not r["filas_alineadas"] and r["huellas"]["comparadas"] == 0


def test_sql_de_luis_sobre_crudo_de_juguete(tmp_path):
    meses = [201901, 201902, 201903, 201904, 201905, 201906, 201907, 201908, 201909, 201910, 201911, 201912]
    filas = [{"numero_de_cliente": 1, "foto_mes": m, "x": float(i)} for i, m in enumerate(meses)]
    filas += [{"numero_de_cliente": 2, "foto_mes": m, "x": 10.0} for m in meses[:9]]   # se va después de 201909
    crudo = tmp_path / "crudo.csv"
    pd.DataFrame(filas).to_csv(crudo, index=False)
    p = pd.read_parquet(pl.construir_panel_luis(crudo, tmp_path / "luis.parquet", hilos=1))
    assert list(p.columns[:5]) == ["numero_de_cliente", "foto_mes", "clase_ternaria", "y", "es_baja2"]
    assert list(p.columns[5:]) == ["x", "x__lag1", "x__lag2", "x__delta1", "x__delta2"]   # intercaladas por columna
    assert sorted(p["foto_mes"].unique()) == pl.MESES_PANEL
    c2 = p[p["numero_de_cliente"] == 2].set_index("foto_mes")
    assert c2.loc[201908, "clase_ternaria"] == "BAJA+2"      # su último mes es 201909
    assert c2.loc[201908, "es_baja2"] == 1 and c2.loc[201906, "clase_ternaria"] == "CONTINUA"
    c1 = p[p["numero_de_cliente"] == 1].set_index("foto_mes")
    assert c1.loc[201908, "x__lag1"] == 6.0 and c1.loc[201908, "x__delta2"] == 2.0


def test_corrida_07_nueva(tmp_path):
    vieja = tmp_path / "07_sensibilidad_muestra_h3" / "20261103T191818_13788"
    vieja.mkdir(parents=True)
    (vieja / "diseno.json").write_text("{}")
    antes = {vieja}
    with pytest.raises(RuntimeError):
        rm.corrida_07_nueva(tmp_path, antes)
    nueva = tmp_path / "07_sensibilidad_muestra_h3" / "20261110T010000_42"
    nueva.mkdir()
    (nueva / "diseno.json").write_text("{}")
    assert rm.corrida_07_nueva(tmp_path, antes) == nueva
